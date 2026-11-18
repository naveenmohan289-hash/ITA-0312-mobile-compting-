# PART II — Engineering, Instrumentation, Testing and Optimisation (50 marks)

**Implementation boundary:** ../common.py implements reproducible host-side workload comparison, runtime-mode analysis dataset, STRIDE audit, power policy simulation, field-tracking policy and scale/validation tables. It is not an Android APK. Device-specific evidence must be collected on a real device/AVD. iOS profiling requires Xcode/Instruments on macOS and is not fabricated here.

## Environment record
Device/model: TO-COLLECT; Android build/API: TO-COLLECT; AVD RAM/CPU: TO-COLLECT; package: replace com.example.assignment4; Python: python --version; date/battery/network/screen: TO-COLLECT.

Run from Assignment 4:
    python common.py all
Outputs are written to outputs/. Python 3.9+, standard library only.

---

# TASK 1 — OS model, lifecycle and memory (8)

## 1.1 Layer/process/lifecycle mapping
Android: Linux kernel → HAL → native libraries/daemons → ART → framework/system services → application. Zygote preloads classes/resources and forks app processes. Binder driver and Binder interfaces provide IPC. Activity lifecycle: onCreate/onStart/onResume/onPause/onStop/onDestroy; Service and BroadcastReceiver lifecycles differ and receivers must finish quickly.

iOS: Core OS (XNU, drivers, security, networking) → Core Services (Foundation, Core Data, CFNetwork) → Media (Core Animation, AVFoundation, Metal) → Cocoa Touch (UIKit, UserNotifications). launchd coordinates process/service launch. XPC/Mach ports provide IPC. UIApplication/UIScene states include active, inactive and background; UIViewController callbacks manage screens.

Windows: NT kernel/drivers → system services/Win32 → WinRT/Windows App SDK/UI framework → app. Packaged-app lifecycle/background activation depends on app model. Use ETW/Process Explorer for Windows evidence if selected.

## 1.1 Android evidence commands
Run on connected device/AVD:
    adb devices
    adb shell getprop ro.build.version.release
    adb shell getprop ro.build.version.sdk
    adb shell ps -A | grep -E 'zygote|system_server|com.example'
    adb shell service list | grep -i activity
    adb shell dumpsys activity processes
    adb shell dumpsys meminfo com.example.assignment4
    adb shell cat /proc/$(adb shell pidof com.example.assignment4)/status
Binder evidence:
    adb shell service list
    adb shell dumpsys -l
    adb shell dumpsys activity services
Interpretation: zygote is the process template; system_server hosts core services. service list names Binder services but is indirect IPC evidence. PSS proportionally attributes shared pages; Java heap is not total process memory. Capture raw output.

Lifecycle evidence:
    adb logcat -c
    adb logcat -v time ActivityTaskManager:I ActivityManager:I AndroidRuntime:E *:S

## 1.2 Process/memory state
    adb shell dumpsys meminfo com.example.assignment4
    adb shell dumpsys activity processes
    adb shell dumpsys activity oom
    adb shell pidof com.example.assignment4
oom_adj/oom_score_adj indicates relative kill priority (higher generally more killable); process state reflects foreground, visible, service and cached work. Memory pressure may trim caches before killing. onTrimMemory is a hint, not guaranteed before process death.

## 1.3 Three conditions and predictions
| Condition | Prediction | Evidence | State |
|---|---|---|---|
| Foreground | Process remains; no trim expected | logcat, meminfo, process state | UI state normally retained |
| Background 5 min | May remain cached or be trimmed | dumpsys before/after | Saved state can restore after process death |
| Low memory | Cached process most likely trimmed/killed | trim logs, process list, ActivityTaskManager | Persisted state restored; transient fields lost |

Controlled test:
    adb shell am start -n com.example.assignment4/.MainActivity
    adb shell input keyevent KEYCODE_HOME
    adb shell am send-trim-memory com.example.assignment4 RUNNING_LOW
    adb shell dumpsys activity processes
    adb shell am force-stop com.example.assignment4
Force-stop is not the same as low-memory kill; label separately. Capture logs for each case and compare predictions. Do not invent callback logs.

## 1.4 Boundary test
Rotate while a form dialog and background save are active. This tests Activity recreation, transient dialog references and in-flight work. Persist draft state in ViewModel/SavedStateHandle and DB transaction; do not retain Activity statically. Record duplicate submission, lost fields and leaks.

---

# TASK 2 — Architecture assumptions vs measured reality (9)

A: compute-heavy parsing/filtering on main thread (poor responsiveness baseline). B: same deterministic workload on ExecutorService/coroutine worker; main thread receives result only. Use MVVM: View observes state; ViewModel coordinates; repository owns data; worker computes. SoC scheduler chooses cores based on utilisation/thermal policy; ordinary SDK apps cannot reliably pin big/LITTLE cores.

Run host model:
    python common.py task2
Q2_Threading_Comparison.csv includes actual host Python timings/checksum and a clearly labelled illustrative tiny-task overhead counterexample. Python GIL affects CPU threading; these are not Android Kotlin results. Implement same deterministic workload in Android main-thread and ExecutorService variants for required device evidence.

Android profiling:
    adb shell dumpsys gfxinfo com.example.assignment4 reset
    adb shell am start -n com.example.assignment4/.MainActivity
    adb shell dumpsys gfxinfo com.example.assignment4 framestats
    adb shell top -H -p $(adb shell pidof com.example.assignment4)
    adb shell dumpsys meminfo com.example.assignment4
Capture Android Studio CPU/Memory profiler or Perfetto. Record duration, CPU time, thread count, context switches if available, PSS/Java heap, allocation count, missed frame deadlines and input latency. Elapsed time alone is insufficient.

**Break assumption:** submit a tiny 10-iteration task to a new thread per item. Thread creation, queueing, synchronisation and context-switch overhead can exceed useful work. A lock around all workers is another counterexample. First harmful decision: creating more workers than useful parallel work or serialising them behind a lock. Repeat many times; report median and p95.

**Full-day requirement:** bounded worker pool, OS-selected efficiency cores, batching, WorkManager for nonurgent work, no busy loop, release wakelocks. Profile energy; elapsed time is not energy.

---

# TASK 3 — ART runtime benchmark and failure (10)

## Stage A
Workloads: CPU loop, allocation-heavy objects and 1,000-row scrolling list. Record cold/warm start, compilation state, GC events/pauses and heap growth.
    adb shell cmd package compile -m help
    adb shell dumpsys package com.example.assignment4
    adb shell cmd package compile -m speed-profile -f com.example.assignment4
    adb logcat -c
    adb logcat -v time -s art:I AndroidRuntime:E
    adb shell dumpsys meminfo com.example.assignment4
Cold = first launch after process absent; warm = process retained. Force-stop clears process, not necessarily ART profile/compilation state.

## Stage B
Run each mode separately:
    adb shell cmd package compile -m verify -f com.example.assignment4
    adb shell cmd package compile -m speed-profile -f com.example.assignment4
    adb shell cmd package compile -m speed -f com.example.assignment4
    adb shell dumpsys package com.example.assignment4
Prediction: verify/interpreter-heavy affects hot CPU loop most (lower steady-state speed, smaller compiled footprint); speed-profile compiles profile-hot methods (balanced); speed compiles broadly (higher storage/maintenance cost, faster hot execution). Record actual filter output and timing. ART options vary by release; device help is authoritative. Baseline Profiles guide hot startup/interaction paths but do not mean all methods are AOT.

## Stage C
In a test-only build, retain Activity in a static collection and block main thread. Never ship these defects.
- Leak: repeated screen creation, heap dump, retained Activity path, heap growth and GC frequency.
- Blocking: StrictMode detects main-thread I/O; ANR trace/watchdog reports input timeout.
    adb shell am force-stop com.example.assignment4
    adb logcat -c
    adb logcat -v time AndroidRuntime:E ActivityManager:E StrictMode:I *:S
    adb shell dumpsys meminfo com.example.assignment4
    adb shell dumpsys activity lastanr
ART heap/GC reports allocation/collection pressure; ActivityManager/watchdog reports ANR; LeakCanary can identify retained object path. Repair by removing static reference, bounding caches, moving I/O off main and using lifecycle-aware state.

## Stage D cross-platform
| Design | Startup/memory | UI thread | Native access |
|---|---|---|---|
| Android ART | DEX interpreter/JIT/AOT, managed heap/GC | Main looper; move CPU/I/O off it | JNI/NDK and Android APIs |
| iOS Swift ARC | Native AOT; retain/release; no tracing GC for ordinary Swift objects | Main actor/UI thread | Swift/Obj-C/C frameworks |
| Flutter Dart | Dart AOT release; Flutter engine/rendering footprint | Dart isolate plus platform/UI/render threads | Platform channels/plugins |
| React Native/WebView | JS engine + JSI/bridge or browser engine; JS heap/DOM/native views | JS thread plus native UI thread | Native modules/plugins/browser APIs |

Recommendation must follow measurements. Native per platform offers strongest platform fidelity/background integration; Flutter may suit a shared UI if startup/memory fit; React Native/WebView requires bridge/JS and memory profiling. No universal winner without target-device evidence.

---

# TASK 4 — Secure application audit (7)

Run:
    python common.py task4
Input fixture: inputs/q4_security_config.json. Output: Q4_STRIDE_Audit.csv (six threats, mechanism, decision, residual risk) and verdict in run_summary.json. STRIDE coverage: spoofing, tampering, repudiation, information disclosure, denial of service and elevation of privilege.

Android checks:
    adb shell dumpsys package com.example.assignment4
    adb shell cmd package list packages -U | grep com.example.assignment4
    adb shell run-as com.example.assignment4 ls files
    adb logcat -v time | grep -iE 'cleartext|SSL|permission'
run-as works only for debuggable packages and is not a production attack. Test only your own app and endpoint.

Prediction exercise: set tls false in JSON fixture or allow cleartext in disposable test app. Predict API traffic exposed and verdict changes to FAIL; run python common.py task4 and compare. A real device proxy trace must use a controlled test endpoint.

Third-party device-ID leak: asset is device identifier/network metadata; affected layer is app/network boundary. Sandbox cannot stop an app/library sending data using its own network permission. Detect by static dependency review, proxy capture or runtime network instrumentation. Remove/replace library, minimise identifier, require TLS and consent. Biometric extension binds Keystore key use to user authentication; work profile adds separate profile UID/data boundary and managed wipe; audit key attestation, profile separation and cross-profile export rules.

---

# TASK 5 — Power engineering (7)

Run:
    python common.py task5
Input q5_power_conditions.csv; output Q5_Power_Policy.csv. Model rules: hot/critical battery reduces sampling and defers upload; low power lengthens interval; moving increases sampling; charging Wi-Fi allows batch upload. Energy values are model estimates, not measured mAh.

Device commands:
    adb shell dumpsys batterystats --reset
    adb shell dumpsys deviceidle force-idle
    adb shell dumpsys deviceidle
    adb shell dumpsys batterystats
    adb shell dumpsys power
    adb shell dumpsys sensorservice
Exit forced idle:
    adb shell dumpsys deviceidle unforce
Measure baseline, DVFS/thermal, Doze/App Standby and app batching separately with same duration/screen/network/location/battery. Save Battery Historian or Energy Profiler capture. Track wakeup alarms, partial wakelock duration, radio active time, GPS/sensor and estimated energy. force-idle is a test control and can disrupt normal operation.

Conflict test: hold a partial wakelock in test build while idle. Predict Doze benefit reduced because CPU cannot fully suspend; compare batterystats wakelock and idle history. Frequent exact alarms can defeat batching.

Deployment:
- Always-on location: sensor batching and short foreground service matter; GPS/radio dominate.
- Gaming/media: display, GPU and sustained CPU dominate; DVFS/thermal governor and frame-rate limits matter.
- Managed fleet: OS-version compatibility, enterprise policy, background scheduling and observability matter; measure per version.

---

# TASK 6 — Battery-aware secure tracking prototype (9)

Run:
    python common.py task6
Inputs q6_tracking_scenarios.csv includes charging Wi-Fi, LTE moving, low battery stationary, low-power, no network, hot device and critical battery. Outputs: Q6_Tracking_Policy.csv, Q6_Hand_Validation.csv and Q6_Scalability.csv.

Policy dimensions: battery normal (>20), conserve (≤20), critical (≤10); network Wi-Fi/cellular/none; motion moving/stationary. Default balanced interval 60 s. Hot/critical: 300 s and defer normal upload. Low power: 120 s and upload in Wi-Fi/charging window. Moving: 15 s and batch upload. Charging+Wi-Fi: 10 s and upload batch. Security invariant: encrypt payload with AES-GCM before local queue (Keystore key assumed) and authenticated TLS for upload.

Architecture: UI main thread → pure domain policy evaluator → repository/encrypted queue → Android Location/SensorManager/WorkManager (foreground service only for visible continuous tracking) → server. Worker threads perform encryption, persistence and network; UI observes status.

Energy model in common.py: sample energy = 0.002 mAh × (600 / sampling interval seconds); radio batch overhead = 0.18 mAh for immediate/batch upload, 0.03 mAh for deferred Wi-Fi/charging opportunity, 0 for queue/no network. This is simplified comparative estimate, not device calibration. Replace constants with target-hardware measurements.

Hand validation: independently apply policy to three conditions and compare Q6_Hand_Validation.csv. Matching validates rule implementation, not physical energy accuracy.

Scalability: Q6_Scalability.csv counts policy evaluations per record and batch wakeups as ceil(records/20); memory estimate 0.65 KB/record. Batching reduces repeated radio promotion/tail energy but high-frequency GPS/sensor sampling still costs energy and creates records.

Emergency change: seconds-level delivery changes objective from battery efficiency to deadline/reliability. Investigate priority queue, emergency foreground tracking, high-priority push where justified, cellular upload and server fleet orchestration. Trade-offs: battery, heat, data cost, privacy exposure and server expense.

**Reflection (≤150 words):** A technique depends on workload and device state. The policy model selects long intervals and defers radio work for stationary low-battery conditions, while moving/emergency conditions need shorter intervals. Batching reduces repeated radio wakeups, but cannot remove location/sensor sampling cost. A permanent wakelock can defeat Doze and aggressive alarms can defeat batching. No single OS feature optimises every workload because latency, motion, battery, network, thermal state and user urgency change the correct decision. The model validates policy logic; profiler and Battery Historian measurements are still required for actual energy and responsiveness.
