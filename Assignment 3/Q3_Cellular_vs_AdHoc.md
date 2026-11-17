# Q3 – Cellular Networks versus Ad Hoc Wireless Networks (7 Marks)

## Cellular network
Mobile nodes communicate with a base station. Base stations connect through backhaul/core network to gateways and services. Mobility is supported by handoff between cells. Coverage depends on deployed infrastructure.

## Ad hoc network
Nodes communicate directly when neighbours are in range. Intermediate mobile nodes forward packets over multiple wireless hops. No fixed base station is required, but nodes must cooperate and maintain routes.

## Comparison

| Parameter | Cellular | Ad hoc |
|---|---|---|
| Infrastructure | Base stations and core | No fixed infrastructure |
| Communication | Through base station | Direct or multi-hop |
| Routing | Infrastructure-assisted | Distributed |
| Mobility | Cell handoff | Neighbour/route changes |
| Topology | Planned cells | Dynamic |
| Scalability | Wide coverage with operator planning | Limited by radio range, contention and routing load |
| Handoff | Managed by network | Route repair or neighbour change |
| Failure | Cell outage can disrupt service | Alternate peer routes may exist |
| Applications | Public voice/data, broadband, IoT | Disaster response, military, temporary field networks |

## Engineering decision
For a disaster area where fixed infrastructure is unavailable, choose an **ad hoc multi-hop network** as the immediate fallback. Rescue vehicles and portable relays forward traffic between teams. If a surviving cellular site or portable base station becomes available, use a hybrid design.

## Result
Cellular networks provide managed wide-area service but depend on infrastructure. Ad hoc networks can be rapidly deployed, although capacity and reliability depend on node density, energy and topology.
