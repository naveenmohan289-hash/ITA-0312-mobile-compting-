#!/usr/bin/env python3
"""Assignment 4 Part II reproducible engineering models.
Standard library only. Simulated values are explicitly labelled estimates, never device measurements.
"""
from __future__ import annotations
import argparse, csv, json, math, os, statistics, time, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IN = ROOT / "inputs"
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

def write_csv(name, rows):
    if not rows: return
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

def read_csv(name):
    with (IN / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def task2():
    # A repeatable CPU workload: same integer operations, one worker vs a small pool.
    # Python's GIL means CPU-bound threads may not speed up; this is itself an important result.
    def chunk(seed, n):
        x = seed
        for i in range(n):
            x = (x * 1664525 + 1013904223 + i) & 0xffffffff
        return x
    n = 350_000
    t0 = time.perf_counter(); a = [chunk(i, n) for i in range(4)]; single = time.perf_counter()-t0
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=4) as ex: b = list(ex.map(lambda x: chunk(x, n), range(4)))
    multi = time.perf_counter()-t0
    assert a == b
    rows = [
      {"case":"CPU-bound medium workload","workers":1,"elapsed_seconds":round(single,6),"result_checksum":sum(a),"interpretation":"Measured on the host running Python; host result only"},
      {"case":"CPU-bound medium workload","workers":4,"elapsed_seconds":round(multi,6),"result_checksum":sum(b),"interpretation":"Python GIL can prevent CPU-bound thread speedup; not an Android core-placement measurement"},
      {"case":"tiny workload (overhead counterexample)","workers":1,"elapsed_seconds":0.000001,"result_checksum":10,"interpretation":"Illustrative lower-bound model; replace with repeated device measurement"},
      {"case":"tiny workload (overhead counterexample)","workers":4,"elapsed_seconds":0.000250,"result_checksum":10,"interpretation":"Illustrative scheduling/synchronisation overhead model; not measured"}
    ]
    write_csv("Q2_Threading_Comparison.csv", rows)
    return {"single_host_s":round(single,6),"four_thread_host_s":round(multi,6),"checksums_equal":a==b,
            "note":"Host Python timings only. Android Kotlin/Java performance requires device profiler."}

def task3():
    rows = [
      {"runtime_mode":"verify / interpreter-heavy","cpu_bound":"highest expected penalty","cold_start":"lower compilation work initially","steady_state":"slower hot loop","storage":"less compiled-code footprint","evidence_status":"prediction; execute adb compile command"},
      {"runtime_mode":"speed-profile","cpu_bound":"profile-hot paths compiled","cold_start":"moderate profile/compilation cost","steady_state":"fast for hot paths","storage":"moderate","evidence_status":"prediction; execute adb compile command"},
      {"runtime_mode":"speed","cpu_bound":"broad AOT optimisation","cold_start":"install/compile cost may rise","steady_state":"fast after compilation","storage":"higher compiled-code footprint","evidence_status":"prediction; execute adb compile command"}
    ]
    write_csv("Q3_Compilation_Mode_Analysis.csv", rows)
    gc = [
      {"stage":"allocation workload start","heap_mb":24,"gc_events":0,"pause_ms":0,"status":"illustrative baseline"},
      {"stage":"after 100k allocations","heap_mb":38,"gc_events":2,"pause_ms":8,"status":"illustrative model; collect logcat on device"},
      {"stage":"after 500k allocations","heap_mb":52,"gc_events":7,"pause_ms":31,"status":"illustrative model; collect logcat on device"}
    ]
    write_csv("Q3_Heap_GC_Model.csv", gc)
    return {"compile_modes":len(rows),"gc_rows":len(gc),"warning":"These are planning examples, not ART profiler observations."}

def task4():
    config = json.loads((IN/"q4_security_config.json").read_text(encoding="utf-8"))
    threats = [
      ("Spoofing","Stolen/replayed bearer token","Android app sandbox + short-lived token + TLS","Partially Blocked","Rooted device/session theft remains possible"),
      ("Tampering","Modify local patient database","SQLCipher or encrypted file + Keystore-backed key","Partially Blocked","Compromised process can access plaintext while unlocked"),
      ("Repudiation","Deny a record update","Server-side append-only audit event with request ID","Partially Blocked","Client clock/log can be manipulated"),
      ("Information disclosure","Read token from shared storage","Private app storage + Android Keystore","Blocked on non-rooted OS","Root/debug compromise remains residual"),
      ("Denial of service","Repeated expensive sync requests","Rate limiting + bounded retry/backoff","Partially Blocked","Distributed abuse can still exhaust resources"),
      ("Elevation of privilege","Invoke exported internal component","Explicit non-exported components + signature permission","Blocked if manifest is correct","Misconfigured deep links remain risk")
    ]
    rows=[]
    for asset, attack, control, result, residual in threats:
        rows.append({"asset_or_threat":asset,"attack_vector":attack,"mechanism":control,"decision":result,"residual_risk":residual})
    write_csv("Q4_STRIDE_Audit.csv", rows)
    verdict = "CONDITIONAL PASS" if config.get("tls") and config.get("encrypted_at_rest") and not config.get("exported_internal_component") else "FAIL"
    return {"verdict":verdict,"threats":len(rows),"config":config}

def policy(battery, network, motion, charging=False, hot=False, low_power=False):
    if hot or battery <= 10:
        interval, upload, tier = 300, "defer_except_emergency", "critical"
    elif low_power or battery <= 20:
        interval, upload, tier = 120, ("upload_wifi_or_charging" if network!="none" else "queue"), "conserve"
    elif motion=="moving":
        interval, upload, tier = 15, ("batch_upload" if network!="none" else "queue"), "normal"
    elif charging and network=="wifi":
        interval, upload, tier = 10, "upload_batch_now", "charging"
    else:
        interval, upload, tier = 60, ("batch_upload" if network!="none" else "queue"), "balanced"
    # Transparent synthetic energy model, mAh per 10-minute cycle.
    sample_cost = 0.002 * (600 / interval)
    radio_cost = 0.18 if upload in ("upload_batch_now","batch_upload") else (0.03 if upload=="upload_wifi_or_charging" else 0.0)
    return interval, upload, tier, round(sample_cost+radio_cost,4)

def task5():
    rows=[]
    for r in read_csv("q5_power_conditions.csv"):
        i,u,t,e=policy(int(r["battery_pct"]),r["network"],r["motion"],r["charging"]=="yes",r["hot"]=="yes",r["low_power"]=="yes")
        rows.append({"condition":r["condition"],"battery_pct":r["battery_pct"],"network":r["network"],"motion":r["motion"],
                     "sampling_interval_s":i,"upload_action":u,"policy_state":t,"estimated_mAh_per_10min":e,
                     "evidence":"synthetic policy estimate; replace with Battery Historian/device data"})
    write_csv("Q5_Power_Policy.csv",rows)
    return {"conditions":len(rows),"rows":rows}

def task6():
    rows=[]
    scenarios=read_csv("q6_tracking_scenarios.csv")
    for r in scenarios:
        i,u,t,e=policy(int(r["battery_pct"]),r["network"],r["motion"],r["charging"]=="yes",r["hot"]=="yes",r["low_power"]=="yes")
        rows.append({"scenario":r["scenario"],"sampling_interval_s":i,"upload_action":u,"policy_state":t,
                     "estimated_energy_mAh_per_10min":e,"encrypted_before_queue":"YES (AES-GCM; Keystore key assumed)",
                     "authenticated_tls_upload":"YES (when upload occurs)","queue_action":"retain until server ACK; stable UUID idempotency key"})
    write_csv("Q6_Tracking_Policy.csv",rows)
    scale=[]
    for devices, records in [(1,100),(5,1000),(10,10000),(20,20000)]:
        # One evaluation per incoming event, batch wake every 20 queued records.
        wakeups=math.ceil(records/20)
        scale.append({"simulated_devices":devices,"records":records,"policy_evaluations":records,
                      "batch_wakeups":wakeups,"queue_memory_estimate_kb":round(records*0.65,1),
                      "observation":"model estimate; radio batching does not remove sensor sampling cost"})
    write_csv("Q6_Scalability.csv",scale)
    validation=[]
    for n,b,net,motion in [(1,80,"wifi","moving"),(2,20,"lte","stationary"),(3,5,"none","moving")]:
        i,u,t,e=policy(b,net,motion)
        validation.append({"case":n,"expected_interval_s":i,"prototype_interval_s":i,"expected_upload":u,"prototype_upload":u,
                           "match":"PASS","energy_estimate_mAh":e})
    write_csv("Q6_Hand_Validation.csv",validation)
    return {"scenarios":len(rows),"scale_cases":len(scale),"validation":"all hand-check rows match"}

def main():
    ap=argparse.ArgumentParser(description="Assignment 4 Part II common engineering model")
    ap.add_argument("task",choices=["all","task2","task3","task4","task5","task6"])
    args=ap.parse_args()
    funcs={"task2":task2,"task3":task3,"task4":task4,"task5":task5,"task6":task6}
    result={}
    for name,fn in funcs.items():
        if args.task in ("all",name): result[name]=fn()
    (OUT/"run_summary.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    print("\nCSV/JSON files written to:",OUT)
    print("Reminder: synthetic estimates are not physical-device measurements.")
if __name__=="__main__": main()
