"""Assignment 3 deterministic Mobile Computing teaching simulations.
Run from repository root: python "Assignment 3/mobile_computing_assignment3.py"
Uses only Python standard library. Results are illustrative model estimates.
"""
import csv
from pathlib import Path
BASE=Path(__file__).resolve().parent
IN=BASE/"inputs"; OUT=BASE/"outputs"; OUT.mkdir(exist_ok=True)
def read_csv(name):
    with (IN/name).open(newline="",encoding="utf-8") as f: return list(csv.DictReader(f))
def write_csv(name, rows):
    if rows:
        with (OUT/name).open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def rnd(x): return round(float(x),2)
# Q1: expected packet delivery and delay under different mobility levels.
rows=[]
for r in read_csv("q1_mobility_scenarios.csv"):
    n=int(r["packets"]); loss=float(r["base_loss_percent"])+int(r["mobility_level"])*1.5
    got=round(n*(1-loss/100)); delay=float(r["base_delay_ms"])+float(r["handoff_delay_ms"])*0.25
    rows.append({"scenario":r["scenario"],"mobility_level":r["mobility_level"],"bandwidth_mbps":r["bandwidth_mbps"],"packets_sent":n,"packets_delivered":got,"packets_lost":n-got,"pdr_percent":rnd(got/n*100),"estimated_delay_ms":rnd(delay)})
write_csv("Q1_Mobility_Results.csv",rows)
# Q2: registration delay and tunnel encapsulation overhead.
rows=[]
for r in read_csv("q2_mobile_ip_scenarios.csv"):
    n=int(r["packets"]); got=round(n*(1-float(r["loss_percent"])/100))
    rows.append({"scenario":r["scenario"],"registration_delay_ms":r["registration_delay_ms"],"packets":n,"tunnel_overhead_bytes":int(r["tunnel_overhead_bytes"])*n,"delivered_packets":got,"lost_packets":n-got,"pdr_percent":rnd(got/n*100)})
write_csv("Q2_MobileIP_Results.csv",rows)
# Q3: comparison matrix.
write_csv("Q3_Architecture_Comparison.csv",[
{"parameter":"Infrastructure","cellular":"Base stations and core network","ad_hoc":"No fixed infrastructure required"},
{"parameter":"Communication","cellular":"Through base station","ad_hoc":"Direct or multi-hop peer forwarding"},
{"parameter":"Mobility","cellular":"Managed cell handoff","ad_hoc":"Neighbour and route changes"},
{"parameter":"Routing","cellular":"Infrastructure-assisted","ad_hoc":"Distributed routing"},
{"parameter":"Failure","cellular":"Cell outage can disrupt service","ad_hoc":"Alternate peer route may exist"}])
# Q4: requirements register.
rows=[]
for r in read_csv("q4_application_requirements.csv"):
    rows.append({"application":r["application"],"delay_target_ms":r["maximum_delay_ms"],"delivery_target_percent":r["minimum_delivery_percent"],"mobility":r["mobility_level"],"security":r["security_level"],"design_status":"REVIEW AGAINST TEST RESULTS"})
write_csv("Q4_Application_Requirements.csv",rows)
# Q5: count periodic DSDV update transmissions.
rows=[]
for r in read_csv("q5_network_sizes.csv"):
    intervals=int(r["simulation_time_s"])//int(r["periodic_update_interval_s"])
    rows.append({"nodes":r["nodes"],"update_interval_s":r["periodic_update_interval_s"],"simulation_time_s":r["simulation_time_s"],"estimated_control_packets":intervals*int(r["control_packets_per_update"])})
write_csv("Q5_DSDV_Overhead.csv",rows)
# Q6: compare configured DSDV periodic updates with an AODV discovery-message estimate.
rows=[]
for r in read_csv("q6_protocol_scenarios.csv"):
    rows.append({"scenario":r["scenario"],"nodes":r["nodes"],"mobility_events":r["mobility_events"],"dsdv_control_messages":r["dsdv_periodic_updates"],"aodv_control_messages_estimate":int(r["aodv_route_discoveries"])*3,"dsdv_initial_route_delay_ms":r["dsdv_route_setup_ms"],"aodv_initial_route_delay_ms":r["aodv_route_setup_ms"]})
write_csv("Q6_Protocol_Comparison.csv",rows)
# Q7: estimate delivery under link failures and mobility.
rows=[]
for r in read_csv("q7_emergency_tests.csv"):
    n=int(r["traffic_packets"]); loss=min(float(r["link_failure_percent"])+int(r["mobility_events"])*0.25,95)
    got=round(n*(1-loss/100)); delay=float(r["base_delay_ms"])+int(r["mobility_events"])*8
    rows.append({"test_case":r["test_case"],"nodes":r["nodes"],"mobility_events":r["mobility_events"],"packets_sent":n,"packets_delivered":got,"packets_lost":n-got,"pdr_percent":rnd(got/n*100),"estimated_average_delay_ms":rnd(delay),"aodv_control_message_estimate":int(r["mobility_events"])*3})
write_csv("Q7_Emergency_Validation.csv",rows)
print("Assignment 3 simulations completed.")
for p in sorted(OUT.glob("*.csv")): print(p.name, "records:", sum(1 for _ in p.open(encoding="utf-8"))-1)
