# Mobile Computing Assignment — Answers Q1–Q7

This submission answers the seven questions in the supplied assignment. Numerical values below are outputs from the deterministic Python simulations; modelling assumptions are stated so the results are reproducible.

## Q1 — Mobile communication or mobile computing?
**Criteria:** (1) user/device mobility, (2) wired or wireless access, (3) tolerance of disconnection, (4) location/context dependence, (5) battery/compute/storage limits.
- (a) Cellular rugged tablet: **mobile**; both, mainly mobile computing because caching, retries and battery matter as well as handover.
- (b) Ethernet laptop moved between offices: **nomadic**; mainly mobile computing/session continuity, but not wireless and not moving during a session.
- (c) Fixed substation router: **fixed-wireless**; mainly communication/link planning, not mobile.
- (d) Push-to-talk handset: **mobile**; mainly mobile communication (coverage, handover, latency).
- (e) Offline meter-reading tablet: **mobile**; mainly mobile computing (local persistence, queueing, conflict resolution and delayed sync).
- Ambiguous case: Wi-Fi tablet inside a moving delivery van. The tablet is mobile relative to the network; router is fixed relative to the vehicle but the overall installation moves.
**Simulation:** 1,000 readings, link availability 90/60/30%, immediate attempt vs retry once per minute for 60 minutes, seed 42.
| Availability | Immediate delivered/lost | Store-forward delivered/lost | Mean store-forward delay |
|---|---:|---:|---:|
| 90% | 893 / 107 | 1000 / 0 | 1.107 min |
| 60% | 588 / 412 | 1000 / 0 | 1.622 min |
| 30% | 313 / 687 | 1000 / 0 | 3.514 min |
Wireless alone cannot provide offline storage, retry, deduplication or conflict resolution. Case (e) requires offline-first application design.

## Q2 — FDMA vs TDMA
2 MHz / 25 kHz = **80 FDMA channels**. TDMA: 2 MHz / 200 kHz = 10 carriers × 8 slots = **80 nominal slots**. Assumed overhead: FDMA 10% → 72 usable; TDMA 15% → 68 usable. Equal nominal capacity is not equal usable capacity.
Predictions: FDMA is simple for continuous voice; dynamic TDMA can reuse idle slots for bursty data; synchronized arrivals can cause blocking in either scheme. Dedicated channels waste capacity for 10%-duty-cycle data.
The simulation uses three generated workloads (continuous voice, bursty short data, synchronized short arrivals). For 1,200 continuous arrivals: FDMA accepts 72, TDMA 68; for bursty data: FDMA 265, TDMA 253. The synchronized edge workload accepts all 800 short bursts over its long observation horizon but utilization is below 0.5%. See `outputs/Q2_access_results.csv`.
Campus telemetry (90% of devices send 200 bytes/minute) should not receive one permanently dedicated channel per device; use pooled scheduled/random access and aggregation.

## Q3 — DS-CDMA
Each bit is multiplied by an L-chip spreading code; the receiver correlates with the intended code and decides from the sign. Processing gain is L: 8→9.03 dB, 16→12.04 dB, 64→18.06 dB. Synchronous Walsh codes have zero cross-correlation; random codes generally do not.
Prediction: synchronous equal-power Walsh users have very low BER; random codes create multi-user interference; a 10× interferer with a one-chip offset breaks orthogonality and can overwhelm the wanted user. The simulation uses 2,000 bits, lengths 8/16/64, Gaussian chip noise and fixed seed. At the largest tested user count, BERs for Walsh equal power were 0; random-code BER was 0.13 (L=8), 0.054 (L=16), and 0 (L=64); the 10× shifted interferer gave approximately 0.48–0.52 BER. The complete values and cross-correlations are in `outputs/Q3_BER.csv` and `outputs/Q3_Correlation.csv`.
Power control is essential because asynchronous timing, multipath and unequal received powers destroy practical orthogonality (near-far problem). With BER target ≤1%, all tested synchronous Walsh loads (up to 8 users) pass; the asynchronous near-far case does not.

## Q4 — OFDMA
Subcarrier spacing Δf = 1/Tu. The cyclic prefix copies the symbol tail to the front; if it exceeds significant channel delay spread it reduces inter-symbol interference and preserves orthogonality, at a CP overhead cost. Numerically checked complex subcarrier inner products (0,1), (0,7), (12,31): all 0 within numerical precision.
Eight users share 64 subcarriers; 1,000 fading realizations compare fixed contiguous, interleaved and channel-aware best-subcarrier allocation. Average sum-throughput proxy / Jain fairness: fixed 144.7600 / 1.0000; interleaved 145.1812 / 1.0000; channel-aware 248.7351 / 0.9997. Results: `outputs/Q4_OFDMA.csv`. A maximum-gain scheduler can starve persistently weak users; choose fairness-constrained channel-aware allocation with a guaranteed minimum rate and admission control.

## Q5 — SDMA
For a uniform linear array:
AF(θ) = (1/N) Σ(n=0…N−1) exp[j n(2πd/λ)(sinθ−sinθ0)].
With half-wavelength spacing, increasing N narrows the main lobe and improves angular discrimination; uniform weighting still has sidelobes. Simulation uses N=2,4,8,16, broadside steering and 10 dB SIR threshold. Minimum tested separation meeting threshold: N=2:55°, N=4:25°, N=8:15°, N=16:10°. Pattern points and SIR are in `outputs/Q5_Patterns.csv` and `outputs/Q5_SIR.csv`. At a toll plaza, vehicles clustered in the same direction cannot reliably be separated by SDMA alone; combine sectors with time/frequency scheduling.

## Q6 — Access-technique selection
Weighted criteria: capacity 0.22, burst efficiency 0.20, interference resistance 0.18, mobility 0.16, simplicity 0.10, fairness/QoS 0.14. Ratings are explicit engineering judgements (1–5) informed by Q2–Q5, not universal constants.
Recommended primary methods: cellular voice—OFDMA (with SDMA beams); jam-resistant tactical link—CDMA (plus frequency agility); stadium high-rate downlink—OFDMA + SDMA; 5,000 low-rate sensors—pooled/scheduled access, with CDMA as the weighted-matrix winner under the declared ratings. ±20% one-at-a-time weight changes leave the four matrix winners unchanged in this test. Real systems combine techniques because frequency, time, code, subcarrier and spatial separation solve different resource problems.

## Q7 — Diagnose, redesign and validate
Chosen limitation: static dedicated channels waste resources for brief, low-rate sensor reports. Objective: maximize delivered reports/minute with 80 parallel channels. Redesign: buffer reports, request short transmission opportunities, schedule up to 80 per second, queue excess and retry in later idle seconds.
With 5,000 sensors, 200 bytes/minute and randomized phases, the constrained static baseline serves 80 reports (1.60%); pooled on-demand scheduling serves 4,477 (89.54%), leaving 523 queued after the retry pass. This is 55.96× more reports served in the simplified model. Costs: request/grant signalling, queue memory, delay and possible unfairness. Static reservation can remain preferable for constant-rate latency-critical flows.
