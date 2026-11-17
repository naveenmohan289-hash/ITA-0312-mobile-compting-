# Assignment 3 – Network Patterns and Flow Diagrams

## Q1 – Wireless network architecture
```mermaid
flowchart LR
 MN1[Mobile node 1] --> AP1[Access point / Base station 1]
 MN2[Mobile node 2] --> AP1
 AP1 --> GW[Gateway / Router]
 GW --> CORE[Core network]
 CORE --> APP[Application server]
 MN3[Moving mobile node] -. handoff .-> AP2[Access point / Base station 2]
 AP2 --> GW
```

## Q2 – Mobile IP registration and packet delivery
```mermaid
sequenceDiagram
 participant MN as Mobile Node
 participant FA as Foreign Agent
 participant HA as Home Agent
 participant CN as Correspondent Node
 MN->>FA: Agent discovery / obtain CoA
 MN->>HA: Registration request
 HA-->>MN: Registration accepted/rejected
 CN->>HA: Packet to home address
 HA->>FA: Encapsulated tunnel packet
 FA->>MN: Decapsulate and deliver
```

## Q3 – Cellular and ad hoc patterns
```mermaid
flowchart TB
 subgraph Cellular
  U1[Mobile user] --> BS[Base station]
  U2[Mobile user] --> BS
  BS --> EPC[Core network]
 end
 subgraph AdHoc
  N1[Node A] --- N2[Node B]
  N2 --- N3[Node C]
  N3 --- N4[Node D]
  N1 -. multi-hop path .- N4
 end
```

## Q4 – Ambulance Mobile IP application
```mermaid
flowchart LR
 AMB[Ambulance MN] --> VIS[Visited network / FA]
 VIS --> HA[Home Agent]
 HA --> HOSP[Hospital / dispatch CN]
```

## Q5 – DSDV route update
```mermaid
flowchart LR
 S[Source S] --- A[Relay A]
 A --- D[Destination D]
 S --- B[Relay B]
 B --- D
```

## Q6 – AODV discovery
```mermaid
sequenceDiagram
 participant S as Source
 participant A as Intermediate A
 participant D as Destination
 S->>A: RREQ
 A->>D: RREQ (record reverse route)
 D-->>A: RREP
 A-->>S: RREP (install forward route)
 S->>A: Data packet
 Note over S,D: Link break triggers RERR and route rediscovery
```

## Q7 – Disaster response hybrid network
```mermaid
flowchart TB
 AMB[Ambulances] <--> R1[Mobile relay 1]
 POL[Police vehicles] <--> R1
 RES[Rescue teams] <--> R2[Mobile relay 2]
 MED[Medical teams] <--> R2
 R1 <--> R2
 R1 <--> CP[Portable command post]
 R2 <--> CP
 CP --> HA[Home Agent when backhaul exists]
 HA --> CN[Hospital / dispatch]
```
