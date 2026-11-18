"""Run reproducible Mobile Computing simulations Q1-Q7.
Install: pip install numpy. Run: python Assignment/implement_q1_q7.py
Writes question-numbered CSV outputs under Assignment/outputs/.
"""
import csv, random, math
from pathlib import Path
import numpy as np
OUT=Path(__file__).parent/"outputs"; OUT.mkdir(exist_ok=True)
def save(name, header, rows):
    with open(OUT/name,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(header); w.writerows(rows)

# Q1: offline meter readings, immediate attempt vs 60 one-minute retries.
random.seed(42); rows=[]
for avail in (.9,.6,.3):
    immediate=delivered=0; delays=[]; lost_queue=0
    for _ in range(1000):
        if random.random()<avail: immediate+=1
        delay=next((m for m in range(1,61) if random.random()<avail),None)
        if delay is None: lost_queue+=1
        else: delivered+=1; delays.append(delay)
    rows += [[avail,"Immediate",immediate,0,1000-immediate,0],
             [avail,"Store-forward",delivered,delivered,lost_queue,round(np.mean(delays),3) if delays else 0]]
save("Q1_Synchronization.csv",["availability","strategy","delivered","delayed","lost","mean_delay_min"],rows)

# Q2: dedicated-channel allocation, with declared overhead assumptions.
random.seed(2026); workloads={
 "Continuous_voice":[(random.expovariate(1/3),random.randint(25,60)) for _ in range(1200)],
 "Bursty_data_10pct":[(random.expovariate(1/1.5),random.randint(1,3)) for _ in range(1200)],
 "Synchronized_edge":[(i*5+random.uniform(0,.05),random.randint(1,2)) for i in range(800)]}
rows=[]
for name,events in workloads.items():
 for scheme,capacity in (("FDMA",72),("TDMA",68)):
    ends=[0.0]*capacity; accepted=blocked=occupied=0
    for a,d in sorted(events):
        free=next((j for j,e in enumerate(ends) if e<=a),None)
        if free is None: blocked+=1
        else: ends[free]=a+d; accepted+=1; occupied+=d
    horizon=max(a+d for a,d in events); util=occupied/(capacity*horizon)
    rows.append([name,scheme,len(events),accepted,blocked,capacity,round(util,4)])
save("Q2_Access_Results.csv",["traffic","scheme","offered","accepted","blocked","usable_channels","utilization"],rows)

# Q3: DS-CDMA, Walsh/random codes, and asynchronous near-far.
rng=np.random.default_rng(7); N_BITS=2000
def hadamard(n):
 h=np.array([[1]])
 while len(h)<n: h=np.block([[h,h],[h,-h]])
 return h
ber=[]; cor=[]
for L in (8,16,64):
 W=hadamard(L)/np.sqrt(L)
 for mode in ("Walsh_equal_power","Random_codes_equal_power","Walsh_near_far_10x_one_chip"):
  for users in (2,4,min(8,L-1)):
   ids=[3,2]+[i for i in range(1,L) if i not in (2,3)][:users-2]
   codes=W[ids] if mode.startswith("Walsh") else rng.choice([-1,1],(users,L))/np.sqrt(L)
   bits=rng.choice([-1,1],(users,N_BITS)); amp=np.ones(users)
   if mode=="Walsh_near_far_10x_one_chip": amp[1]=10
   chips=np.einsum("ub,ul->bl",bits*amp[:,None],codes)
   if mode=="Walsh_near_far_10x_one_chip":
    shifted=np.roll(codes[1],1); chips+=(bits[1]*amp[1])[:,None]*(shifted-codes[1])[None,:]
   rx=chips+rng.normal(0,.12,(N_BITS,L)); decision=rx@codes[0]
   errors=int(np.sum(np.where(decision>=0,1,-1)!=bits[0]))
   ber.append([L,mode,users,errors,N_BITS,round(errors/N_BITS,5),10*math.log10(L)])
   cor.append([L,mode,users,round(float(np.max(np.abs(codes[0]@codes[1:].T))),5)])
save("Q3_BER.csv",["chips_per_bit","condition","users","bit_errors","bits_tested","BER","processing_gain_dB"],ber)
save("Q3_Correlation.csv",["code_length","condition","users","max_abs_cross_correlation"],cor)

# Q4: OFDMA scheduling over 1,000 fading realizations.
rng=np.random.default_rng(44); U=8; K=64; R=1000; noise=.18
sums={m:np.zeros(U) for m in ("Fixed_contiguous","Interleaved","Channel_aware")}
for _ in range(R):
 gains=rng.exponential(1,(U,K))
 groups={m:[[] for _ in range(U)] for m in sums}
 for k in range(K):
  groups["Fixed_contiguous"][k//8].append(k)
  groups["Interleaved"][k%U].append(k)
  groups["Channel_aware"][int(np.argmax(gains[:,k]))].append(k)
 for m,gg in groups.items():
  for u,ks in enumerate(gg):
   if ks: sums[m][u]+=sum(np.log2(1+gains[u,k]/noise) for k in ks)/R
rows=[]
for m,v in sums.items():
 rows.append([m,round(float(v.sum()),4),round(float(v.sum()**2/(U*(v@v))),4),*[round(float(x),4) for x in v]])
save("Q4_OFDMA.csv",["allocation","sum_bps_hz_proxy","jain_fairness"]+[f"user_{i+1}" for i in range(U)],rows)
orth=[]
n=np.arange(64)
for a,b in ((0,1),(0,7),(12,31)):
 orth.append([a,b,round(float(abs(np.vdot(np.exp(2j*np.pi*a*n/64),np.exp(2j*np.pi*b*n/64)))/64),12)])
save("Q4_Orthogonality.csv",["subcarrier_a","subcarrier_b","normalized_inner_product"],orth)

# Q5: ULA array-factor pattern and SIR for broadside beam, half-wavelength spacing.
angles=np.linspace(-90,90,1801); patterns=[]; sir=[]
def af_db(N,deg):
 psi=np.pi*np.sin(np.deg2rad(np.asarray(deg)))
 den=np.sin(psi/2); amp=np.ones_like(np.asarray(deg,dtype=float)); mask=np.abs(den)>1e-12
 amp[mask]=np.abs(np.sin(N*psi[mask]/2)/(N*den[mask]))
 return 20*np.log10(np.maximum(amp,1e-6))
for N in (2,4,8,16):
 p=af_db(N,angles)
 for a,v in zip(angles[::10],p[::10]): patterns.append([N,round(float(a),2),round(float(v),3)])
 for sep in range(5,61,5):
  val=10*np.log10(1/max(10**(af_db(N,np.array([sep]))[0]/10),1e-12))
  sir.append([N,sep,round(float(val),3),val>=10])
save("Q5_Patterns.csv",["elements","angle_deg","array_factor_db"],patterns)
save("Q5_SIR.csv",["elements","separation_deg","SIR_dB","meets_10dB"],sir)

# Q6: weighted technique matrix and sensitivity.
weights=[.22,.20,.18,.16,.10,.14]
ratings={"SDMA":[4,4,3,4,3,3],"TDMA":[3,2,3,4,4,3],"FDMA":[2,2,3,3,4,2],"CDMA":[4,4,4,4,2,3],"OFDMA":[5,5,3,5,3,4]}
fit={"Cellular_voice":{"SDMA":4,"TDMA":4,"FDMA":3,"CDMA":4,"OFDMA":5},
"Tactical_jam_resistant":{"SDMA":3,"TDMA":2,"FDMA":2,"CDMA":5,"OFDMA":3},
"Stadium_downlink":{"SDMA":4,"TDMA":2,"FDMA":2,"CDMA":3,"OFDMA":5},
"5000_sensors":{"SDMA":3,"TDMA":3,"FDMA":2,"CDMA":4,"OFDMA":3}}
rows=[]
for dep,adj in fit.items():
 for tech,rr in ratings.items(): rows.append([dep,tech,round(sum(w*x for w,x in zip(weights,rr))*adj[tech]/5,3)])
save("Q6_Weighted_Scores.csv",["deployment","technique","score"],rows)
sens=[]
for i in range(6):
 for factor in (.8,1.2):
  ww=weights.copy(); ww[i]*=factor; z=sum(ww); ww=[x/z for x in ww]
  for dep,adj in fit.items():
   sc={t:sum(w*x for w,x in zip(ww,ratings[t]))*adj[t]/5 for t in ratings}
   sens.append([i,factor,dep,max(sc,key=sc.get)])
save("Q6_Sensitivity.csv",["criterion_index","weight_factor","deployment","winner"],sens)

# Q7: pooled scheduling versus fixed allocation for 5,000 200-byte reports/minute.
random.seed(77); devices=5000; channels=80; bins=[0]*60
for _ in range(devices): bins[int(random.random()*60)]+=1
served=sum(min(x,channels) for x in bins); excess=sum(max(0,x-channels) for x in bins)
idle=[channels-x for x in bins]; remain=excess
for free in idle:
 take=min(free,remain); served+=take; remain-=take
 if remain==0: break
save("Q7_Redesign.csv",["design","devices","channels","reports_served","unserved","delivery_percent"],[
 ["Static_dedicated",5000,80,80,4920,1.6],["Pooled_on_demand",5000,80,served,remain,round(served/5000*100,2)]])
save("Q7_Load_Distribution.csv",["second","arrivals"],[[i,x] for i,x in enumerate(bins)])
print("Generated Q1-Q7 outputs in",OUT)
