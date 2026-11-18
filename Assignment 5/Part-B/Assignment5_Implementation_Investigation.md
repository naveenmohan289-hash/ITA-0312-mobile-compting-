# PART B — IMPLEMENTATION & COMPUTATIONAL INVESTIGATION (25 MARKS)

The shared implementation is `code/common.py`. Run all experiments with `python "Assignment 5/code/common.py" all`; each task also accepts b1, b2, b3 or b4. The script writes CSV evidence to `outputs/`.

# TASK B1 — Instrumented Background Work (7)
**Implementation:** deterministic WorkManager-style queue model. Metrics: enqueued, deferred, cancelled, successful, attempts, peak workers and residual backlog. Per-decision trace records job ID, priority, reason, battery, network and Doze. Single worker is explicit (peak concurrency 1 when jobs exist).

**Validation scenarios:**
1. Good connectivity/battery: 88% battery, good network, Doze off, permission valid. Eligible encrypted jobs execute; sensitive plaintext is rejected.
2. Doze/low battery: 12% battery and Doze on. Routine jobs defer; critical status does not bypass privacy or permission checks.
3. Permission revoked boundary: permission false at decision time; work cancels without upload. Real Android code must re-check permission immediately before protected sensor access and sending.

**B1.2 comparison:** design pseudocode is asynchronous and event-driven; simulation uses finite lists and scenario snapshots for reproducibility. A production worker must re-read mutable constraints at execution time and handle platform cancellation callbacks.

**B1.3 scheduling:** Version 1 FIFO sorts by arrival. Version 2 priority heuristic sorts descending priority, then arrival. Priority cannot override feasibility/security. The model has one worker.

**B1.4 effect:** inspect B1 CSVs. Static scenario snapshots mean both strategies have identical feasibility totals; priority changes order only. It may improve critical delivery when deadlines, limited slots or changing resources interact, but this simulation does not claim that effect.

# TASK B2 — Adversarial Workload (5)
Two six-record workloads use the same constraints. Workload A mostly has low battery thresholds, encrypted data and metered permission: predict few deferrals. Workload B has high battery thresholds, metered disallowance and sensitive plaintext: predict more deferrals and security cancellations. Compare processed attempts, deferrals and successes in B2 CSVs.

Input size alone is inadequate: encryption readiness, priority, minimum battery, metered permission, retry count, payload size, radio wake-ups and conflicts affect work/energy. Workload B's structure creates repeated infeasibility despite equal record count.

# TASK B3 — Exact vs Approximate Feed Optimisation (8)
**Exact:** enumerate every quality/cache pair and minimise documented cost; operation count is product of candidate counts. Exactness is only relative to the simplified model and finite grid.

**Approximate:** start at quality 3/cache 3; lower quality when frame penalty exceeds target, then reduce cache/prefetch pressure under battery/frame constraints; stop at steady state or 12 iterations. Records iterations, quality changes and evictions.

B3.1/B3.2: three cases in `data/b3_feed_cases.json`; compare exact/approximate costs and match flag in `B3_Correctness_and_Counterexamples.csv`. Third case is a low-battery challenge. B3.3: 8, 40, 120 items and increasing candidate dimensions; compare configuration evaluations with bounded adaptive operations in `B3_Scalability.csv`. B3.4: approximate gains bounded decision effort/live responsiveness, sacrifices global optimality. Accept it for live scrolling where an optimisation pause is worse than a small quality compromise; use exact search offline for small tuning spaces.

# TASK B4 — Multimedia Decision (5)
Greedy rule tries 720p, 480p, then 360p and selects the first candidate fitting model upload-time and battery-energy guardrails. Metered network schedules rather than immediately uploads. CSV includes resolution, bitrate, estimated upload seconds, energy and remaining battery.

Challenge profile uses low CPU/bandwidth; fixed estimates can mis-rank candidates because they omit codec hardware acceleration, thermal throttling and changing radio conditions.

**Production decision note:** exhaustive search over resolution × bitrate × codec × frame rate × device × network is too expensive per clip/user. The heuristic guarantees only first candidate meeting stated model guardrails, not globally minimum energy or best perceptual quality. It provides bounded candidate checks and quick response. Exact/cloud-assisted tuning suits offline device labs, small candidate sets or optional server transcoding after consent; capture must work offline. Monitor p50/p95 upload latency, retries, battery delta, thermal state, dropped frames, encoding duration, downgrade rate, data use, failures, crashes/ANRs and privacy incidents.

**Evidence warning:** generated CSV values are deterministic teaching-model estimates, not real phone/network measurements. Physical-device profiler evidence is required before deployment.
