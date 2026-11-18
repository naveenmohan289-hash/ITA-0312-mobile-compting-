"""Assignment 5 simulation engine: Python 3.9+, standard library only.
Battery/energy/time figures are deterministic model estimates, not device measurements.
"""
import csv, json, argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data"; OUT=ROOT/"outputs"
def load(name):
    with (DATA/name).open(encoding="utf-8") as f: return json.load(f)
def save(name,rows):
    OUT.mkdir(parents=True,exist_ok=True)
    if rows:
        with (OUT/name).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def yes(v): return str(v).lower() in ("true","1","yes")
def schedule(items,strategy="fifo",scenario=None):
    c=scenario or {"battery":85,"network":"good","doze":False,"permission":True}
    q=[dict(x) for x in items]
    if strategy=="priority": q.sort(key=lambda x:(-int(x["priority"]),int(x["arrival"])))
    m={"strategy":strategy,"enqueued":len(q),"deferred":0,"cancelled":0,"successful":0,"attempts":0,"peak_workers":1 if q else 0,"residual":0}
    trace=[]
    for x in q:
        m["attempts"]+=1
        if not yes(c.get("permission",True)): reason="permission_revoked_cancel"; m["cancelled"]+=1
        elif yes(x.get("sensitive",False)) and not yes(x.get("encrypted",False)): reason="unencrypted_sensitive_reject"; m["cancelled"]+=1
        elif yes(c.get("doze",False)) and not yes(x.get("critical",False)): reason="doze_defer"; m["deferred"]+=1
        elif int(c.get("battery",100))<int(x.get("min_battery",20)): reason="low_battery_defer"; m["deferred"]+=1
        elif c.get("network") not in ("good","metered") or (c.get("network")=="metered" and not yes(x.get("metered_ok",False))): reason="network_defer"; m["deferred"]+=1
        else: reason="executed"; m["successful"]+=1
        trace.append({"id":x["id"],"priority":x["priority"],"decision":reason,"battery":c.get("battery"),"network":c.get("network"),"doze":c.get("doze")})
    m["residual"]=m["enqueued"]-m["successful"]-m["cancelled"]
    return m,trace
def b1():
    items=load("b1_sensor_jobs.json"); scenarios={"good_connectivity_battery":{"battery":88,"network":"good","doze":False,"permission":True},"doze_low_battery":{"battery":12,"network":"good","doze":True,"permission":True},"permission_revoked_midrun":{"battery":80,"network":"good","doze":False,"permission":False}}
    rows=[]; traces=[]
    for name,c in scenarios.items():
        for s in ("fifo","priority"):
            m,t=schedule(items,s,c); m["scenario"]=name; rows.append(m)
            for x in t: x.update(scenario=name,strategy=s); traces.append(x)
    save("B1_Scheduler_Comparison.csv",rows); save("B1_Decision_Trace.csv",traces); return rows
def b2():
    rows=[]; traces=[]
    for name,items in load("b2_workloads.json").items():
        m,t=schedule(items,"priority",{"battery":28,"network":"metered","doze":False,"permission":True}); m["workload"]=name; rows.append(m)
        for x in t: x["workload"]=name; traces.append(x)
    save("B2_Workload_Comparison.csv",rows); save("B2_Decision_Trace.csv",traces); return rows
def cost(n,q,c):
    drop=max(0,19+0.55*n-4.2*q-0.9*c); energy=2+0.8*q+0.22*c+max(0,c-4)*0.35; memory=max(0,c*18+n*2-150)
    return round(drop*2+energy+memory*0.08,3),round(drop,2),round(energy,2)
def exact(n,qs,cs):
    best=None; count=0
    for q in qs:
        for c in cs:
            z,d,e=cost(n,q,c); count+=1; r={"quality":q,"cache":c,"cost":z,"frame_drop_ms":d,"energy_units":e}
            if best is None or z<best["cost"]: best=r
    return best,count
def adaptive(n,battery):
    q=3;c=3;changes=0;evictions=0;hist=[]
    for _ in range(12):
        z,d,e=cost(n,q,c); frame=16+d; hist.append((q,c,frame,battery))
        if frame<=16 and battery>=25: break
        if frame>16 and q>1: q-=1; changes+=1
        elif battery<25 and c>1: c-=1; evictions+=1
        elif frame>16 and c>1: c-=1; evictions+=1
        else: break
    z,d,e=cost(n,q,c)
    return {"quality":q,"cache":c,"cost":z,"frame_drop_ms":d,"energy_units":e,"quality_changes":changes,"cache_evictions":evictions,"iterations":len(hist)}
def b3():
    rows=[]
    for x in load("b3_feed_cases.json"):
        ex,ops=exact(x["items"],x["quality_levels"],x["cache_sizes"]); ap=adaptive(x["items"],x["battery"])
        rows.append({"case":x["name"],"items":x["items"],"exact_cost":ex["cost"],"approx_cost":ap["cost"],"match":ex["cost"]==ap["cost"],"exact_configurations":ops,"approx_iterations":ap["iterations"],"approx_quality_changes":ap["quality_changes"],"approx_cache_evictions":ap["cache_evictions"],"exact_quality":ex["quality"],"exact_cache":ex["cache"],"approx_quality":ap["quality"],"approx_cache":ap["cache"]})
    scale=[]
    for n,qs,cs in [(8,[1,2,3,4],[1,2,3,4]),(40,[1,2,3,4,5,6],[1,2,3,4,5,6]),(120,list(range(1,9)),list(range(1,9)))]:
        ex,ops=exact(n,qs,cs); ap=adaptive(n,35)
        scale.append({"items":n,"quality_levels":len(qs),"cache_sizes":len(cs),"exact_configurations_evaluated":ops,"adaptive_iterations":ap["iterations"],"adaptive_quality_changes":ap["quality_changes"],"adaptive_cache_evictions":ap["cache_evictions"],"exact_cost":ex["cost"],"approx_cost":ap["cost"]})
    save("B3_Correctness_and_Counterexamples.csv",rows); save("B3_Scalability.csv",scale); return rows,scale
def encode(device,network):
    battery=int(device["battery"]); cpu=int(device["cpu"]); bw=float(network["mbps"])
    for res,br,energy in [("720p",1800,2.4),("480p",900,1.3),("360p",500,0.8)]:
        sec=(br*30/8/1000)*8/bw; use=energy*(1 if cpu>=60 else 1.25)
        if sec<=float(network["max_upload_s"]) and use<=max(.2,battery*.035):
            return {"resolution":res,"bitrate_kbps":br,"upload_seconds":round(sec,2),"energy_units":round(use,2),"battery_remaining_est":round(max(0,battery-use),2),"decision":"upload_now" if network["kind"]=="good" else "schedule_unmetered"}
    return {"resolution":"360p","bitrate_kbps":500,"upload_seconds":round((500*30/8/1000)*8/bw,2),"energy_units":.8,"battery_remaining_est":round(max(0,battery-.8),2),"decision":"defer_until_better_network"}
def b4():
    rows=[]
    for x in load("b4_device_profiles.json"): rows.append({"device":x["device"]["name"],**encode(x["device"],x["network"])})
    save("B4_Encoding_Decisions.csv",rows)
    net={"mbps":.8,"max_upload_s":30,"kind":"metered"}; candidates=[]
    for res,br,en in [("720p",1800,3),("480p",900,1.625),("360p",500,1)]:
        sec=(br*30/8/1000)*8/net["mbps"]; candidates.append({"resolution":res,"bitrate_kbps":br,"seconds":round(sec,2),"energy":en,"feasible":sec<=30 and en<=95*.035})
    save("B4_Challenge_Search.csv",candidates); return rows,encode({"battery":95,"cpu":25},net)
def main():
    p=argparse.ArgumentParser(); p.add_argument("task",nargs="?",default="all",choices=["all","b1","b2","b3","b4"]); a=p.parse_args()
    funcs={"b1":b1,"b2":b2,"b3":b3,"b4":b4}
    result={k:fn() for k,fn in funcs.items()} if a.task=="all" else funcs[a.task]()
    print(json.dumps(result,indent=2)); print("CSV outputs:",OUT)
if __name__=="__main__": main()
