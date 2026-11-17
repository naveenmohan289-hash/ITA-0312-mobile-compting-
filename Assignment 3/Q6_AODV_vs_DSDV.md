# Q6 – Reactive Routing and Protocol Comparison (7 Marks)

## Reactive routing and AODV
A reactive protocol discovers a route only when data must be sent and no valid route exists. AODV uses:
- **RREQ:** source broadcasts a Route Request.
- **RREP:** destination or a node with a fresh route replies.
- **RERR:** reports an unusable active route.
- **Sequence numbers:** help choose fresh routes and avoid routing loops.

## AODV discovery
1. Source checks its routing table.
2. If no valid route exists, it creates a unique RREQ and broadcasts it.
3. Intermediate nodes record reverse route and forward a new RREQ only once.
4. Destination/eligible intermediate node returns RREP.
5. Source installs the route and transmits data.
6. Link failure invalidates the route; RERR is sent and discovery may restart.

## DSDV versus AODV

| Feature | DSDV | AODV |
|---|---|---|
| Route discovery | Continuous maintenance | On demand |
| Initial data delay | Low if route is current | Discovery delay for unknown route |
| Control overhead | Periodic updates | RREQ/RREP/RERR when needed |
| Idle traffic | Updates continue | Lower control traffic when idle |
| Mobility | Periodic convergence may lag | Active route repair/discovery |
| Suitable use | Frequent traffic, steadier topology | Intermittent traffic, changing topology |

## Joint decision
For a highly dynamic network with intermittent traffic, select **AODV** because it avoids periodic updates for every destination. First-packet route discovery and repeated RREQ flooding during frequent breaks are disadvantages. Continuous emergency traffic with strict delay may justify a hybrid/local proactive strategy.

## Result
AODV is demand-driven; DSDV offers routes in advance at periodic overhead. Selection depends on traffic, mobility, node count, bandwidth and delay. Run program for `outputs/Q6_Protocol_Comparison.csv`.
