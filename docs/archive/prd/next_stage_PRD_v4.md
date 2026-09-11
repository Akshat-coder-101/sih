# Product Requirements Document
## IBVAP v4: Verified Pilot Release and Production Readiness

| Field | Value |
|---|---|
| Document version | 4.0 |
| Status | Proposed release PRD |
| Supersedes | PRD v3 Critical Gap Closure and Pilot Hardening |
| Baseline | Current repository after reported v3 implementation |
| Target outcome | Reproducible, secure, detector-backed pilot release |
| Primary owner | Team PERCEPTRONS |

## 1. Purpose

PRD v3 introduced the critical-gap closure plan and the repository now contains workers, bounded queues, alert lifecycle fields, evidence records, readiness and metrics routes, endpoint token helpers, a fixture video, and expanded tests.

Verification still found a difference between implemented components and release-grade behavior. PRD v4 is the final hardening increment for the first pilot. It prioritizes proof of the real execution path, consistent security in every environment, reliable integrations, safe schema upgrades, and reproducible test execution.

No new analytics capability shall be accepted ahead of the release blockers in this document.

## 2. Release Status Baseline

### Present

- Per-camera capture and processing worker structure.
- Drop-oldest bounded frame queue.
- Tracker, tripwire geometry, polygon containment, and cooldown logic.
- YOLO ONNX parsing and NMS utilities.
- Alert lifecycle and provenance fields.
- EvidenceAsset creation in detector-backed alert evaluation.
- HMAC signing helper and C2 payload construction.
- `/health`, `/ready`, `/metrics`, evidence, export, and fence-rule routes.
- Frontend lifecycle/provenance filters and server-authoritative export flow.
- Fixture generator and 10 declared backend unit tests.

### Not release-verified

- Real YOLO model execution through a recorded fixture.
- Universal authentication of WebSocket and stream routes.
- Accurate model readiness reporting.
- Actual network delivery and retry of C2 events.
- Migration-based database upgrade.
- Reproducible test execution from a clean environment.
- Full authorization, concurrency, failure-isolation, and performance evidence.

## 3. Release Objective

Release a pilot in which an authorized operator can monitor a real or recorded source and complete this verifiable path:

```text
Source video
  -> bounded queue
  -> configured detector
  -> per-camera tracker
  -> database fence rule
  -> deduplicated detector alert
  -> encrypted EvidenceAsset
  -> ledger record
  -> authenticated WebSocket event
  -> operator acknowledgement
  -> audit record
```

The same application shall expose a clearly labelled simulation mode for generated scenes and synthetic alerts. Simulation mode shall never be used as evidence for production performance claims.

## 4. Release Blockers

| ID | Blocker | Priority | Exit evidence |
|---|---|---:|---|
| V4-01 | Authentication differs between development and production | P0 | Anonymous stream and WebSocket tests fail in every environment |
| V4-02 | `/ready` claims a model is loaded when it may not be | P0 | Readiness reflects actual configured model and worker state |
| V4-03 | Worker defaults to an unloaded detector and contour fallback | P0 | Configured model path is loaded and fixture inference is measured |
| V4-04 | Fixture test bypasses capture and inference | P0 | Test opens fixture and exercises worker pipeline |
| V4-05 | C2 adapter logs instead of sending | P0 | Mock receiver records signed request and retry behavior |
| V4-06 | Production CORS and secret policy are incomplete | P0 | Unsafe production configuration fails startup |
| V4-07 | Startup schema creation replaces migrations | P1 | Existing database upgrades through versioned migration |
| V4-08 | Alert/ledger concurrency is unproven | P1 | Parallel writers pass uniqueness and chain tests |
| V4-09 | Test dependencies and commands are not reproducible | P1 | Clean environment installs and runs all tests |
| V4-10 | Operational metrics are incomplete or unvalidated | P1 | Metrics match worker state under controlled load |
| V4-11 | Documentation references unavailable verification artifacts | P1 | Walkthrough and runbook exist and match actual commands |
| V4-12 | Frontend still contains compatibility assumptions for unauthenticated streams | P1 | Authenticated browser stream strategy is documented and tested |

## 5. Functional Requirements

### FR-1: Environment-independent endpoint security (P0)

- FR-1.1: `/ws/alerts` shall reject missing, malformed, expired, revoked, and insufficient tokens before registering a socket in development, staging, and production.
- FR-1.2: `/cameras/{cam_id}/stream` shall validate the token and authorize camera access in every non-test environment.
- FR-1.3: The anonymous guest operator shortcut shall be restricted to an explicit test mode and shall never be active in development, staging, or production by default.
- FR-1.4: WebSocket rejection shall use a documented close code and shall not leak token-validation details.
- FR-1.5: Stream authorization shall return consistent `401`, `403`, and `404` responses without exposing camera existence where policy requires concealment.
- FR-1.6: The browser client shall use a documented authentication mechanism for image/video streams that does not expose bearer tokens in logs or referrers.

**Acceptance:** The authorization matrix passes for anonymous, operator, supervisor, administrator, service account, malformed, expired, and revoked credentials across REST, WebSocket, stream, evidence, export, and rule endpoints.

### FR-2: Truthful readiness and model lifecycle (P0)

- FR-2.1: A model registry shall identify the configured model path, version, classes, device, and load status.
- FR-2.2: `/ready` shall report model readiness from the actual detector registry, not a constant.
- FR-2.3: Readiness shall distinguish liveness, database readiness, model readiness, worker readiness, and configuration readiness.
- FR-2.4: A `503 Service Unavailable` response shall be returned when a required pilot dependency is unavailable.
- FR-2.5: Model load failure shall produce a structured system event and an operator-visible degraded state.
- FR-2.6: Startup shall not report ready while all workers use a non-model fallback unless explicit simulation mode is active and reported.

**Acceptance:** Tests change model configuration, remove model weights, stop workers, and break the database; each condition produces the expected readiness response and dashboard state.

### FR-3: Configured detector execution (P0)

- FR-3.1: Detector configuration shall be supplied through environment or versioned deployment configuration.
- FR-3.2: Every production worker shall receive an explicit detector instance or an explicit simulation detector.
- FR-3.3: The detector shall expose model version, inference device, confidence threshold, NMS threshold, and measured latency.
- FR-3.4: Color-contour or synthetic detection shall be available only as a labelled fixture/simulation adapter.
- FR-3.5: Model output class mapping shall be validated against the configured model metadata.
- FR-3.6: Malformed model output shall fail the affected frame and create a telemetry event without stopping the worker.

**Acceptance:** A checked-in detector fixture or approved lightweight model produces known person and vehicle results with expected normalized coordinates.

### FR-4: Genuine fixture-driven end-to-end test (P0)

- FR-4.1: The test shall open `fixtures/test_crossing.mp4` through the capture component.
- FR-4.2: The test shall run frames through the bounded queue, detector adapter, tracker, and database-backed rule evaluator.
- FR-4.3: The test shall verify a detector-backed alert with `provenance=detector`, stable track ID, rule ID, source-frame timestamp, evidence hash, EvidenceAsset, ledger record, and broadcast payload.
- FR-4.4: The test shall verify cooldown deduplication across repeated crossing frames.
- FR-4.5: The fixture test shall not directly construct the final track as a substitute for worker execution.

**Acceptance:** The end-to-end test fails when any pipeline stage is disconnected or replaced by an unlabelled simulation fallback.

### FR-5: Real C2 delivery and reliability (P0)

- FR-5.1: High-severity alerts shall be serialized using a versioned C2 schema.
- FR-5.2: Requests shall include HMAC-SHA256 signature, timestamp, event ID, and idempotency key.
- FR-5.3: Delivery shall use a real HTTP client with connect/read timeouts and bounded retries.
- FR-5.4: A successful response shall be validated before marking delivery successful.
- FR-5.5: Failures shall remain locally persisted with attempt count, last error, next retry time, and terminal dead-letter state.
- FR-5.6: Retries shall not include encrypted evidence payloads unless explicitly required by the integration contract.
- FR-5.7: Duplicate delivery shall be safely ignored by the receiver using the idempotency key.

**Acceptance:** The mock C2 receiver observes a signed request, rejects an invalid signature, simulates timeout, receives a retry after recovery, and records only one accepted event.

### FR-6: Secure production configuration (P0)

- FR-6.1: Production startup shall reject the default JWT secret, weak JWT secrets, absent AES key, default C2 secret, wildcard CORS, and demo seeding.
- FR-6.2: CORS origins shall be parsed from an explicit allowlist and wildcard origins shall be rejected when credentials are enabled.
- FR-6.3: Secrets shall be loaded from a deployment secret mechanism and shall never be committed, returned, or logged.
- FR-6.4: Development, test, staging, and production configuration behavior shall be separately documented.
- FR-6.5: Test fixtures shall be able to inject secrets without mutating global production configuration.

**Acceptance:** Configuration tests cover every unsafe combination and production import fails safely before serving requests.

### FR-7: Database migrations and concurrency (P1)

- FR-7.1: Replace production `create_all()` startup behavior with a versioned migration tool.
- FR-7.2: Provide an upgrade migration from the prototype schema to the v4 schema.
- FR-7.3: Alert ID generation shall remain unique under concurrent workers and database retries.
- FR-7.4: Ledger sequence creation shall use a concurrency-safe strategy or a database-backed sequence.
- FR-7.5: Alert, evidence, ledger, and audit writes shall define transaction and recovery behavior.
- FR-7.6: PostgreSQL shall be the pilot reference database; SQLite shall remain a supported test/development profile only.

**Acceptance:** Two or more concurrent writers create alerts without duplicate IDs, missing ledger records, or broken chain links; clean and prototype databases both migrate successfully.

### FR-8: Evidence asset integrity and access (P1)

- FR-8.1: Every captured snapshot shall create exactly one linked EvidenceAsset unless an explicit deduplication policy applies.
- FR-8.2: Content hashes shall be computed over the documented canonical bytes.
- FR-8.3: EvidenceAsset lifecycle shall include `processing`, `available`, `expired`, and `failed` states.
- FR-8.4: Evidence retrieval shall use EvidenceAsset as the source of truth rather than duplicating alert snapshot logic.
- FR-8.5: Evidence access, download, expiry, and deletion shall be audited.
- FR-8.6: Encryption/decryption failures shall produce an unavailable state and not expose ciphertext.

**Acceptance:** Evidence survives restart, hash verification succeeds, unauthorized access is rejected, and retention cleanup is tested.

### FR-9: Observability and operations (P1)

- FR-9.1: `/health` shall remain liveness-only.
- FR-9.2: `/ready` shall expose component-level readiness.
- FR-9.3: `/metrics` shall expose worker FPS, processed frames, queue depth, dropped frames, frame age, inference latency, alert latency, C2 status, and WebSocket clients.
- FR-9.4: Metrics shall identify camera, worker, model, and environment labels without exposing secrets or sensitive evidence.
- FR-9.5: Logs shall be structured and include request ID, camera ID, alert ID, worker ID, and error code where applicable.
- FR-9.6: Shutdown, restart, source failure, model failure, and database failure shall be observable events.

**Acceptance:** A controlled failure exercise changes readiness, metrics, and system events in a predictable way.

### FR-10: Reproducible verification and documentation (P1)

- FR-10.1: Pin Python and Node versions or document supported version ranges.
- FR-10.2: Provide one clean-environment backend install command and one test command.
- FR-10.3: Provide one clean-environment frontend install, build, and browser smoke-test command.
- FR-10.4: Check in `walkthrough.md` or replace all references with an existing verification document.
- FR-10.5: Verification documentation shall record dependency versions, test counts, expected outputs, and known limitations.
- FR-10.6: Documentation shall never report tests as passed when they were only syntax-compiled or blocked by missing dependencies.

**Acceptance:** A new developer can clone the repository, install dependencies, run all tests, start the services, query health/readiness/metrics, and reproduce the documented results.

## 6. Test Matrix

| Area | Required tests |
|---|---|
| Endpoint security | REST, WebSocket, stream, evidence, export, and rule authorization matrix |
| Configuration | Unsafe production defaults, CORS, missing keys, demo seed isolation |
| Model lifecycle | Valid model, missing model, malformed output, readiness transitions |
| Queue | Drop-oldest, bounded memory, stale-frame age, shutdown unblocking |
| E2E | Fixture file through capture, queue, detector, tracker, rule, alert, evidence, ledger, broadcast |
| Concurrency | Parallel alert IDs, ledger ordering, transaction rollback, duplicate prevention |
| C2 | Signature, timeout, retry, idempotency, invalid response, dead-letter |
| Evidence | Encryption, hash, retrieval, expiration, access audit, failure state |
| Resilience | One worker failure, one camera failure, database restart, C2 outage |
| Frontend | Authenticated stream, WebSocket reconnect, error/readiness states, mobile overflow |
| Performance | Four workers, queue pressure, P95 alert latency, 8-hour soak |

## 7. Delivery Plan

### Sprint 1: Security and readiness

- Enforce endpoint authentication in every non-test environment.
- Fix CORS and production configuration validation.
- Add model registry and truthful readiness semantics.
- Add authorization and configuration tests.

### Sprint 2: Detector-backed E2E path

- Configure the detector through deployment settings.
- Replace direct-track fixture testing with worker-driven fixture execution.
- Add detector output fixtures and coordinate contract tests.
- Add worker failure isolation and queue telemetry tests.

### Sprint 3: Integration and persistence

- Implement real C2 HTTP delivery with retries and idempotency.
- Add C2 delivery persistence and dead-letter state.
- Add EvidenceAsset lifecycle and source-of-truth retrieval.
- Introduce migrations and concurrency-safe database writes.

### Sprint 4: Release verification

- Complete endpoint, resilience, performance, and browser smoke tests.
- Add walkthrough/runbook with reproducible commands.
- Run four-worker and 8-hour soak tests.
- Publish a pilot readiness report with measured limitations.

## 8. Definition of Done

V4 is complete only when:

1. Anonymous clients cannot access streams or alert WebSockets in any deployable environment.
2. Production readiness reflects actual database, model, worker, and configuration state.
3. A configured detector processes the recorded fixture through the full worker path.
4. The fixture produces a detector-backed, deduplicated, evidence-backed alert.
5. C2 delivery sends real signed HTTP requests and handles failure/retry/idempotency.
6. Unsafe production defaults and wildcard CORS are rejected at startup.
7. Migrations upgrade existing prototype data without loss.
8. Concurrent alert creation preserves IDs and ledger integrity.
9. EvidenceAsset is the authoritative evidence lifecycle record.
10. All declared tests run from a clean documented environment.
11. Metrics and logs demonstrate worker health, queue pressure, latency, and failures.
12. Documentation matches the actual system and labels simulation clearly.

## 9. Release Decision

The pilot may be released only if all P0 requirements pass and no P1 requirement has an unknown result. Any unavailable detector model, unauthenticated endpoint, logging-only C2 path, false readiness signal, or unreproducible test result is a release blocker.

The pilot shall be presented as a software-defined surveillance analytics system for controlled evaluation, not as a certified operational security product. Human operators remain responsible for interpreting alerts and taking action.
