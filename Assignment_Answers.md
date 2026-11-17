# ASSIGNMENT 1 – FREQUENCY PLANNING FOR A CELLULAR TOWNSHIP
## Question-wise answers (Q1–Q12)

### Common assumptions and notation
The brief gives the service area (12 km²), subscriber range and the event-day surge, but does not give a measured traffic map, licensed channel count, per-subscriber busy-hour traffic, cell radius, antenna patterns or propagation survey. Therefore, the implementation uses explicit illustrative assumptions: total channel equivalents \(S=420\), nominal cell radius \(R=0.5\) km, busy-hour traffic \(a_u=0.02\) Erlang/subscriber, target blocking \(B=0.02\), service area \(A_T=12\) km², and seed 197226. These values are replaceable inputs, not measured network facts. Erlang-B assumes Poisson call arrivals, exponential holding times, loss system/no queue and independent channels.

Notation: \(N\)=reuse-cluster size; \(D\)=co-channel reuse distance; \(Q=D/R\); \(n\)=path-loss exponent; \(S\)=total channels; \(C\)=channels/cell; \(A_h\)=hexagonal cell area.

---

## Q1. Design alternative frequency-planning strategies (5 marks)

**Strategy 1 – Fixed frequency reuse (iterative spatial reuse).** Divide the available spectrum into \(N\) disjoint channel groups and repeat the pattern over a hexagonal grid. Valid ideal hexagonal cluster sizes are \(N=i^2+ij+j^2\), for non-negative integers \(i,j\); examples include 3, 4, 7, 9 and 12. The reuse distance is \(D=R\sqrt{3N}\). Each cell receives approximately \(S/N\) channels. Control channels are reserved consistently in each group; remaining traffic channels carry user sessions. FDMA assigns distinct carrier channels; TDMA can subdivide a carrier into time slots; CDMA/OFDMA would instead use codes/subcarriers and require an interference/load plan.

Pseudocode:
```
for each candidate N in valid_hex_cluster_sizes:
    compute D = R * sqrt(3*N)
    build hexagonal cell grid
    create co-channel conflict edges for separation < D
    greedily assign one of N frequency groups per cell
    estimate capacity and first-tier SIR
select N meeting SIR and blocking targets at lowest cost
```
Principle: **spatial reuse**. Assumptions: regular hexagonal coverage, approximately uniform traffic and fixed channel demand. Preprocessing: traffic map, propagation survey, terrain/building data, hex-grid and candidate-site plan. Network operator/planner bears most survey and planning cost; regulator supplies spectrum constraints. This is the baseline because it is simple, predictable and easy to audit.

**Strategy 2 – 120-degree sectorized reuse (spatial filtering).** Split each base-station coverage area into three directional sectors using directional antennas. The same site has three sector antenna patterns; the number of strong first-tier interferers seen by a sector can fall from about six to about two in an idealized 120° model. The frequency plan can retain a reuse cluster while assigning channel subsets to sectors according to the antenna plan. Control channels must remain reachable across sectors; traffic channels are allocated per sector. FDMA/TDMA channel groups are natural; OFDMA can schedule resource blocks by sector.

Pseudocode:
```
for each site:
    install/plan 3 antennas with 120-degree azimuth separation
    partition traffic channels among sectors
    assign reuse groups to sectors with adjacent-sector checks
    evaluate antenna-pattern overlap and SIR
    rebalance sector channel pools if one sector is overloaded
```
Principle: **spatial filtering**. Assumptions: directional patterns and correct antenna orientation; real side lobes and downtilt are not ideal. Preprocessing: azimuth/tilt survey, traffic-by-direction map and propagation prediction. Operator bears antenna/site optimization cost. Investigate because it can improve SIR without acquiring more spectrum, although it adds hardware and uneven-sector blocking risk.

**Strategy 3 – Dynamic channel assignment / channel borrowing (trunking).** Keep a common or semi-common channel pool. A cell requests a channel when a call arrives; the controller selects a channel that is not active in a nearby interfering cell. If the local pool is exhausted, a channel may be borrowed from a lightly loaded neighbor only if the reuse/interference constraint remains satisfied. Control channels carry requests, measurements and handoff signalling; traffic channels carry calls/data. This can be implemented with FDMA/TDMA channels or OFDMA resource blocks.

Pseudocode:
```
on call request in cell c:
    form candidate channels = free channels in local + borrowable pools
    remove candidates active in interfering neighbor cells
    rank remaining candidates by interference and reuse cost
    if a candidate exists: assign it and update occupancy
    else: block the request
on call release or handoff: return/update the channel pool
```
Principle: **trunking and adaptive interference avoidance**. Assumptions: a controller has timely occupancy/interference information and signaling is reliable. Preprocessing: busy-hour traffic matrix, neighbor graph, interference measurements and handoff routes. Operator bears measurement, controller and backhaul cost. Investigate because statistical pooling can reduce blocking under nonuniform and time-varying demand.

**Strategy 4 – Hierarchical macro–micro layering (recursive cell splitting).** Macrocells provide broad-area coverage and mobility continuity. In hotspots, microcells/picocells are inserted; overloaded cells are recursively split, reducing radius from \(R\) to \(R/2\) per round. Smaller cells reuse spectrum more frequently and lower required transmit power, but create more sites and handoffs. Macro layer can retain robust control/coverage; small cells carry localized traffic. OFDMA/TDMA scheduling can coordinate layers; separate carriers or coordinated resource blocks reduce cross-layer interference.

Pseudocode:
```
plan macro layer over township
while predicted local load > per-cell target:
    choose overloaded hotspot cells
    split each selected cell into 4 child cells of radius R/2
    assign channels subject to macro/micro interference constraints
    reduce power and update neighbor/handoff graph
    stop when load target met or cost/site limit reached
```
Principle: **recursive spatial reuse**. Assumptions: suitable sites/backhaul/power exist and handoffs can be coordinated. Preprocessing: high-resolution traffic map, candidate micro-site survey, propagation/indoor survey and mobility routes. Operator bears the incremental site, backhaul and optimization cost. Investigate because capacity can be concentrated where demand occurs instead of permanently overbuilding the whole township.

---

## Q2. Governing design parameters (2 marks)

| Strategy | Dominant parameter | Why it governs the design |
|---|---|---|
| Fixed reuse | Cluster size \(N\), equivalently \(Q=\sqrt{3N}\) | Channels/cell are approximately \(S/N\), while reuse distance and SIR rise with \(N\). |
| Sectoring | Effective first-tier interferer count \(i_0\) and antenna discrimination | Fewer strong interferers improve SIR; sector traffic imbalance controls blocking. |
| Dynamic assignment | Number of simultaneously available non-conflicting channels \(C_{\rm free}\) | Determines whether a request can be admitted; pooling changes trunking efficiency. |
| Hierarchical splitting | Cell radius \(R_k\) (or split round \(k\)) | Cell density scales as \(1/R_k^2\), local capacity per area rises, and handoff rate rises as cells shrink. |

For a fixed channel pool, increasing \(N\) improves isolation but reduces channels per cell. When subscribers rise from 1,000 to 100,000+, the planner should not simply increase \(N\) indefinitely: it should use measured hotspot loads, dynamic pooling, sectorization and localized splitting. The dominant variable is therefore linked to each strategy's actual capacity/interference mechanism.

---

## Q3. Capacity and interference functions (6 marks)

**1. Hexagonal geometry and reuse.** A regular hexagon of circumradius \(R\) is six equilateral triangles of side \(R\):
\[
A_h=6\left(\frac{\sqrt3}{4}R^2\right)=\frac{3\sqrt3}{2}R^2.
\]
For 12 km², the ideal cell count is
\[
M_{\rm ideal}=\frac{12}{A_h}.
\]
At \(R=0.5\) km, \(A_h=0.6495\) km² and \(M_{\rm ideal}=18.48\), so at least 19 ideal cells are needed before overlap, edge and capacity margins. The simulator uses a finite hex-centre layout for geometry checks and this area ratio for capacity estimates.

Moving \(i\) cells along one lattice axis and \(j\) along the 60° axis gives squared centre displacement
\[
D^2=3R^2(i^2+ij+j^2),\quad N=i^2+ij+j^2.
\]
Thus \(D=R\sqrt{3N}\) and \(Q=D/R=\sqrt{3N}\). For \(N=7\), \(Q=\sqrt{21}=4.583\).

**2. Channels and Erlang-B.** With \(S=420\), channels/cell are approximately \(C=\lfloor S/N\rfloor\). At \(N=7\), \(C=60\). For offered traffic \(A\) Erlangs and \(C\) circuits:
\[
B(0,A)=1,\quad B(C,A)=\frac{A B(C-1,A)}{C+A B(C-1,A)}.
\]
Find the largest \(A_c\) satisfying \(B(C,A_c)\le0.02\) by numerical bisection. Total carried design capacity is approximately \(M A_c\), with \(M\approx12/A_h\). Actual busy-hour demand is \(A_{\rm demand}=0.02U\), where \(U\) is subscriber count under the stated traffic assumption. This makes blocking a per-cell as well as a system-wide load-balancing issue.

**3. Co-channel SIR.** With path loss \(P_r\propto d^{-n}\), desired distance \(r\), and first-tier interferers at distances \(d_m\):
\[
\mathrm{SIR}=\frac{r^{-n}}{\sum_{m=1}^{i_0}d_m^{-n}}.
\]
If the \(i_0\) interferers are approximated as equidistant at \(D\), then
\[
\mathrm{SIR}\approx\frac{(D/r)^n}{i_0}.
\]
At the cell edge \(r=R\), \(D/R=\sqrt{3N}\), so
\[
\mathrm{SIR}_{dB}\approx10\log_{10}\left(\frac{(3N)^{n/2}}{i_0}\right).
\]
For \(N=7,n=4,i_0=6\): \(10\log_{10}(21^2/6)=18.67\) dB, matching the assignment's sanity-check value. For ideal 120° sectoring with two dominant interferers, replace \(i_0=6\) by \(2\), yielding \(23.44\) dB in this simplified model. Actual antenna side lobes, user position and unequal distances change the result.

**4. Strategy-specific functions.**
- Fixed reuse: \(C_{\rm cell}\approx S/N\), \(D=R\sqrt{3N}\), and the above six-interferer SIR approximation.
- Sectoring: same total licensed channel count, divided among three sectors; \(i_0\) can approach 2 ideally, but each sector has fewer circuits and traffic can be unbalanced.
- Dynamic assignment: instantaneous \(C_{\rm free}\) depends on the local pool and neighbor occupancy. Pooling reduces blocking relative to isolated fixed pools when loads are uneven; the exact gain must be measured by a controller-level simulation.
- Hierarchical: at split round \(k\), \(R_k=R/2^k\), cell density grows by \(4^k\), and site count in a fixed area grows approximately by \(4^k\). Reuse distance shrinks in proportion to radius if the same \(N\) is retained.

**5. Planning cost versus capacity.** Let \(c_s\) be one-time survey/planning cost per township, \(c_{\rm site}\) site deployment cost, \(c_{\rm sec}\) sector upgrade cost/site, and \(c_{\rm ctrl}\) dynamic controller cost. A transparent lifecycle proxy is
\[
K_{\rm fixed}=c_s+M c_{\rm site},\quad
K_{\rm sector}=c_s+M(c_{\rm site}+c_{\rm sec}),
\]
\[
K_{\rm dynamic}=c_s+M c_{\rm site}+c_{\rm ctrl},\quad
K_{\rm split}(k)=c_s+M4^k c_{\rm site}+c_{\rm coord}(k).
\]
Cost per supported Erlang is \(K/C_{\rm total}\). This expresses the trade-off: increasing \(N\) reduces capacity per cell; sectoring spends hardware to improve isolation; dynamic assignment spends control complexity to improve pooling; splitting spends sites/backhaul to localize capacity. Monetary values are intentionally not fabricated because no local cost schedule was supplied.

---

## Q4. Best, average and worst-case behaviour (4 marks)

**SIR by mobile position.** With \(P_r\propto d^{-n}\), the desired signal grows sharply as the mobile approaches the serving base station. At the ideal cell centre, desired distance is small and SIR is best; at a representative mid-cell distance it is lower; near the cell edge/corner, the serving distance is largest and several first-tier interferers may be geometrically close, so SIR is worst. In a hexagonal grid, corners are especially sensitive because neighboring cells are not all at the same distance. Sectoring improves the directional case when the serving antenna points toward the mobile and suppresses off-axis interferers; sector boundaries can be worse because two sectors may have similar received power. Dynamic assignment can avoid a currently active co-channel neighbor but cannot remove propagation loss or all interference.

A numerical illustration uses \(N=7,n=4\): the equal-distance cell-edge approximation is 18.67 dB for six interferers and 23.44 dB for two dominant sector interferers. At a mobile distance \(r=R/2\), the same approximation adds \(10n\log_{10}(R/(R/2))=12.04\) dB, giving 30.71 dB and 35.48 dB respectively. These are idealized geometry calculations, not measured percentile values.

**Blocking by time.** Off-peak traffic gives low offered load \(A\) and low Erlang-B blocking. Average traffic gives intermediate blocking. Busy-hour load approaches the 2% design point. An event surge can exceed the circuit pool and cause high blocking even if average-day performance is good. For illustration, with 60 circuits, evaluate \(B(60,A)\) using the recurrence in the code; blocking rises nonlinearly as \(A\) approaches/exceeds the carried-traffic limit.

**Shadowing and path-loss exponent.** Lognormal shadowing adds a random dB term to received powers; it broadens the SIR distribution, increasing the probability of unusually weak desired signal or strong interferer. A larger \(n\) makes distant interferers decay faster and generally improves reuse SIR, but also makes coverage more sensitive to distance and obstacles. The simulator sweeps \(n=2.5,3,4\) and includes an optional shadowing standard deviation. Best/average/worst must therefore be interpreted as distributions, not one deterministic value.

---

## Q5. Scaling and sensitivity analysis (3 marks)

For fixed reuse, channels/cell scale approximately as \(S/N\), so per-cell circuit capacity is reduced as \(N\) grows. Under the equal-distance model, SIR scales as \(N^{n/2}/i_0\). Number of cells in a fixed area scales as \(1/R^2\). If radius is halved, approximately four times as many cells are required. For \(n=2.5,3,4\), SIR's dependence on \(N\) becomes progressively stronger: \(N^{1.25}\), \(N^{1.5}\), and \(N^2\), respectively, before accounting for antenna and shadowing effects.

Demand under the assumed 0.02 Erlang/subscriber is 20 E at 1,000 users, 200 E at 10,000, 400 E at 20,000 and 2,000 E at 100,000. The network must scale both total circuits and spatial distribution; a single larger cluster cannot solve localized overload efficiently. Fixed reuse is practical for stable uniform demand; sectoring is useful where interference limits capacity; dynamic assignment is attractive with uneven demand; microcells become preferable when hotspots persist and site/backhaul cost is justified. A useful break-even rule is to split a hotspot when the cost of additional micro-sites is lower than the cost of permanent over-provisioning or the revenue/service loss from blocking. The numeric threshold requires local site and traffic costs, which were not provided.

---

## Q6. Recurrence for repeated cell splitting (3 marks)

Let \(M_0\) be initial cell count, \(R_0\) initial radius and \(C_0\) carried capacity per cell at the target blocking. A four-way split replaces one parent with four children, so it adds three net cells. Under uniform splitting:
\[
M_k=4M_{k-1},\quad R_k=R_{k-1}/2,\quad
P_k=P_{k-1}/2^n.
\]
If per-cell channel resources are reused and each child can support approximately \(C_0\), aggregate capacity follows \(C_k=4C_{k-1}\). Total transmit power per child follows the stated path-loss scaling \(P_k=P_0/2^{nk}\); this is an idealized link-budget relation and real power depends on coverage and antenna gains.

For selective splitting, let \(f_k\) be the fraction of cells split in round \(k\):
\[
M_k=M_{k-1}(1+3f_k),\quad
R_{\rm split}=R_{k-1}/2,\quad
C_k=C_{k-1}(1+3f_k)
\]
under equal-load/equal-capacity assumptions. If \(f_k=1\), this reduces to uniform splitting. Handoff load rises as cell boundaries become more numerous; a first-order proxy is proportional to \(1/R_k\), hence approximately doubles per uniform round. Base case: \(M_0\) cells, radius \(R_0=0.5\) km, initial traffic demand \(D_0\), and capacity \(C_0\) per cell. Work/cost per round is proportional to the number of sites added, \(3f_kM_{k-1}\), plus survey, backhaul and coordination.

---

## Q7. Solve the recurrence and interpret (4 marks)

For uniform splitting, \(C_k=4C_{k-1}\). Repeated substitution gives
\[
C_1=4C_0,\ C_2=4(4C_0)=4^2C_0,\ldots,\ C_k=4^kC_0.
\]
Demand \(D\) is supportable when \(4^kC_0\ge D\), hence
\[
k\ge\log_4(D/C_0),\qquad
k_{\min}=\left\lceil\log_4(D/C_0)\right\rceil
\]
for \(D>C_0\); otherwise \(k=0\). The method is valid because the same multiplicative capacity factor is applied each round.

For selective splitting, with constant fraction \(f\):
\[
C_k=C_0(1+3f)^k,\quad
k_{\min}=\left\lceil\frac{\log(D/C_0)}{\log(1+3f)}\right\rceil.
\]
If fractions vary by round, \(C_k=C_0\prod_{t=1}^k(1+3f_t)\), and the minimum \(k\) is the first round for which this product reaches \(D/C_0\).

Uniform splitting multiplies site count by \(4^k\), radius falls to \(R_0/2^k\), and ideal transmit power per child falls to \(P_0/2^{nk}\). At the same time, handoff frequency and backhaul coordination increase. Selective splitting limits cost by targeting only overloaded cells. The recurrence is a capacity abstraction; real child-cell capacity may be lower due to finite spectrum, interference, indoor penetration and uneven traffic.

---

## Q8. Implement and test planning strategies (4 marks)

The Python implementation is in `src/planner.py`. It includes:
- hexagonal area and axial-grid generation;
- valid cluster-size generation using \(i^2+ij+j^2\);
- greedy conflict-graph channel-group assignment;
- Erlang-B recursion and numerical inversion for 2% blocking;
- Monte-Carlo first-tier SIR with six-interferer and ideal two-interferer sector cases;
- parameter sweeps for \(N=3,4,7,12\), \(n=2.5,3,4\), sectorized/unsectorized cases;
- demand sizes 1,000, 10,000, 20,000 and 100,000 with a fixed random seed;
- event surge calculation and generated tables/plots.

Run:
```
python src/planner.py --self-test
python src/planner.py --out results
```
Sanity check: \(N=7,n=4\) gives \(10\log_{10}(441/6)=18.67\) dB, approximately 18.7 dB. The simulator's Monte-Carlo output is position-dependent and is not expected to equal this cell-edge/equidistant approximation exactly. Test cases check geometry, valid N values, Erlang-B bounds, capacity inversion and finite SIR values.

---

## Q9. Experimental performance (3 marks)

The program records:
- `sir_experiments.csv`: mean SIR, fifth-percentile SIR and outage probability for the specified N, n and sectoring sweeps;
- `capacity_experiments.csv`: channels/cell, Erlang capacity, cell count, offered traffic and blocking for each subscriber scale;
- `event_surge.json`: event traffic density and idealized temporary-cell lower bound;
- `sir_cdf.png`, `blocking_vs_load.png`, `capacity_vs_N.png`: comparison plots.

Mean SIR describes typical radio conditions; fifth-percentile SIR exposes cell-edge risk; outage probability exposes the fraction below a chosen threshold; blocking probability describes admission failure; sites and run-time expose cost and computational burden. Compare strategies at the same seed, offered traffic, path-loss exponent and channel pool. The SIR CDF plot is an illustrative normal approximation based on the Monte-Carlo summary; the CSV mean and fifth percentile are the direct Monte-Carlo statistics.

---

## Q10. Theory versus simulation (4 marks)

The analytical \(N=7,n=4\) result (18.67 dB) assumes a cell-edge mobile and six equal-distance first-tier interferers. The Monte-Carlo model samples mobile locations across the cell and uses actual unequal distances, so its mean and fifth percentile need not equal 18.67 dB. Sectoring's analytical improvement from 18.67 to 23.44 dB assumes exactly two dominant interferers and ideal antenna rejection; real side lobes and sector-edge users reduce the gain.

Erlang-B theory assumes Poisson arrivals, exponential holding times, an infinite source population and a fixed number of circuits. Real subscriber arrivals may be correlated, calls may be handed off, and dynamic assignment may borrow channels. Differences also arise from finite network edges, rounded channel counts, irregular terrain, shadowing, unequal cell loads and omitted adjacent-channel interference. Therefore the model is best used for comparative planning and sensitivity, not a guaranteed field prediction. Under uniform load, fixed reuse is easiest to validate; under uneven traffic, dynamic assignment and localized microcells can use resources more efficiently. The final choice must be based on the actual traffic map and measured SIR/blocking.

---

## Q11. Recommend and defend the final design (4 marks)

**Recommendation: a hybrid design** – retain a macrocell fixed-reuse layer for continuous township coverage, apply 120° sectoring at high-interference/high-load macro sites, use dynamic channel assignment or coordinated resource-block scheduling for short-term imbalance, and selectively add microcells only in persistent hotspots. Use \(N=7\) as a conservative starting reuse plan, \(R=0.5\) km as the initial planning radius, and three 120° sectors at selected high-load sites. Validate \(N\), radius and sector azimuths using a real propagation survey before deployment.

Why this is preferable: fixed reuse gives a stable baseline; sectoring reduces dominant co-channel interference; dynamic assignment helps uneven traffic without permanently reserving all capacity in every cell; selective splitting adds capacity where needed without multiplying all township sites. At \(N=7\), the idealized six-interferer cell-edge SIR is 18.67 dB, while the ideal two-interferer sector approximation is 23.44 dB. Capacity and blocking are calculated from 60 channels/cell using Erlang-B at 2%; exact expected township capacity is printed in the generated results. The cost trade-off is additional antenna/controller/site expense against reduced interference and blocking. Beyond 100,000 subscribers, reassess with measured busy-hour and indoor/event loads; the hybrid remains a scalable framework, but the specific 420-channel assumption may no longer be adequate. No unconditional guarantee is possible without licensed spectrum, propagation and cost data.

---

## Q12. Day-4 design challenge: event surge (8 marks)

### A. Impact analysis (2 marks)
Event traffic is
\[
A_e=25,000(0.05)=1,250\text{ Erlangs}.
\]
For a 1 km² stadium zone, the event density is 1,250 E/km². At the illustrative 100,000-subscriber township forecast, baseline traffic is \(100,000(0.02)=2,000\) E over 12 km², or 166.7 E/km² if uniform. The event-zone traffic density is therefore 7.5 times this township-average density. The event lasts four hours and occurs about twice monthly; uniform traffic, steady demand and permanent-capacity assumptions are invalid for the stadium zone. Predictability and short duration make temporary capacity more economical than permanently provisioning the whole network for the peak.

### B. Original design on event day (2 marks)
The original \(N=7\) fixed-reuse design has 60 channels/cell under \(S=420\). Its 2%-blocking capacity per cell is obtained by inverting Erlang-B in the program. The theoretical ideal lower bound on temporary cells is \(\lceil1,250/A_c\rceil\), where \(A_c\) is that per-cell capacity; actual requirement is higher after reserve channels, interference, nonuniform attendance, uplink limits and handoff margins. If the stadium is covered by only one or a few macro sectors, offered traffic will exceed the circuit pool and blocking rises sharply. Co-channel interference also worsens if channels are reused aggressively without coordinated antenna and power planning. The unchanged design is therefore not recommended for the event peak.

### C. Adaptation/redesign (2 marks)
**Modify temporarily, not permanently:** deploy a small-cell cluster or cells-on-wheels (COWs) around the stadium for the four-hour peak; use directional 60°/120° sectors where traffic is concentrated; activate dynamic channel borrowing and coordinated scheduling; retain macro layer for coverage and mobility. Use low transmit power and a locally planned reuse pattern; coordinate macro/micro channels or resource blocks to limit cross-tier interference. Provide additional backhaul and power. A practical deployment count should be set from measured Erlang-B capacity per temporary cell plus a safety margin, not from the ideal lower bound alone. This adds capacity mainly in the 1 km² event zone; SIR can be maintained by directional antennas, power control and coordination, at the cost of temporary equipment, transport and setup.

### D. Evidence-based defence (2 marks)
Two events/month and four hours/event represent about eight peak hours/month. A temporary COW/small-cell solution incurs recurring deployment and operating cost only on event days, while permanent stadium microcells incur ongoing rental, power, maintenance and backhaul cost. The correct economic choice compares monthly temporary cost with annualized permanent-site cost and the cost of lost calls/service during blocking. The event traffic is 1,250 E concentrated in 1 km², so doing nothing is not defensible; permanently splitting the entire township is also inefficient. A temporary localized overlay is the best initial choice, with permanent microcells justified only if post-event measurements show frequent non-event congestion. Final channel counts, SIR and blocking must be verified with the real channel plan, antenna patterns, event arrival profile and field measurements.

---

## Conclusion
A fixed reuse plan establishes predictable spectrum sharing, but no single method solves every load pattern. Sectoring improves spatial isolation, dynamic assignment improves statistical pooling, and hierarchical splitting localizes capacity. The defensible township design is a measured, hybrid macro layer with targeted sectoring and dynamic allocation, plus temporary stadium capacity for the predictable event surge. The attached simulator makes the stated assumptions and comparisons reproducible; its outputs are planning estimates rather than a substitute for a propagation survey.
