# Product Requirements Document
## IBVAP v3: Critical Gap Closure and Pilot Hardening

| Field | Value |
|---|---|
| Document version | 3.0 |
| Status | Proposed execution PRD |
| Supersedes | PRD v2.0 Secure Multi-Camera Operations Platform |
| Baseline | Current repository after reported Stage 2A-2D work |
| Target outcome | Verified, secure, end-to-end pilot slice |
| Primary owner | Team PERCEPTRONS |

## 1. Purpose

PRD v2.0 defined the target pilot platform. The current repository contains many of the planned models, schemas, utilities, dashboard workflows, and API routes, but verification identified gaps between component existence and production behavior.

This PRD defines the next development increment: connect the existing components into one real execution path, close the highest-risk security issues, make readiness truthful, and establish repeatable evidence that the pilot works.

This document is intentionally narrower than PRD v2.0. New analytics features shall not be prioritized until the critical path and security foundations below are complete.

## 2. Verified Baseline

The repository currently includes:

- Extended alert lifecycle and provenance fields.
- `FenceRule`, `EvidenceAsset`, and `SystemEvent` model definitions.
- Tracker, geometry utilities, YOLO output parsing, and NMS utilities.
- RTSP/local capture worker structure and procedural demo generators.
- Alert lifecycle/provenance filters and CSV export UI.
- `/ready`, alert export, evidence, and fence-rule routes.
- Four backend tests covering geometry, tracking, and ledger tamper detection.
- A frontend production build that currently succeeds.

The following are not yet accepted as complete because runtime wiring or security verification is missing:

- Capture worker to detector to tracker to rule-engine execution.
- Bounded queue behavior and queue telemetry.
- Authenticated stream and WebSocket access.
- Truthful model and worker readiness reporting.
- Evidence asset creation and retrieval.
- Database migrations and upgrade safety.
- Production C2 delivery.
- Dependency-installable and reproducible automated tests.

## 3. Criticality and Priorities

| Priority | Meaning | Release rule |
|---|---|---|
| P0 | Security, data loss, or core pipeline failure | Must be complete before pilot testing |
| P1 | Required pilot behavior or operational reliability | Must be complete before pilot release |
| P2 | Quality, scale, usability, or maintainability improvement | May follow the first pilot |

## 4. Critical Gap Register

| ID | Gap | Risk | Priority | Owner area |
|---|---|---|---|---|
| G-01 | No verified runtime path from captured frames to detector-backed alerts | Platform can appear live while producing only simulated alerts | P0 | Video/inference |
| G-02 | Capture worker has no bounded queue | Memory growth, stale frames, and unpredictable latency | P0 | Video ingestion |
| G-03 | WebSocket and camera stream tokens are accepted but not validated | Unauthorized users may receive live alerts or video | P0 | Security/API |
| G-04 | Readiness hardcodes model readiness and does not represent worker health | Orchestrators and operators receive false health signals | P0 | Operations |
| G-05 | Production CORS and JWT defaults are unsafe | Cross-origin exposure and token forgery risk | P0 | Security/deployment |
| G-06 | Alert IDs use row counts | Concurrent writers can collide and corrupt alert creation | P0 | Data/API |
| G-07 | EvidenceAsset is defined but not populated by the alert path | Evidence retention, hashing, and access audit are incomplete | P1 | Evidence |
| G-08 | `create_all()` is used instead of migrations | Existing installations cannot be safely upgraded | P1 | Database |
| G-09 | C2 delivery is logging-only | Tactical integration claims are not demonstrable | P1 | Integrations |
| G-10 | Test suite cannot run in the active environment | Reported verification is not reproducible | P1 | QA/tooling |
| G-11 | Client CSV fallback can export without server audit | Compliance record can be incomplete | P1 | Frontend/API |
| G-12 | Documentation and code can diverge on simulated vs. real capabilities | Operators and evaluators may misinterpret system state | P1 | Product/docs |
| G-13 | No full end-to-end, authorization, failure-isolation, or performance suite | Core pilot risks remain unmeasured | P1 | QA |
| G-14 | No URL routing or browser history integration | Navigation is not a conventional multi-page workflow | P2 | Frontend |
| G-15 | Large TensorFlow bundle and limited mobile/performance measurement | Slow startup and weak field usability | P2 | Frontend/performance |

## 5. Release Objective

Deliver one verifiable pilot slice:

```text
Recorded/RTSP source
  -> bounded per-camera queue
  -> YOLO detector
  -> per-camera tracker
  -> configured fence rule
  -> deduplicated alert
  -> encrypted evidence asset
  -> ledger record
  -> authenticated WebSocket
  -> operator acknowledgement
  -> audit record
```

The slice must work with a recorded fixture even when no physical camera is available. Demo generators may remain available, but all generated events and frames must be labelled as simulation.

## 6. Functional Requirements

### FR-1: End-to-end inference worker (P0)

- FR-1.1: Each enabled camera shall have an independently managed capture/processing worker.
- FR-1.2: The worker shall read frames from a source, publish them to a bounded queue, run the configured detector, update the camera tracker, and submit active tracks to the rule engine.
- FR-1.3: The worker shall attach camera ID, source-frame timestamp, model version, and processing timestamp to each inference result.
- FR-1.4: Detector failure on one frame shall be recorded and shall not terminate the camera worker.
- FR-1.5: Failure of one camera worker shall not stop other camera workers or the API.
- FR-1.6: The system shall provide a deterministic recorded-video fixture that crosses a configured tripwire.

**Acceptance:** A test fixture produces a detector-backed `provenance=detector` alert with a stable track ID, rule ID, source-frame time, snapshot, ledger record, and WebSocket event.

### FR-2: Bounded queues and backpressure (P0)

- FR-2.1: Each camera queue shall have a configured maximum size.
- FR-2.2: Queue overflow shall drop the oldest stale frame or follow an explicitly configured policy.
- FR-2.3: The queue shall expose depth, maximum depth, dropped-frame count, oldest-frame age, and last-consumer time.
- FR-2.4: The processing path shall prefer recent frames when latency is more important than completeness.
- FR-2.5: Worker shutdown shall unblock producers and consumers and release capture resources.

**Acceptance:** A stress test exceeding queue capacity keeps memory bounded, reports dropped frames, and maintains the configured maximum frame age.

### FR-3: Detector and tracker contract (P0)

- FR-3.1: The detector adapter shall expose a typed result contract for class, confidence, pixel box, normalized box, model version, and inference latency.
- FR-3.2: Model output parsing shall be tested against a checked-in tensor fixture for person, car, truck, and motorcycle classes.
- FR-3.3: NMS behavior shall be tested for overlapping boxes and class-specific results.
- FR-3.4: Tracker state shall be scoped by camera and shall expose missed frames, dwell time, direction, and last-seen time.
- FR-3.5: Detector confidence and tracker state shall not be replaced by random values in the detector-backed path.

**Acceptance:** Unit and integration tests prove detector output reaches the rule engine without changing schema or coordinate meaning.

### FR-4: Rules and alert correctness (P0)

- FR-4.1: Fence rules shall be loaded from the database for the relevant camera.
- FR-4.2: Tripwire crossing shall use consecutive track positions and respect direction configuration.
- FR-4.3: Polygon and loiter rules shall validate coordinate count and coordinate range before activation.
- FR-4.4: Cooldown keys shall include camera, rule, track, and event type.
- FR-4.5: Alert creation shall use a collision-resistant ID strategy that remains correct with concurrent workers.
- FR-4.6: Alert creation, evidence creation, and ledger append shall use a transaction boundary or compensating failure path.
- FR-4.7: Every detector-backed alert shall include provenance, rule ID, rule version, and source-frame time.

**Acceptance:** Repeated crossings by one track create only one alert during cooldown; separate cameras and tracks remain independent.

### FR-5: Evidence lifecycle (P1)

- FR-5.1: Alert creation shall create an `EvidenceAsset` for every captured snapshot.
- FR-5.2: Evidence shall be encrypted before persistence and assigned a SHA-256 content hash.
- FR-5.3: Evidence metadata shall be returned without encrypted payloads unless the caller has explicit evidence access.
- FR-5.4: Evidence access and download shall be authenticated, authorized, and audit logged.
- FR-5.5: Missing, processing, expired, and unavailable evidence states shall be distinguishable.
- FR-5.6: Retention cleanup shall remove expired evidence and write an audit/system event.

**Acceptance:** A test alert can be created, evidence can be retrieved by an authorized role, unauthorized retrieval is rejected, and the content hash verifies after decryption.

### FR-6: Authentication and endpoint authorization (P0)

- FR-6.1: WebSocket authentication shall validate a token before registering the connection.
- FR-6.2: Camera stream access shall validate a token and authorize the requested camera.
- FR-6.3: Invalid, expired, missing, or insufficient tokens shall be rejected consistently across REST, WebSocket, and stream access.
- FR-6.4: Service accounts shall be distinct from interactive users and restricted to ingestion/inference operations.
- FR-6.5: Authorization tests shall cover operator, supervisor, administrator, service account, anonymous, expired-token, and malformed-token cases.
- FR-6.6: Tokens shall not be placed in URLs for browser or stream access when a safer authenticated transport is available; URL tokens shall be treated as a documented compatibility exception with logging protections.

**Acceptance:** The authorization matrix passes for every protected endpoint, including `/ws/alerts`, `/cameras/{id}/stream`, evidence, export, fence rules, and alert mutations.

### FR-7: Secure configuration (P0)

- FR-7.1: Production startup shall fail when `IBVAP_JWT_SECRET`, encryption key, database URL, or CORS allowlist is absent or unsafe.
- FR-7.2: Development defaults shall be enabled only under an explicit development environment flag.
- FR-7.3: Wildcard CORS shall be prohibited when credentials or authentication are enabled outside local development.
- FR-7.4: Demo account seeding shall require an explicit development/demo flag.
- FR-7.5: Secrets shall be redacted from logs, errors, metrics, URLs, and frontend bundles.

**Acceptance:** A production configuration test fails startup for unsafe defaults and succeeds only with valid secrets and explicit allowed origins.

### FR-8: Database migrations and concurrency (P1)

- FR-8.1: Introduce a migration tool and version all schema changes.
- FR-8.2: Existing prototype databases shall have an upgrade path for new alert, rule, evidence, and telemetry fields.
- FR-8.3: Alert and ledger sequence creation shall be safe under concurrent writers.
- FR-8.4: Foreign keys, indexes, uniqueness constraints, and delete behavior shall be tested on SQLite and PostgreSQL profiles.
- FR-8.5: Startup shall not silently alter production schema.

**Acceptance:** A clean database and a v2 prototype database both migrate successfully, preserve alerts, and pass integrity verification.

### FR-9: C2 integration adapter (P1)

- FR-9.1: Implement a versioned outbound event contract for high-severity alerts.
- FR-9.2: Requests shall be signed, idempotent, timeout-bounded, and retryable.
- FR-9.3: Failed deliveries shall remain locally persisted and be placed in a retry/dead-letter state.
- FR-9.4: Delivery attempts, responses, and final status shall be audit/system events without logging sensitive evidence.
- FR-9.5: The mock receiver shall test duplicate delivery, timeout, invalid signature, and recovery behavior.

**Acceptance:** A high-severity alert remains available locally when C2 is down, then is delivered once after recovery with a verifiable audit trail.

### FR-10: Observability and truthful readiness (P0)

- FR-10.1: `/health` shall be liveness-only and shall not claim model or worker readiness.
- FR-10.2: `/ready` shall report database, model, worker, queue, and configuration readiness independently.
- FR-10.3: `model_loaded` shall reflect actual model state, not a constant.
- FR-10.4: Readiness shall return a non-ready status when required dependencies or workers are unavailable.
- FR-10.5: Structured events shall include camera ID, worker ID, alert ID, request ID, and error code where applicable.
- FR-10.6: Dashboard status shall distinguish backend offline, stream unavailable, detector unavailable, and simulation mode.

**Acceptance:** Tests toggle each dependency and prove the readiness response changes accurately.

### FR-11: Audit-safe frontend behavior (P1)

- FR-11.1: A successful export shall occur only after the server confirms and records the export.
- FR-11.2: The frontend shall not silently fall back to an unaudited local export when server export fails in supervisor/admin workflows.
- FR-11.3: Failed mutations shall either roll back optimistic UI state or show a clearly pending/unsaved state.
- FR-11.4: Success and failure messages shall identify whether the action was persisted or local-only.
- FR-11.5: Mobile layouts shall pass 320px, 390px, and 430px viewport checks without horizontal overflow.

**Acceptance:** A failed export produces an actionable error and no downloaded compliance report; successful export creates a server audit record.

### FR-12: Documentation and provenance (P1)

- FR-12.1: Every simulated stream and simulated alert shall be visibly labelled and filterable.
- FR-12.2: Documentation shall identify which capabilities are real, simulated, optional, or not implemented.
- FR-12.3: `walkthrough.md` or an equivalent verification document shall be checked into the repository.
- FR-12.4: The runbook shall include exact dependency installation, test, migration, startup, health, readiness, and rollback commands.
- FR-12.5: Claims shall not describe mock C2, generated streams, or browser-only inference as production CCTV analytics.

**Acceptance:** A new developer can reproduce the test suite and identify the provenance of every dashboard alert.

## 7. Data Model and API Changes

### Required model changes

- Add `source_type` and `timezone` to cameras.
- Add queue/worker telemetry storage or an explicit metrics backend.
- Add `EvidenceAsset` lifecycle status and access metadata.
- Add C2 delivery status, attempt count, next retry time, and idempotency key.
- Add session/revocation storage if token revocation is required.
- Add unique constraints and indexes for alert timestamps, camera IDs, provenance, state, and ledger sequence.

### Required endpoint behavior

- `/ready` must return an accurate readiness status and appropriate HTTP semantics.
- `/ws/alerts` must authenticate before connection registration.
- `/cameras/{id}/stream` must authorize camera access.
- `/alerts` must use concurrency-safe ID generation.
- `/alerts/{id}/evidence` must return `EvidenceAsset` metadata and enforce access policy.
- `/alerts/export.csv` must be the authoritative audited export path.
- A new `/metrics` endpoint or metrics integration shall expose worker, queue, inference, alert, and delivery measurements.

## 8. Test Plan

### P0 tests

- Recorded fixture end-to-end detector-to-alert test.
- Bounded queue stress and stale-frame test.
- Worker failure isolation test.
- WebSocket anonymous/invalid/valid token test.
- Camera stream authorization test.
- Production configuration rejection test.
- Truthful readiness state test.
- Concurrent alert ID creation test.

### P1 tests

- Evidence encryption, hash, retention, and access audit test.
- Database migration from prototype schema.
- C2 retry, signature, idempotency, timeout, and dead-letter tests.
- Server-authoritative CSV export and audit test.
- API error contract tests.
- Four-role authorization matrix.
- 8-hour soak test with at least four camera workers.

### Frontend tests

- Mobile viewport checks at 320px, 390px, and 430px.
- No horizontal document overflow.
- Mobile drawer open/close/navigation.
- Alert filter and lifecycle actions.
- Offline, empty, success, and error states.
- Provenance labels for detector and simulation events.

## 9. Delivery Sequence

### Sprint 1: P0 security and configuration

- Secure JWT/encryption/CORS configuration.
- Authenticate WebSocket and camera stream endpoints.
- Correct readiness semantics.
- Add authorization and configuration tests.

### Sprint 2: P0 real execution path

- Implement bounded queues.
- Wire capture workers to detector, tracker, and rule engine.
- Add deterministic recorded fixture.
- Fix concurrent alert/ledger ID creation.
- Add worker failure isolation.

### Sprint 3: P1 persistence and integration

- Implement EvidenceAsset creation and lifecycle.
- Add database migrations and upgrade tests.
- Add C2 adapter with retry and idempotency.
- Add telemetry and metrics endpoint.

### Sprint 4: P1 verification and release hardening

- Remove unaudited export fallback.
- Add complete authorization, integration, soak, and mobile tests.
- Add verification walkthrough and operational runbook.
- Measure latency, throughput, recovery, and hardware efficiency.

## 10. Definition of Done

The v3 increment is complete only when:

1. A recorded or RTSP source produces a real detector-backed alert through the complete pipeline.
2. Queue depth and dropped-frame behavior are bounded and measured.
3. Anonymous clients cannot access streams or WebSocket alerts.
4. Production configuration rejects unsafe secrets, wildcard CORS, and demo seeding.
5. `/ready` reports actual model and worker state.
6. EvidenceAsset records are created, encrypted, hashed, authorized, and audited.
7. Database migrations upgrade an existing prototype database without data loss.
8. Concurrent alert creation cannot collide or break ledger sequencing.
9. C2 failure does not lose local alerts and recovery is idempotent.
10. The test suite installs and runs from documented commands.
11. Frontend export, mutation, provenance, empty, error, and mobile workflows are verified.
12. Documentation clearly distinguishes real, simulated, and unavailable capabilities.

## 11. Success Metrics

Metrics shall be measured on a named reference machine and dataset:

- P95 source-frame-to-alert latency <= 2 seconds.
- At least 10 processed FPS per stream for the supported pilot configuration.
- At least 4 concurrent workers without unbounded queues.
- Worker recovery within 60 seconds after source restoration.
- Zero unauthorized stream or WebSocket accesses in the authorization suite.
- Zero lost local alerts during C2 outage simulation.
- Zero critical findings in dependency and security review.
- 100% of exported reports represented by an audit record.
- No horizontal overflow from 320px through 430px viewport widths.

## 12. Deferred Work

The following remain outside v3 unless required to prove the pilot slice:

- Cross-camera identity tracking.
- Production facial recognition/watchlist matching.
- Production ANPR model accuracy work.
- Public blockchain anchoring.
- Multi-region deployment.
- Custom domain, public marketing analytics, reviews, and waitlist functionality.

## 13. Required Decisions

Before Sprint 2, decide:

- Reference detector model and ONNX output format.
- Tracker implementation and license.
- Queue overflow policy: drop-oldest, drop-newest, or priority.
- PostgreSQL version and migration tool.
- Evidence storage and key-management approach.
- C2 message schema, signing method, retry policy, and ownership.
- Supported hardware and test dataset.
