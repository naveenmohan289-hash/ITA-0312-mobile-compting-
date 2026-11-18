# Android Kotlin reference source

These are modular source files to integrate into a disposable Android test application. They are not a complete Gradle project and have not been compiled against a specific Android SDK in this repository.

- ThreadingBenchmark.kt: same deterministic workload on main thread and fixed executor; capture frame stats/Perfetto. The main-thread version is intentionally blocking and should be run only with bounded test input.
- RuntimeWorkloads.kt: CPU/allocation/list workloads and test-only leak/ANR triggers. Clear the leak after the experiment; never ship test triggers.
- TrackingPowerPolicy.kt: pure deterministic battery/network/motion policy used as the domain layer. Add unit tests for every boundary.

Keep UI, domain policy and repository/storage separate. Use Android Keystore for production encryption; these snippets do not implement cryptographic storage or a complete app.