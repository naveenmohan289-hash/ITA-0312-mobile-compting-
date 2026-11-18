# Architecture and build patterns

## Layered architecture
- Domain: SensorRecord, SyncJob, NotificationEvent, DeviceConstraints.
- Application: ValidateAndEncrypt, ScheduleWork, SyncCoordinator, ConflictResolver.
- Platform adapters: sensor callback, WorkManager worker, permitted foreground-service adapter, notification adapter, connectivity/battery observers.
- Data: encrypted local database, transactional outbox, retry metadata, acknowledgement cursor.
- Remote: authenticated API, idempotency key, server acknowledgement.

## Patterns
1. Outbox: persist event and pending upload atomically.
2. State machine: NEW → PERSISTED → QUEUED → RUNNING → ACKNOWLEDGED / WAITING / FAILED.
3. Constraint scheduling: network, battery, charging and idle requirements.
4. Idempotent retry: stable ID prevents duplicate remote writes.
5. Priority scheduling: critical/high-value jobs first without bypassing security.
6. Compensation: release leases and restore outbox after cancellation.
7. Adapter: isolate Android APIs from platform-independent policy.

## Build workflow
Define immutable job model; implement policy; add encrypted persistence; add WorkManager adapter passing opaque IDs only; add explicit internal Intent receivers; instrument privacy-safe counters; test permission revocation, Doze, network loss, process death and duplicates; profile real devices. Python deliverable implements policy/simulation/tests, not an Android Gradle application.
