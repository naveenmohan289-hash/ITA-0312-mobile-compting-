# PART A — DESIGN, ANALYSIS & ARCHITECTURAL REASONING (25 MARKS)

# TASK A1 — Constraint-Aware Intent & Service Architecture (7)

## A1.1 Problem model
**Inputs:** timestamped sensor events; network state (none/metered/unmetered); battery percentage; Doze state; user preferences; runtime permission and consent; encryption/key status; logout event.

**Outputs:** authenticated encrypted records accepted by backend; privacy-minimised critical-event notification; durable backlog status.

**Stage decisions:** validate permission/consent; validate and encrypt reading; persist; classify urgency; select an execution component; upload/defer/reject; acknowledge and advance local cursor only after server acknowledgement.

**Constraints:** battery threshold, Doze/background quota, network and metered-data policy, sensor/runtime permission, consent, encryption at rest/in transit, least-privilege component exposure, logout and user responsiveness.

**Goal:** every permitted record is either acknowledged remotely or remains safely encrypted in a durable local backlog. No sensitive plaintext is exposed and no blocking sensor/network work occurs on the UI thread.

## A1.2 Runtime state
Maintain job ID, event timestamp, encrypted payload reference, sensitivity, priority/critical flag, retry count, idempotency key, and state (NEW, VALIDATED, PERSISTED, QUEUED, RUNNING, WAITING_NETWORK, ACKNOWLEDGED, FAILED, CANCELLED). Also maintain permission/consent generation, key availability, battery, Doze, network type, metered preference, worker lease/attempt ID, next eligible time, acknowledgement token, notification status and logout tombstone. Persist state transactionally before scheduling; recover queued/waiting jobs after process restart.

## A1.3 Feasibility / pruning
- **Reject** if payload integrity fails or sensitive data is not encrypted.
- **Cancel** if logout/consent revocation invalidates the job, or required permission is revoked before protected access.
- **Defer** if network is unavailable, metered policy forbids it, Doze/quota blocks routine work, battery is below the job threshold, or a key service is temporarily unavailable.
- **Execute** only when permission, consent, encryption, required network and platform/battery constraints pass.
- Critical notification may use an allowed user-visible path, but never bypass privacy, permission or encryption checks.
- Retry transient failures with bounded exponential backoff and stable idempotency key. Do not retry permanent authorization/schema failures.
- Delete a record only after authenticated server acknowledgement or explicit lawful user deletion. Deferral never destroys data.

## A1.4 Complete architectural pseudocode
```text
PROCEDURE SCHEDULE_OR_EXECUTE(job_store, runtime)
  WHILE application_active OR durable_jobs_exist
    event ← WAIT(sensor_event, network_change, battery_change,
                 doze_change, permission_change, logout, worker_result)

    IF event = sensor_event THEN
      IF permission AND consent are valid THEN
        record ← VALIDATE_AND_ENCRYPT(event.payload)
        IF integrity_valid(record) AND encrypted(record) THEN
          ATOMICALLY PERSIST(record, PERSISTED, idempotency_key)
          ENQUEUE(record.id, UPLOAD_WORKER, network_constraint, battery_policy)
        ELSE REJECT_AND_AUDIT(event, "invalid_or_unprotected")
        ENDIF
      ELSE REJECT_AND_AUDIT(event, "permission_or_consent_missing")
      ENDIF
    ENDIF

    IF event is critical THEN
      IF permission AND consent AND encryption valid THEN
        SEND explicit internal Intent containing opaque event_id only
        POST privacy_minimised notification
      ENDIF
    ENDIF

    candidates ← SELECT QUEUED or WAITING_NETWORK jobs
    ORDER candidates by criticality DESC, priority DESC, age ASC
    FOR EACH job IN candidates
      snapshot ← READ_CURRENT battery, Doze, network, permission,
                 consent, key_status, logout_generation
      component ← WorkManager worker for deferrable work;
                  foreground service only for permitted ongoing
                  user-visible activity
      intent ← explicit internal Intent with job_id only
      IF logout_generation changed OR consent revoked THEN
        CANCEL job; erase transient plaintext; write tombstone; CONTINUE
      ENDIF
      IF permission absent OR integrity invalid THEN
        REJECT/CANCEL and audit; CONTINUE
      ENDIF
      IF sensitive(job) AND NOT encrypted(job) THEN
        REJECT; never export payload in an Intent; CONTINUE
      ENDIF
      IF network absent OR metered policy forbids THEN
        SET WAITING_NETWORK; DEFER with connectivity constraint; CONTINUE
      ENDIF
      IF Doze blocks job OR battery < job.minimum_battery THEN
        SET QUEUED; DEFER with constraints and backoff; CONTINUE
      ENDIF

      START_OR_ENQUEUE(component, intent)
      SET RUNNING; acquire bounded worker lease
      result ← EXECUTE idempotent encrypted upload
      IF authenticated_server_ACK(result) THEN
        ATOMICALLY SET ACKNOWLEDGED and save ack token
        remove local payload according to retention policy
      ELSE IF transient_failure(result) THEN
        SET WAITING_NETWORK; increment retry; release lease
        schedule bounded exponential backoff
      ELSE
        SET FAILED; release lease; record privacy-safe diagnostic
      ENDIF
    ENDFOR

    IF logout event THEN
      increment logout_generation
      CANCEL user-scoped workers and pending notification actions
      erase transient plaintext and revoke session credentials
      retain/delete encrypted backlog only according to consent policy
    ENDIF
    ASSERT no sensitive plaintext crosses component boundary
    ASSERT only acknowledged or explicitly deleted records leave backlog
    ASSERT UI thread performs no blocking work
  ENDWHILE
ENDPROCEDURE
```

**Component mapping:** internal communication uses explicit Intents carrying opaque IDs, not health payloads. Platform events use supported callbacks/system broadcasts where appropriate. Ordered broadcasts are not a security boundary; validate sender and every receiver if legacy ordered delivery is used. WorkManager handles deferrable periodic upload. Foreground service is reserved for permitted, ongoing, user-noticeable work.

## A1.5 Manual trace
| Event | Choose | Constraint check | Action | Notify / undo |
|---|---|---|---|---|
| Sensor reading S01 | Validate and encrypt | Permission/key valid | Persist and enqueue | Intent contains job ID only |
| Connectivity lost | Select S01 | Network none | Defer to WAITING_NETWORK | Keep encrypted backlog |
| Enter Doze | Select S01 | Routine work blocked | Defer with backoff | UI remains responsive |
| Critical reading S02 | Alert path | Permission and encryption valid | Persist and post allowed alert | Minimal notification text |
| User logout | All user jobs | Logout generation changed | Cancel workers and pending actions | Clear transient secrets; apply consent retention |

This demonstrates choose → check → execute/defer → notify → cancel/backtrack. Backtracking releases leases, cancels stale work and restores durable queue state; it does not delete unacknowledged records.

# TASK A2 — Incremental, Safe Synchronisation (5)

## A2.1 Diagnosis
The naïve loop examines and attempts every record without first checking network, battery, priority, encryption, conflict or acknowledgement. It can wake the radio needlessly, drain battery, transmit plaintext, overwrite newer remote versions, repeat duplicate uploads and lose retry state. Continuing after network failure is not a retry policy.

## A2.2 Redesigned pseudocode
```text
PROCEDURE INCREMENTAL_SYNC(local_store, remote_index, runtime)
  sync_set ← EMPTY
  FOR EACH record ordered by priority DESC, age ASC
    IF explicit_user_delete OR retention_expired THEN
      DISCARD only under explicit deletion/retention policy; CONTINUE
    ENDIF
    IF sensitive(record) AND NOT encrypted(record) THEN
      QUARANTINE; audit; CONTINUE
    ENDIF
    IF battery < record.minimum_battery THEN DEFER; CONTINUE ENDIF
    IF network = NONE OR (network = METERED AND NOT metered_allowed)
      THEN DEFER; CONTINUE
    ENDIF
    remote ← LOOKUP record ID and version
    IF remote newer AND contents differ THEN
      resolution ← APPLY_CONFLICT_POLICY(record, remote)
      IF resolution = NEEDS_USER THEN DEFER
      ELSE ADD resolution to sync_set
      ENDIF
    ELSE ADD record to sync_set
    ENDIF
  ENDFOR
  FOR EACH item IN sync_set
    IF constraints_changed OR authentication_expired THEN DEFER; CONTINUE ENDIF
    result ← UPLOAD encrypted item with idempotency key
    CASE result:
      ACK: mark acknowledged; advance cursor
      TRANSIENT_FAILURE: defer with bounded backoff
      PERMANENT_POLICY_FAILURE: quarantine or discard only if policy says so
      CONFLICT: resolve or defer; never blind overwrite
    ENDCASE
  ENDFOR
ENDPROCEDURE
```
Every record takes Upload, Defer, Discard under a defined rule, or Resolve Conflict.

## A2.3 Five-record pruning trace
Assume battery 45%, network metered, and metered upload disabled.

| Record | Priority | Size | Sensitivity | Encrypted | Decision |
|---|---:|---:|---|---|---|
| R1 | 5 | 4 KB | Critical health | Yes | Defer: metered policy |
| R2 | 4 | 2 KB | Public event | Yes | Defer: metered policy |
| R3 | 3 | 8 KB | Health | No | Reject/quarantine: plaintext sensitive data |
| R4 | 2 | 1 KB | Public | Yes | Defer: metered policy |
| R5 | 1 | 20 KB | Health | Yes | Defer: metered policy |

**Early termination:** R3 is rejected before payload construction or network access. An upload/retry branch cannot be correct and safe while the required encryption precondition is false. It must be encrypted through a trusted key path or quarantined.

## A2.4 Offline-first challenge
A rule that permanently discards records when network is absent is invalid under offline-first eventual consistency. The violated assumption is that immediate remote delivery is required. Network absence must prune only the current upload attempt: persist the record in a durable outbox and retry later with version metadata, idempotency and conflict resolution. Sensitive-plaintext rejection remains valid.

# TASK A3 — Common Background-Work Pattern (5)

| Component | Sensor collection | Data sync | Push notification |
|---|---|---|---|
| State | Permission, last sample, cadence, battery | Outbox, versions, retries, network, ACK | Token, message ID, expiry, settings |
| Decision variable | Sample/defer/stop | Upload/defer/resolve/discard | Deliver/defer/suppress |
| Candidates | Callback, foreground service, worker | WorkManager worker, retry, resolver | Push receiver, notification worker |
| Feasibility | Permission, privacy, rate, Doze | Encryption, auth, network, battery | Signature/token, expiry, permission |
| Goal | Valid sample stored | Remote ACK and cursor advanced | Permitted alert delivered once or expired |
| Pruning/defer | Low battery, revoked permission, pause | Offline, metered policy, key unavailable | Expired, muted, invalid token |
| Undo/cancel | Stop listener; release sensor | Release lease; retain outbox | Cancel pending notification; deduplicate |

## A3.1 Common pattern
All are asynchronous event-driven state machines: receive events, maintain durable state, select candidate action, check feasibility, execute bounded work, record result, then advance, retry or cancel. They require idempotency, observability and cleanup because the process may stop at any time.

## A3.2 Generic pseudocode
```text
PROCEDURE SCHEDULE_OR_EXECUTE(State)
  events ← COLLECT external and completion events
  State ← APPLY_EVENTS_TRANSACTIONALLY(State, events)
  candidates ← GENERATE_CANDIDATE_WORK(State)
  ORDER candidates by priority, deadline, age
  FOR EACH candidate
    action ← SELECT_ACTION(candidate, State)
    IF NOT SECURITY_PRECONDITIONS(action) THEN REJECT_AND_AUDIT; CONTINUE ENDIF
    IF NOT RESOURCE_AND_PLATFORM_FEASIBLE(action) THEN
      PERSIST_WAITING_STATE; SCHEDULE_ELIGIBILITY_RECHECK; CONTINUE
    ENDIF
    checkpoint ← SAVE_RECOVERY_CHECKPOINT(State)
    result ← EXECUTE_IDEMPOTENT_ACTION(action)
    IF SUCCESS THEN COMMIT state and result
    ELSE IF TRANSIENT_FAILURE THEN
      RESTORE checkpoint; RELEASE resources; PERSIST retry with backoff
    ELSE RESTORE_OR_COMPENSATE; CANCEL dependent work; RECORD failure
    ENDIF
  ENDFOR
  RETURN State
ENDPROCEDURE
```

## A3.3 Undo/cancellation
Cleanup releases sensor listeners, worker leases, locks, temporary files and pending notification actions, and restores retryable state. If a sync worker is cancelled after opening a transaction but before server ACK, omitting rollback can leave the record marked sent even though it never arrived. The record is silently lost. Restore it to the outbox and retry idempotently.

# TASK A4 — Tractability and Placement (4)

| Problem | Solution | Efficient verification? | Resource class | Reason |
|---|---|---|---|---|
| Tiny on-device image classifier | Label and confidence | Yes, fixed inference and test-set metrics | On-device feasible | Small bounded model; local latency/privacy |
| Cloud speech recognition | Transcript with timestamps/confidence | Yes, reference transcript and WER | Network-bound | Audio transfer and server latency |
| Nearby P2P file sharing | Authenticated integrity-checked transfer | Yes, hash/bytes/peer authentication | Security-critical | Untrusted peers, identity and integrity |
| E2E encrypted messaging | Correct endpoint plaintext from ciphertext | Partly; protocol tests/test vectors, formal proof harder | Security-critical | Key management, forward secrecy, metadata |
| Multiplayer state sync | Consistent-enough authoritative state in latency budget | Bounded traces yes; global consistency harder | Hybrid required | Client prediction plus server reconciliation |
| Offline vector map rendering | Correct visible tiles/labels for viewport/zoom | Yes, coverage and visual regression | Battery-critical | CPU/GPU, memory, storage and energy |

“Runs slowly” is only a symptom. Define workload, device, latency/frame-time percentile, throughput, energy, memory, network and quality objective. A 200 ms task may be fine in background sync but unacceptable in a 60 Hz frame. Local processing avoids network delay and raw-data transfer but consumes device CPU, memory and battery. Cloud offload scales compute but adds bandwidth, latency, availability, cost and exposure risks. Hybrid placement must state which data leaves device, encryption, authority and offline behaviour.

# TASK A5 — Approximate UI Optimisation (4)

## A5.1 Exact approach
For each allowed tuple (decode resolution, cache size, prefetch distance), replay the same feed, measure frame misses/energy/memory, reject hard-limit violations and select minimum weighted cost. This is exact only for the finite candidate grid and assumed model. If n feed items each have q, c and p choices, naïve joint search can reach (qcp)^n; device profiles multiply the search.

## A5.2 Adaptive pseudocode
```text
PROCEDURE ADAPT_FEED(metrics, parameters, limits)
  parameters ← initial quality, cache capacity, prefetch window
  REPEAT
    metrics ← MEASURE(frame_time_p95, dropped_frames, battery,
                      memory_pressure, decode_queue)
    IF frame_time_p95 > frame_budget THEN
      lower quality if possible
      ELSE reduce prefetch window
      ELSE evict least-recently-used cache entry
    ELSE IF battery < battery_floor THEN
      reduce prefetch window and cache capacity
    ELSE IF frame time safely below budget AND memory low THEN
      cautiously increase prefetch window
    ENDIF
    APPLY changes at frame boundary; RECORD state and operation counts
  UNTIL stable for K windows OR maximum adjustments reached
  RETURN parameters, metrics
ENDPROCEDURE
```
Selection restores frame budget first, then reduces energy/memory while retaining acceptable visual quality.

## A5.3 Trade-off
A feasible smooth experience meets observed frame-time/memory constraints for tested workloads. It does not prove global minimum energy or maximum quality. Greedy changes can miss interactions among cache, decode and prefetch. The sacrifice is optimality guarantee in exchange for bounded decisions and responsiveness. Exact optimality requires complete search over a correct model and fixed workload.
