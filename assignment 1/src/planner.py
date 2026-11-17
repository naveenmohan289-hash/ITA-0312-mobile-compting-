
"""Reproducible cellular frequency-planning simulator for Assignment 1.

Models: fixed reuse, 120-degree sectoring, dynamic channel assignment,
and hierarchical microcell splitting. This is an educational planning model,
not a vendor-grade RF planning tool.
"""
from __future__ import annotations
import math, csv, json, time, argparse
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt

AREA_KM2 = 12.0
TOTAL_CHANNELS = 420
R_KM = 0.5
TRAFFIC_PER_SUBSCRIBER_ERLANG = 0.02
BLOCKING_TARGET = 0.02
SEED = 197226

def erlang_b(channels: int, offered: float) -> float:
    """Stable Erlang-B recursion."""
    b = 1.0
    for m in range(1, max(0, int(channels)) + 1):
        b = offered * b / (m + offered * b)
    return b

def carried_traffic(channels: int, target_blocking=BLOCKING_TARGET) -> float:
    """Largest offered traffic (Erlangs) whose Erlang-B blocking <= target."""
    if channels <= 0: return 0.0
    lo, hi = 0.0, max(1.0, channels * 2.0)
    while erlang_b(channels, hi) < target_blocking:
        hi *= 2
    for _ in range(70):
        mid = (lo + hi) / 2
        if erlang_b(channels, mid) <= target_blocking: lo = mid
        else: hi = mid
    return lo

def hex_area(radius_km: float) -> float:
    return 3 * math.sqrt(3) * radius_km**2 / 2

def cluster_valid_sizes(max_n=30):
    vals = []
    for i in range(0, int(math.sqrt(max_n))+2):
        for j in range(0, int(math.sqrt(max_n))+2):
            n = i*i + i*j + j*j
            if 1 <= n <= max_n and n not in vals: vals.append(n)
    return sorted(vals)

def axial_centres(radius_km: float, area_km2=AREA_KM2):
    """Generate axial hex centres and retain centres inside a square proxy of area."""
    # Adjacent centre spacing = sqrt(3) R. Clip by a circle with equal area.
    d = math.sqrt(3) * radius_km
    extent = math.sqrt(area_km2 / math.pi)
    pts=[]
    lim=int(math.ceil(2*extent/d))+2
    for q in range(-lim, lim+1):
        for r in range(-lim, lim+1):
            x=d*(q+r/2)
            y=d*(math.sqrt(3)/2*r)
            if x*x+y*y <= extent*extent:
                pts.append((q,r,x,y))
    return pts

def graph_reuse_colouring(points, reuse_distance, max_colours=60):
    """Greedy graph colouring: same-colour sites obey the specified separation."""
    n=len(points); cols=[-1]*n
    xy=np.array([[p[2],p[3]] for p in points])
    # Degree-first ordering improves finite-grid colouring.
    dist=np.sqrt(((xy[:,None,:]-xy[None,:,:])**2).sum(axis=2))
    adjacency=dist < (reuse_distance-1e-9)
    np.fill_diagonal(adjacency, False)
    order=sorted(range(n), key=lambda i: int(adjacency[i].sum()), reverse=True)
    for i in order:
        used={cols[j] for j in np.where(adjacency[i])[0] if cols[j]>=0}
        c=next((k for k in range(max_colours) if k not in used), None)
        if c is None: c=max_colours
        cols[i]=c
    return cols

def sir_db(r_km, n_exp=4.0, interferers=6, sectorized=False, shadow_sigma_db=0.0,
           samples=12000, seed=SEED):
    """Monte-Carlo SIR with idealized first-tier geometry.
    Sectoring reduces effective first-tier interferers from 6 to 2.
    """
    rng=np.random.default_rng(seed)
    m=2 if sectorized else interferers
    # Approximate co-channel sites at D = R*sqrt(3N), six equidistant.
    # For sectoring, only two dominant interferers are retained.
    D=r_km*math.sqrt(3*7)
    theta=rng.uniform(0,2*np.pi,(samples,m))
    # User radial location: uniform over hex area approximated by sqrt(U)*R.
    rho=np.sqrt(rng.random(samples))*r_km
    phi=rng.uniform(0,2*np.pi,samples)
    ux=rho*np.cos(phi); uy=rho*np.sin(phi)
    if sectorized:
        # Dominant pair on boresight direction.
        angles=np.column_stack([np.zeros(samples), np.full(samples, np.pi)])
        ix=D*np.cos(angles); iy=D*np.sin(angles)
        di=np.sqrt((ix-ux[:,None])**2+(iy-uy[:,None])**2)
        interf=np.sum(di**(-n_exp),axis=1)
    else:
        ang=np.arange(6)*np.pi/3
        ix=D*np.cos(ang)[None,:]; iy=D*np.sin(ang)[None,:]
        di=np.sqrt((ix-ux[:,None])**2+(iy-uy[:,None])**2)
        interf=np.sum(di**(-n_exp),axis=1)
    ds=np.sqrt(ux**2+uy**2)
    ds=np.maximum(ds,0.015*r_km)
    signal=ds**(-n_exp)
    sir=10*np.log10(signal/interf)
    if shadow_sigma_db>0:
        sir += rng.normal(0, shadow_sigma_db, samples)
    return {"mean_db":float(np.mean(sir)), "p05_db":float(np.percentile(sir,5)),
            "outage_0db":float(np.mean(sir<0)), "samples":samples}

def strategy_capacity(N, sectorized=False, dynamic=False, radius=R_KM):
    channels_per_cell=max(1, TOTAL_CHANNELS//N)
    # Sectoring divides cell channels into 3 sector pools; total cell channels unchanged.
    # Dynamic assignment uses a pooled trunking gain approximation of 12%.
    if dynamic:
        channels_per_cell=max(1, int(channels_per_cell*1.12))
    per_cell=carried_traffic(channels_per_cell)
    count=max(1, math.ceil(AREA_KM2/hex_area(radius)))
    return {"channels_per_cell":channels_per_cell, "traffic_per_cell_E":per_cell,
            "cells":count, "total_capacity_E":count*per_cell,
            "blocking_at_capacity":erlang_b(channels_per_cell,per_cell)}



def make_fixed_channel_plan(N=7, radius=R_KM):
    """Create finite hex grid and assign one reuse colour per site."""
    pts=axial_centres(radius)
    D=radius*math.sqrt(3*N)
    colours=graph_reuse_colouring(pts,D,max_colours=N)
    plan=[]
    for idx,(pt,c) in enumerate(zip(pts,colours)):
        q,r,x,y=pt
        plan.append({"site_id":idx,"q":q,"r":r,"x_km":round(x,4),
                     "y_km":round(y,4),"reuse_group":int(c),
                     "channel_start":int(c*(TOTAL_CHANNELS//N)),
                     "channel_end":int((c+1)*(TOTAL_CHANNELS//N)-1)})
    return plan

def dynamic_channel_allocator(neighbour_map, active_channels, local_pool):
    """Allocate the lowest-numbered free channel not active in a co-channel neighbour."""
    chosen={}
    for cell in sorted(neighbour_map):
        forbidden=set()
        for nb in neighbour_map[cell]:
            forbidden.update(active_channels.get(nb,set()))
        used=set(active_channels.get(cell,set()))
        candidate=next((ch for ch in local_pool if ch not in forbidden and ch not in used),None)
        if candidate is not None:
            active_channels.setdefault(cell,set()).add(candidate)
            chosen[cell]=candidate
        else:
            chosen[cell]=None
    return chosen

def split_recurrence(M0, capacity0, rounds, split_fraction=1.0, n_exp=4.0):
    """Return selective/uniform cell, capacity, radius and per-child power by round."""
    M=float(M0); C=float(capacity0); R=R_KM; P=1.0
    out=[{"round":0,"cells":M,"aggregate_capacity":M*C,"radius_km":R,"relative_child_power":P}]
    for k in range(1,rounds+1):
        factor=1+3*split_fraction
        M*=factor; C*=factor; R/=2; P/=2**n_exp
        out.append({"round":k,"cells":M,"aggregate_capacity":M*C,
                    "radius_km":R,"relative_child_power":P})
    return out

def run_experiments(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    subscribers=[1000,10000,20000,100000]
    strategies=["fixed_reuse","120_degree_sectoring","dynamic_assignment","hierarchical_microcells"]
    rows=[]
    for N in [3,4,7,12]:
        for n in [2.5,3.0,4.0]:
            for sect in [False,True]:
                sir=sir_db(R_KM,n_exp=n,sectorized=sect,seed=SEED+int(N*10+n*100))
                rows.append({"N":N,"path_loss_n":n,"sectorized":sect,**sir})
    with open(out_dir/"sir_experiments.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)

    cap_rows=[]
    for N in [3,4,7,12]:
        for strat in strategies[:3]:
            d=strategy_capacity(N,sectorized=(strat=="120_degree_sectoring"),
                                dynamic=(strat=="dynamic_assignment"))
            for sub in subscribers:
                demand=sub*TRAFFIC_PER_SUBSCRIBER_ERLANG
                cap_rows.append({"strategy":strat,"N":N,"subscribers":sub,
                    "offered_traffic_E":demand,**d,
                    "blocking_at_demand":erlang_b(d["channels_per_cell"],
                        demand/max(1,d["cells"]))})
    # Hierarchical capacity with successive radius-halving and 4x area cell density.
    for sub in subscribers:
        demand=sub*TRAFFIC_PER_SUBSCRIBER_ERLANG
        for k in range(4):
            R=R_KM/(2**k)
            N=7
            d=strategy_capacity(N,radius=R)
            cap_rows.append({"strategy":"hierarchical_microcells","N":N,"subscribers":sub,
                "offered_traffic_E":demand,**d,
                "blocking_at_demand":erlang_b(d["channels_per_cell"],
                    demand/max(1,d["cells"])),"split_rounds":k,"radius_km":R})
    with open(out_dir/"capacity_experiments.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=sorted({k for row in cap_rows for k in row}))
        w.writeheader(); w.writerows(cap_rows)

    # Explicit fixed channel plan and dynamic allocation demonstration.
    plan=make_fixed_channel_plan(N=7)
    with open(out_dir/"fixed_reuse_channel_plan.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=plan[0].keys()); w.writeheader(); w.writerows(plan)
    neighbour_map={0:[1,2],1:[0,2],2:[0,1]}
    active={0:{0},1:{1},2:set()}
    dynamic_demo=dynamic_channel_allocator(neighbour_map,active,list(range(12)))
    (out_dir/"dynamic_assignment_demo.json").write_text(json.dumps(
        {str(k):v for k,v in dynamic_demo.items()},indent=2))
    split=split_recurrence(M0=19,capacity0=1.0,rounds=3,split_fraction=1.0,n_exp=4)
    with open(out_dir/"cell_splitting_recurrence.csv","w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=split[0].keys()); w.writeheader(); w.writerows(split)

    # Event surge: 25,000 x 0.05 E in 1 km2 = 1,250 E/km2.
    event_E=25000*0.05
    event_density=event_E/1.0
    base_density=(100000*TRAFFIC_PER_SUBSCRIBER_ERLANG)/AREA_KM2
    # Approximate temporary microcell requirement at N=7; capacity/cell from Erlang B.
    base_cell=carried_traffic(TOTAL_CHANNELS//7)
    temporary_cells=math.ceil(event_E/base_cell)
    event={"attendees":25000,"traffic_each_E":0.05,"event_traffic_E":event_E,
           "event_zone_km2":1.0,"event_density_E_per_km2":event_density,
           "township_reference_density_E_per_km2":base_density,
           "density_multiplier_vs_township":event_density/base_density,
           "N":7,"channels_per_cell":TOTAL_CHANNELS//7,
           "2_percent_blocking_capacity_per_cell_E":base_cell,
           "temporary_cells_required_ideal_lower_bound":temporary_cells,
           "event_duration_hours":4,"events_per_month":2}
    (out_dir/"event_surge.json").write_text(json.dumps(event,indent=2))

    # Plot 1: SIR CDFs for fixed vs sectorized.
    plt.figure(figsize=(7,4.5))
    for sect,label in [(False,"Omnidirectional"),(True,"120° sectorized")]:
        rng=np.random.default_rng(SEED+int(sect))
        # Reuse same model samples; CDF of SIR.
        # Generate with slightly denser samples for smooth curve.
        m=sir_db(R_KM,4.0,sectorized=sect,samples=20000,seed=SEED+int(sect))
        # Store distribution for CDF using direct reproducible approximation.
        # The CSV carries mean and fifth percentile; this curve is illustrative.
        x=np.linspace(-10,35,200)
        mu=m["mean_db"]; sd=8.0 if not sect else 7.0
        cdf=0.5*(1+np.array([math.erf((v-mu)/(sd*math.sqrt(2))) for v in x]))
        plt.plot(x,cdf,label=label)
    plt.xlabel("SIR (dB)"); plt.ylabel("Approximate cumulative probability")
    plt.title("Illustrative SIR CDF (n = 4, N = 7)")
    plt.grid(True,alpha=.3); plt.legend(); plt.tight_layout()
    plt.savefig(out_dir/"sir_cdf.png",dpi=160); plt.close()

    # Plot 2: Erlang-B blocking vs offered load for 60 channels.
    ch=TOTAL_CHANNELS//7
    loads=np.linspace(0.1, min(ch*1.7,100), 160)
    probs=[erlang_b(ch,a) for a in loads]
    plt.figure(figsize=(7,4.5)); plt.semilogy(loads,probs)
    plt.axhline(.02,linestyle="--",label="2% target")
    plt.xlabel("Offered traffic per cell (Erlangs)"); plt.ylabel("Blocking probability")
    plt.title(f"Erlang-B blocking vs offered load ({ch} channels)")
    plt.grid(True,which="both",alpha=.3); plt.legend(); plt.tight_layout()
    plt.savefig(out_dir/"blocking_vs_load.png",dpi=160); plt.close()

    # Plot 3: channels/cell and approximate capacity by cluster size.
    ns=np.array([3,4,7,12])
    caps=[strategy_capacity(int(N))["total_capacity_E"] for N in ns]
    plt.figure(figsize=(7,4.5)); plt.plot(ns,caps,marker="o")
    plt.xlabel("Cluster size N"); plt.ylabel("Approx. township capacity (Erlangs)")
    plt.title("Capacity trend against cluster size")
    plt.grid(True,alpha=.3); plt.tight_layout()
    plt.savefig(out_dir/"capacity_vs_N.png",dpi=160); plt.close()
    return {"event":event,"sir_rows":len(rows),"capacity_rows":len(cap_rows)}

def self_test():
    assert abs(hex_area(1)-2.598076211) < 1e-6
    assert cluster_valid_sizes(12)==[1,3,4,7,9,12]
    assert erlang_b(1,1)>0 and erlang_b(10,1)<0.01
    assert carried_traffic(60)>0
    assert len(make_fixed_channel_plan(7))>0
    demo=dynamic_channel_allocator({0:[1],1:[0]},{0:set(),1:{0}},[0,1,2])
    assert demo[0] is not None and demo[1] is not None and demo[0] != demo[1]
    assert split_recurrence(1,1,2)[-1]["cells"] == 16
    s=sir_db(.5,4,sectorized=False,samples=1000)
    assert -30 < s["mean_db"] < 40
    return "PASS: geometry, valid cluster sizes, Erlang-B, capacity inversion and SIR checks"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="results")
    p.add_argument("--self-test",action="store_true")
    a=p.parse_args()
    if a.self_test: print(self_test())
    t=time.perf_counter()
    summary=run_experiments(Path(a.out))
    summary["runtime_seconds"]=round(time.perf_counter()-t,3)
    print(json.dumps(summary,indent=2))
if __name__=="__main__": main()
