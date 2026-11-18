# PART I — Architecture Design and Analysis (50 marks)

Scope: Tasks 1–6 from Part I. This is design-only and intentionally contains no implementation code, consistent with the no-IDE/no-SDK instruction. Android is selected whenever one platform is required. OS behaviour varies by release and vendor.

# TASK 1 — Architecture Review (6)

## 1.1 Diagnose the draft (2)

1. **Drivers and HAL omitted.** No hardware-to-kernel interface is defined for camera, display, modem, GNSS or sensors; an engineer cannot identify device control or error paths.
2. **Native libraries and system services omitted.** Graphics, media, SQLite, networking, notifications and location have no owning layer or API contract.
3. **Kernel responsibility is vague and inaccurate.** Android uses a Linux monolithic kernel with modules. It schedules processes/threads, manages virtual memory, filesystems, networking, Binder driver, security hooks and device drivers; it does not execute app UI logic.
4. **Runtime semantics are missing.** APKs contain DEX bytecode and optional native libraries. ART verifies/loads DEX and uses interpretation, JIT and profile-guided AOT. The draft does not state which code is translated or when.
5. **Permission lifecycle/enforcement is missing.** PackageManager records requests/grants; user/system grants runtime permissions where applicable; framework services, AppOps, Linux UID and SELinux enforce access. No enforcement point is identified.
6. **Power management is undefined.** There is no trigger, state, policy owner or mechanism. Doze, App Standby, JobScheduler, wakelocks, vendor Power HAL, CPU frequency scaling and suspend must be distinguished.
7. **App/OS communication path omitted.** SDK calls, Binder IPC, JNI/NDK and system calls are not mapped; privilege boundaries and error returns cannot be evaluated.
8. **Process isolation/lifecycle omitted.** Per-app UID, SELinux domain, process importance, Activity lifecycle and process death are necessary to reason about protection and state restoration.

## 1.2 Repaired Android layered specification (3)

| Layer | Responsibility | Exposes upward | Depends on below |
|---|---|---|---|
| 0 Hardware | CPU, RAM/MMU, flash, display, camera, GNSS, sensors, modem, PMIC | Interrupts, registers, DMA, physical resources | Board, firmware, electrical design |
| 1 Linux drivers | Handle interrupts, DMA, device queues, device power and hardware-specific control | Kernel device interfaces, input/network events | Hardware buses, clocks and firmware |
| 2 Linux kernel | Process/thread scheduler, virtual memory, filesystem, networking, Binder driver, security hooks, suspend/resume | Syscalls, sockets, Binder device, procfs/sysfs, signals | Drivers and hardware |
| 3 Android HAL | Vendor interfaces for camera, audio, sensors, GNSS, graphics and power | Stable hardware service contracts | Kernel drivers and vendor firmware |
| 4 Native libraries/daemons | Bionic, libbinder, graphics/media/SQLite/TLS libraries, SurfaceFlinger and daemons | C/C++ APIs, native services and JNI libraries | Kernel syscalls, HAL |
| 5 Android Runtime (ART) | Loads/verifies DEX; class loading, managed heap/GC, interpreter, JIT, profile-guided AOT; Zygote preloads and forks | Java/Kotlin execution, JNI, managed threads and heap | Linux process/memory services and native libraries |
| 6 Framework/system services | ActivityManager, PackageManager, WindowManager, PowerManager, LocationManager, NotificationManager, ConnectivityManager, permission controller | SDK APIs, lifecycle callbacks, permission prompts, jobs, notifications | ART, native services, HAL, Binder/kernel |
| 7 Applications | UI, domain logic, data layer and optional NDK libraries; normally own Linux UID and SELinux domain | User-facing functionality | Framework APIs, ART, app-private storage |

**Explicit locations:** kernel = Layer 2; runtime = Layer 5; permission decisions = PackageManager/permission controller and AppOps at Layer 6; enforcement = framework services plus UID/SELinux/kernel at Layers 2–6; power policy = PowerManager/DeviceIdleController/JobScheduler at Layer 6, vendor Power HAL at Layer 3 and CPU-frequency/cpuidle/suspend at Layer 2.

**Call path:** app API → framework SDK → Binder proxy/driver → privileged system service → permission/AppOps/UID/SELinux check → HAL/native service → kernel driver → hardware. Return travels through Binder callback, intent or listener. JNI/NDK and syscalls are alternative native paths, not security bypasses.

## 1.3 Design defence (≤100 words) (1)

This is a technical specification because every layer has a bounded responsibility, an upward interface and a dependency below. It locates kernel, ART, HAL, framework services and power controls, and identifies the IPC and privilege boundaries. It names who grants and enforces permissions rather than using a general claim that the OS is secure. An engineer can allocate implementation work from the interface contracts, while a tester can inspect Binder calls, lifecycle callbacks, permission decisions and power-state transitions.

# TASK 2 — Android vs iOS vs Windows (8)

## 2.1 Requirement model (2)

- Input: platform architecture, background message workload, OS versions, push requirements and security constraints.
- Output: platform-specific delivery design and realistic promise for delivery after screen-off, suspension and process death.
- Objective: deliver authenticated messages with bounded delay while protecting content and limiting wake-ups.
- Constraints: background quotas, user permission, sandbox, battery, network loss, process death and UI responsiveness.
- Decision: use native push adapters with a shared message protocol; define which work is allowed in background.
- Required facts: kernel/syscall boundary, process launch, runtime/compiler, framework lifecycle, sandbox, IPC, push service, background policy, key storage and TLS.

## 2.2 Hypothesis (1)

OS-controlled push and background-execution policy will affect screen-off delivery more than kernel family alone because the system push daemon can receive an event and display a notification even when the application process is suspended or absent.

## 2.3 Comparison matrix (3)

| Dimension | Android | iOS | Windows |
|---|---|---|---|
| Kernel | Linux monolithic kernel with modules, Binder driver, SELinux | XNU hybrid: Mach, BSD and I/O Kit | Windows NT hybrid kernel: executive, scheduler, memory and I/O managers |
| Kernel interface | Linux syscalls, Binder device, sockets, ioctl, procfs/sysfs | Mach traps/ports, BSD/POSIX syscalls, IOKit | NT system services via Win32/NTDLL; object, I/O and ALPC mechanisms |
| Runtime | ART executes DEX using verification, interpreter, JIT and profile-guided AOT; JNI to native | Native ARM64 binaries; Objective-C runtime supplies classes/selectors/dynamic dispatch; Swift/Obj-C use ARC | WinRT is an API contract; packaged apps may use native PE or .NET IL/CoreCLR/AOT depending on app model |
| Framework | Android SDK: Activity, Service, BroadcastReceiver, ContentProvider, Jetpack | Cocoa Touch/UIKit/SwiftUI, UIApplication/scenes and UIViewController | WinUI/UWP/Windows App SDK and WinRT contracts |
| Isolation | Per-app Linux UID, SELinux domain, private storage, permission/AppOps | App sandbox/container, code-signing entitlements, privacy permissions | AppContainer/package identity capabilities for packaged apps; desktop apps differ |
| IPC | Binder RPC, intents, providers, sockets/shared memory | XPC, Mach ports, NSXPCConnection, shared containers | COM/WinRT activation, RPC/ALPC, named pipes, app services |
| Push/background | FCM via Google Play services/system components; Doze and priority limits apply | APNs via push daemon; alerts can display when app not running; silent pushes discretionary/throttled | WNS and background task activation subject to app model and OS policy |
| Messaging consequence | Use FCM for notification/wake hint, persist by ID and handle process recreation | Use APNs alert for visible message; do not promise silent-push execution | Use WNS and supported activation; do not depend on permanent socket execution |

**Decision:** native push adapters (FCM/APNs/WNS), shared message schema, server-side durable inbox, message IDs, acknowledgements and idempotent retry. Push is not exactly-once storage/transport.

## 2.4 Screen-off trace (1)

Android: sender → FCM infrastructure → Google Play services → notification service validates app/channel/permission → notification displayed; where permitted, app process/callback is scheduled → ART runs messaging callback → app verifies and persists message ID → notification shown/updated. Doze may defer normal priority.

iOS: sender → APNs → device push daemon → UserNotifications validates entitlement/authorisation and displays alert → if allowed, system may wake app for callback → app verifies/persists. Silent pushes are discretionary and throttled.

## 2.5 Process killed challenge (1)

1. Prediction: visible alert may still display on both platforms because push/notification daemons are OS-managed; arbitrary app processing is not guaranteed.
2. Responsible components: Android FCM/notification service and process manager; iOS APNs daemon/UserNotifications and lifecycle policy.
3. Trace: push to system daemon → eligible alert shown → user taps → OS creates app process → runtime initialises → launch/scene callback reads durable inbox → app fetches canonical message by ID.
4. Prediction holds for user-visible alerts, not guaranteed background execution. Exactly-once logical processing requires server IDs and idempotent writes.

# TASK 3 — Runtime Environment (9)

## 3.1 Execution model (1)

| Platform | Delivered code | Loader | When machine instructions execute |
|---|---|---|---|
| Android ART (Dalvik is legacy) | DEX plus optional native .so | Package installer, Zygote fork, ART class loader | Interpreter/JIT at runtime; profile-guided AOT may compile during install/maintenance; native library already machine code |
| iOS | Signed ARM64 native executable/frameworks | launchd/kernel and dyld | Native instructions after mapping/linking; Obj-C runtime initialises metadata/dynamic dispatch |
| Windows | Native PE or .NET IL assemblies, depending on app model | Windows loader/package activation; CLR for managed assembly | PE is machine code; IL JIT/AOT according to deployment. WinRT is API contract, not universal runtime |

## 3.2 Android launch sequence (2)

| Step | Component/action | Purpose | Prerequisite |
|---|---|---|---|
| 1 | Launcher requests Activity through ActivityTaskManager/ActivityManager Binder | Selects component/task | Installed, enabled package |
| 2 | Zygote forks process or existing process reused | App gets isolated process while sharing preloaded pages | Zygote and kernel process/memory services |
| 3 | Kernel applies UID, groups, SELinux and limits | Establishes isolation before app code | Package security metadata |
| 4 | ART initialises VM/class loader, loads DEX; linker loads native libraries | Makes classes/native dependencies executable | Address space, mapped APK/DEX, runtime libraries |
| 5 | ActivityThread binds app, creates Application; providers may install | Runs app-level setup | ART, main looper, framework connection |
| 6 | Activity onCreate/onStart/onResume | Restores/initialises screen and connects UI | App object, resources, lifecycle service |
| 7 | View measure/layout/draw; RenderThread and SurfaceFlinger compose frame | Produces first visible screen | Window token, display/graphics service |

## 3.3 Runtime strategies (4)

- **Interpretation:** executes bytecode without compiling every method first. ART retains interpreter paths for cold/less-used code.
- **JIT:** compiles hot methods at runtime; faster repeated execution but consumes CPU and temporary memory.
- **AOT:** compiles before execution. iOS app code is normally native AOT. ART can use install-time/profile-guided AOT.
- **Profile-guided compilation/Baseline Profiles:** identify hot startup/interaction paths and guide ART compilation; do not eliminate runtime profiling.

| Runtime | Memory | Native access | Startup, footprint, portability |
|---|---|---|---|
| ART Kotlin/Java | Tracing GC; cheap allocation, but GC uses CPU and may pause | JNI/NDK, native libs, syscalls | DEX portability across Android ABIs; JIT warm-up; AOT costs storage but improves hot paths |
| Swift/Objective-C | ARC reference counting; retain/release and autorelease pools; cycles possible | Swift ABI, Objective-C runtime, C APIs, Darwin syscalls | Native code avoids managed JIT warm-up; architecture-specific binaries; object graph affects memory |
| Windows .NET/WinRT | .NET tracing GC; native/COM resources require deterministic disposal | WinRT/COM ABI, P/Invoke, Win32 | IL portability across supported runtime; JIT/AOT trade startup/footprint; WinRT is not a runtime |

**Low-memory conclusion:** no universal winner. A small native/AOT app with bounded allocations is predictable. On Android, ART with bounded caches, limited object churn and startup profiles is preferable to assuming GC alone solves pressure. Swift ARC avoids tracing GC but still has retain cycles and native memory pressure.

## 3.4 Cold/warm trace (1)

Cold: launch request → Zygote fork → security setup → ART initialisation/class loading → Application/provider setup → Activity callbacks → layout/draw. Warm: reuse live process and VM; skip fork and most VM setup; resume or recreate Activity, restore state and draw. Warm is not guaranteed after memory pressure.

## 3.5 Dependency (1)

Kernel must create process, map memory and schedule threads before ART executes. ART must initialise class loading, heap and main looper before framework callbacks instantiate app classes. Framework services must provide resources, window token and permission state before protected APIs or rendering can work. Therefore the launch order is a dependency graph.

# TASK 4 — Security Forensics (7)

Chosen platform: Android.

## 4.1 Defect mapping (2)

| Defect | Unused mechanism | Why OS cannot protect user |
|---|---|---|
| Request all permissions in advance | Least privilege, runtime permission, AppOps | Broad access increases damage; OS cannot make an unnecessary request appropriate |
| Token in other-app-readable file | UID sandbox, private storage, Keystore | Developer intentionally bypasses file isolation |
| Accept updates from any source | Package signing and publisher verification | Unverified app-level update can replace trusted code/data |
| Plain HTTP | TLS and certificate validation | Network attacker can observe/modify traffic; sandbox does not protect data after transmission |

## 4.2 Attack trace (2)

Malicious app reads the shared-readable token: confidentiality is first lost at file read. On public Wi-Fi, attacker intercepts the HTTP update request and changes note content: integrity is lost when the server accepts modified data. Stolen token also enables replay while valid. Local disclosure and missing TLS compound.

## 4.3 Minimal repair (2)

1. Request only the permission when feature is used; explain purpose; handle denial/revocation. PackageManager/permission controller records grant and framework services enforce it.
2. Store token in app-private encrypted storage; wrap AES-GCM data key with Android Keystore, hardware-backed where available.
3. Verify update publisher signature, package identity and monotonic version; reject unknown signer/downgrade.
4. Require HTTPS with certificate-chain/hostname validation; disable cleartext in Network Security Config. Pin only with safe rotation/recovery.

## 4.4 Regression (1)

Contact selection still works: request READ_CONTACTS only when user chooses import, or use system contact picker for least privilege. Allow → selected contact imported; deny → no contact data read and app continues; revoke → later access denied gracefully.

# TASK 5 — Power Management (7)

## 5.1 State policy (3)

| State | Hardware/kernel | Entry | Exit | Allowed work |
|---|---|---|---|---|
| Active | Display on, interactive CPU, sensors as requested | User interaction/foreground task | Screen off and no urgent work | UI, bounded sensor/network |
| Idle/Doze | Display off, CPU idle between maintenance windows, network/alarm quotas | Screen off, stationary, unplugged and idle criteria met | Motion, charger, interaction or maintenance window | System services, batched jobs, qualifying urgent push |
| Suspended | CPUs mostly suspended, RAM retained, wake sources armed, modem paging | No runnable work and suspend blockers released | Interrupt, alarm, push/modem or power button | Kernel wake handler/system work; app only in granted window |

Fitness app uses sensor hardware batching and short worker processing, persists compact records and releases wakelock. Never hold a permanent partial wakelock.

## 5.2 Urgent push change (2)

The insufficient assumption is that the app must keep CPU awake to receive all events. OS/modem push infrastructure receives network event. Use FCM/APNs to wake system components, display urgent notification and grant short processing time; use hardware batching and scheduled jobs for nonurgent samples. Stop permanent wakelock and network polling. A bounded wakelock is permitted only during a short critical operation.

## 5.3 Battery saver at 15% (2)

- Kernel/hardware: lower CPU frequency/voltage target, prefer efficiency cores, reduce background wakeups; vendor Power HAL coordinates hardware.
- Runtime: reduce background execution, avoid eager allocation and expensive periodic tasks.
- App: stationary sample interval rises (e.g. 15 s to 120 s); batch/defer normal uploads; retain emergency path and reduce nonessential animation.
- Trade-off: nonurgent location freshness falls; acceptable because emergency updates remain prioritised and user is informed.

# TASK 6 — RuralCare field data system (13)

## Stage 1: model (2)

Input: patient encounter forms, device class, connectivity/charge, identity and ACK state. Output: protected local records and canonical server records without silent loss or duplicate logical submissions. Objective: ten-hour offline-capable shift and safe eventual sync. Constraints: J2ME/WML limitations, network outages, battery, storage, key security and privacy. Decisions: native A/B apps, constrained C fallback, encryption, protocol and idempotent sync.

## Stage 2: strategy (2)

Use native Android/iOS apps for Classes A/B: modern sandbox, hardware-backed key storage, TLS, lifecycle-aware background scheduling. Share domain schema and REST API. For Class C use a minimal J2ME MIDlet/RMS only if device security and TLS are validated; otherwise WML over HTTPS with no sensitive persistent cache. If neither secure storage nor modern TLS exists, capture only a non-identifying visit reference or exclude the device from sensitive offline mode. This feature reduction is safer than pretending WML offers smartphone security.

## Stage 3: constraints and sync metadata (2)

| Class | Runtime | Security | Power | Offline storage | Connectivity |
|---|---|---|---|---|---|
| A Android | ART/Dex, Android framework | UID, SELinux, runtime permissions, Keystore, file encryption, TLS | Doze, WorkManager, foreground service only for user-visible tracking, sensor batching | Encrypted Room/SQLite | Wi-Fi/LTE/5G, intermittent |
| B iPhone | Swift/Obj-C native, Cocoa Touch | Sandbox, signing, Keychain, Data Protection, TLS | BackgroundTasks, Core Location, push, OS scheduling | Protected Core Data/SQLite | Wi-Fi/LTE/5G |
| C feature phone | J2ME MIDP/CLDC or WML | Variable PIN/isolation; TLS may be weak/absent | Coarse timers, limited background work | RMS or server session; no sensitive cache if insecure | 2G/GPRS/WAP, low bandwidth |

Retain UUID (dedupe), pseudonymous patient ID, visit ID, device/worker ID, monotonic sequence, UTC timestamp/timezone/clock quality, schema version, payload hash, encrypted payload, key version, sync state, retry count, server receipt/ACK and last attempt. UUID/hash detect duplicates/tampering; sequence/time preserve ordering; schema/key version support migration/decryption; ACK prevents deleting data before durable server commit.

## Stage 4: complete specification (4)

**Class A architecture:** Activity/Compose UI on main thread → domain use cases on worker executor → repository → encrypted Room/SQLite + Keystore → WorkManager sync; foreground service only for explicitly visible active tracking.

**Class B:** SwiftUI/UIKit → domain layer → repository → protected DB + Keychain → BackgroundTasks/URLSession background transfer; Core Location only with user-authorised mode.

**Class C:** MIDlet UI → validation/compact encoding → RMS queue; WML fallback submits minimal HTTPS form. No sensitive persistent cache where protection is not validated.

**Capture:** validate fields; generate UUID/sequence; canonicalise and hash; encrypt payload AES-256-GCM with random nonce; persist ciphertext, nonce, tag and key version transactionally; never log PHI/tokens. A/B data key is protected by Keystore/Keychain.

**Security:** at rest Android file-based encryption + Keystore; iOS Data Protection + Keychain; C only if validated secure storage exists. In transit TLS certificate validation + short-lived OAuth/OIDC token. On loss revoke token/device, trigger MDM wipe where enrolled; encryption remains mandatory because remote wipe is best effort while offline.

**Ten-hour power policy:** hardware sensor batching; moving 15–30 s, stationary 2–5 min; aggregate points; upload batches on Wi-Fi/charging or bounded cellular interval; WorkManager/BackgroundTasks; no permanent wakelock; warn before critical battery.

**Sync sequence:** (1) authenticate TLS and get server cursor; (2) select unsynced records in sequence order and bounded batch; (3) send UUID/hash/schema/idempotency key; (4) server validates and inserts under unique UUID constraint; (5) server returns per-record ACK/reject; (6) client marks only ACKed UUIDs synced; (7) interruption retains unACKed records and retries with exponential backoff/jitter; repeated UUID is idempotent; (8) corrections create new version/event with audit trail.

**Failure:** A/B transaction rollback and durable queue; retry on network return; invalid token pauses for re-auth; full storage blocks new records with warning. C RMS full stops accepting offline records; network loss preserves only non-sensitive reference if storage insecure; unsupported TLS disables sensitive transfer and requires approved gateway/device. Server uses idempotent insert and per-record response.

## Stage 5: desk-check (1)

Class A is offline six hours: each encounter is validated, UUID assigned, encrypted and committed locally. Battery reaches 20%: policy lowers stationary sampling and defers normal upload. Phone lost before sync: no ACK means local-only records are not yet on server. Locked-device encryption/Keystore protects ciphertext. Exposed: minimal metadata such as app presence/record count. Lost: records are unrecoverable if device/key is destroyed and no backup exists. Recoverable: if device returns and user unlocks, data can sync; ACKed records are already on server. Offline-only data cannot be recovered magically.

## Stage 6: attack design (2)

| Adverse condition | Challenge and prediction | Trace/result |
|---|---|---|
| Stolen unlocked phone | Attacker may see decrypted screen/session | Re-auth, short timeout, minimum PHI display and remote revoke reduce but do not eliminate unlocked-window exposure; partially survives |
| Sync interrupted after server insert before ACK | Client cannot know commit status | Retry same UUID; server unique constraint returns prior result/ACK; survives if insert is transactional/idempotent |
| Class C lacks secure storage/TLS | PHI could leak at rest/in transit | Disable sensitive cache/transfer; allow non-identifying reference only or exclude device; full feature requirement fails until managed secure handset/gateway |
| Incorrect device clock | Timestamp order can be wrong | Preserve monotonic sequence and server receipt time; flag uncertain event time |

Critical decisions: encrypt before persistence, key isolation, UUID idempotency, delete only after ACK, and capability-gate Class C. Do not assume all feature phones provide encryption/TLS.
