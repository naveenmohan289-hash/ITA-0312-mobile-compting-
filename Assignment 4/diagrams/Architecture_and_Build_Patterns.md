# Assignment 4 — Figures and Build Patterns

## Figure 1: Android layered architecture (Part I Task 1)
```mermaid
flowchart TB
  APP[Applications: UI / domain / data]
  FW[Framework + system services: Activity, Package, Power, Location, Notification]
  ART[Android Runtime: ART / DEX / GC / JIT / AOT]
  NAT[Native libraries and daemons: Bionic / Binder / media / graphics]
  HAL[Android HAL: camera / sensor / GNSS / power / audio]
  K[Linux kernel: scheduler / VM / Binder driver / network / security]
  D[Device drivers]
  HW[Hardware: CPU / RAM / flash / modem / display / sensors]
  APP --> FW --> ART --> NAT --> HAL --> K --> D --> HW
```

## Figure 2: Secure application call and enforcement path
```mermaid
sequenceDiagram
  participant A as App process (UID)
  participant F as Framework API
  participant B as Binder driver
  participant S as Privileged system service
  participant P as Permission/AppOps/SELinux
  participant H as HAL/native service
  participant K as Kernel driver
  participant D as Device
  A->>F: API request
  F->>B: Binder transaction
  B->>S: IPC with caller identity
  S->>P: Check permission and policy
  P-->>S: Allow or deny
  S->>H: Hardware operation
  H->>K: Kernel interface
  K->>D: Driver controls hardware
  D-->>A: Result via callback/IPC
```

## Figure 3: Android process launch and first frame (Part I Task 3)
```mermaid
flowchart TD
  L[Launcher tap] --> AM[ActivityTaskManager]
  AM --> Z[Zygote fork or reuse process]
  Z --> SEC[UID / SELinux / process setup]
  SEC --> ART[ART VM / class loader / DEX]
  ART --> APP[Application and providers]
  APP --> ACT[Activity lifecycle callbacks]
  ACT --> R[Measure / layout / draw]
  R --> SF[RenderThread + SurfaceFlinger]
  SF --> SCREEN[First visible frame]
```

## Figure 4: RuralCare offline-first architecture (Part I Task 6)
```mermaid
flowchart TB
  UI[Native UI / MIDlet / WML] --> DOM[Validation and domain use cases]
  DOM --> ENC[UUID + hash + AES-GCM encryption]
  ENC --> Q[Durable encrypted offline queue]
  Q --> JOB[WorkManager / BackgroundTasks / constrained MIDlet sync]
  JOB --> TLS[Authenticated TLS + idempotency key]
  TLS --> API[Server API]
  API --> DB[Unique UUID constraint + audit database]
  API --> ACK[Per-record ACK]
  ACK --> Q
```

## Figure 5: Part II MVVM and worker execution pattern
```mermaid
flowchart LR
  V[View / Activity / Compose] --> VM[ViewModel]
  VM --> UC[Use case / domain policy]
  UC --> EX[Executor / coroutine worker]
  EX --> REPO[Repository]
  REPO --> DB[Encrypted local database]
  REPO --> OS[Android OS services]
  OS --> NET[Network / sensors / location]
  REPO --> VM
  VM --> V
```

## Figure 6: Battery-aware tracking policy state machine
```mermaid
stateDiagram-v2
  [*] --> Balanced
  Balanced --> Conserve: battery <= 20% or low power
  Balanced --> Moving: motion = moving
  Balanced --> Charging: charging and Wi-Fi
  Balanced --> Critical: battery <= 10% or device hot
  Moving --> Balanced: stationary
  Moving --> Conserve: low battery
  Charging --> Balanced: unplugged
  Conserve --> Balanced: battery > 20% and low-power off
  Conserve --> Critical: battery <= 10% or hot
  Critical --> Conserve: cooled and battery > 10%
```

## Build/test patterns
- **Part I:** design/specification only; no SDK, emulator or source code.
- **Part II:** separate UI, domain, data and OS-service adapters. Keep policy evaluation pure and deterministic; inject clock/network/battery inputs for tests.
- **Security invariant:** encrypt before persistence; authenticate TLS before upload; do not mark records synced before server ACK.
- **Power invariant:** no permanent wakelock; batch sensors/network; emergency override is explicit and logged.
- **Validation:** every test has input, expected decision, actual output, evidence source and interpretation.
