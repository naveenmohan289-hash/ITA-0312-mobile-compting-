# Q4 – Applications of Mobile IP and Routing Requirements (7 Marks)

## Selected application: Emergency ambulance communication
An ambulance sends patient status, location updates and requests for medical support while travelling between coverage areas.

## Entities and architecture
- Mobile nodes: ambulance terminal, paramedic device and mobile command vehicle.
- Access: cellular base station, portable access point or emergency relay.
- Mobility: MN home address, HA, visited-network FA/CoA and CN (hospital/dispatch server).
- Routing: gateway/IP network when available; ad hoc relays if fixed infrastructure fails.

```mermaid
flowchart LR
 AMB[Ambulance MN] --> FA[Visited network / FA]
 FA --> GW[Gateway]
 GW --> HA[Home Agent]
 HA --> CN[Hospital / Dispatch CN]
```

## Communication flow
Ambulance discovers the visited network, obtains a CoA and registers it with HA. Dispatch sends traffic to the stable home address. HA tunnels packets to the current CoA. When the ambulance changes network, it registers the new CoA.

## Requirements
- Low delay for emergency alerts and patient status.
- High packet delivery and acknowledgement/retry.
- Authentication, encryption and access control for patient data.
- Handoff with minimal interruption.
- Priority scheduling for emergency traffic.
- Fallback routing if a base station or backhaul fails.

Mobile IP is suitable when an ambulance must preserve a stable IP identity across IP networks. It does not guarantee connectivity when all links fail; buffering, redundant links and ad hoc fallback are needed.

## Result
Mobile IP supports session reachability across visited networks, while routing/reliability mechanisms handle the changing path. Evaluate delay, packet delivery, handoff interruption and security.
