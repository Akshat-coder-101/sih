# Product Requirements Document
## IBVAP Next Stage: Secure Multi-Camera Operations Platform

| Field | Value |
|---|---|
| Document version | 2.0 |
| Status | Proposed |
| Owner | Team PERCEPTRONS |
| Baseline | Prototype v0.1 / current repository |
| Target release | Production-ready pilot |
| Primary users | Operators, supervisors, administrators, system integrators |

## 1. Purpose

This document defines the next development stage for IBVAP. The current repository provides a functional demonstration dashboard with browser webcam inference, generated CCTV scenes, seeded alerts, a FastAPI service, SQLite persistence, encrypted evidence fields, JWT login, RBAC, WebSocket alert delivery, and a local hash-chain ledger.

The next stage must convert the demonstration paths into a secure, observable, testable pilot without presenting simulated capabilities as real operational intelligence.

## 2. Problem-to-Solution Traceability

| Operational problem | IBVAP response | Proof required |
|---|---|---|
| Conventional CCTV requires continuous manual observation | Multi-camera ingestion, object detection, tracking, rules, and prioritized alerts | Operator receives a detector-backed alert without watching every frame |
| FRS, ANPR, and smart cameras require specialized hardware | Software adapters run face, plate, and object models on standard IP-camera or recorded video | Same analytics pipeline works with a supported RTSP source and a local test file |
| Remote BOP links are unreliable | Per-camera bounded queues, reconnect logic, local buffering, and degraded operation | One failed camera does not stop other camera pipelines |
| Border crossings and perimeter breaches are difficult to identify quickly | Configurable virtual fences and direction-aware intrusion rules | Crossing fixture creates one deduplicated alert within the latency target |
| Suspicious behavior is difficult to review at scale | Dwell, loitering, night movement, and multi-signal rule evaluation | Each alert includes the rule, evidence, confidence, and provenance |
| Alerts and evidence need accountable handling | Encrypted evidence, RBAC, audit history, lifecycle states, and tamper-evident hashes | Unauthorized access is rejected and an authorized review is auditable |
| Existing command systems need integration without blocking the pilot | Versioned outbound webhook adapter with retries, signing, and a mock receiver | Integration failures do not lose the local alert or block the pipeline |

## 3. Capability Coverage

The following capabilities are product commitments. They may be delivered in separate stages, but they must not be described as operationally available until their acceptance tests pass.

| Capability | Delivery stage | Minimum pilot behavior |
|---|---|---|
| Human detection and tracking | 2B | Detect persons, assign per-camera track IDs, and show confidence and trajectory state |
| Vehicle detection and classification | 2B | Detect and classify car, truck, and motorcycle with a tested model fixture |
| Face detection | 2B | Detect and box faces; discard crops when no approved retention purpose exists |
| Facial recognition | 2C, governed feature | Optional watchlist matching only with approved data, consent/legal basis, threshold tests, and human review |
| ANPR | 2C | Detect plates, OCR text, confidence, and an explicit unreadable result without blocking the stream |
| Virtual fence intrusion | 2B | Evaluate configured line/polygon crossings and emit deduplicated alerts |
| Suspicious activity | 2C | Evaluate loitering, dwell, unusual movement, and rule combinations with explainable reasons |
| Night-time movement | 2C | Detect movement in configured night windows or low-light streams and label the detection context |
| Real-time alerts and event logging | 2B | Persist, broadcast, acknowledge, resolve, export, and audit events |
| Command and control integration | 2D | Send signed, idempotent alert messages through a versioned adapter with retry and dead-letter handling |

## 4. Solution Principles

- Software-first: use standard IP cameras and existing network/video infrastructure wherever the source provides a supported stream.
- Edge-aware: process frames near the source when bandwidth is constrained; synchronize metadata and alerts centrally when connectivity permits.
- Cheap-first inference: run person and vehicle detection continuously, then invoke face, ANPR, and higher-cost behavior models only on configured triggers.
- Human decision authority: analytics prioritize and explain events; they do not autonomously authorize force or tactical action.
- Fail independently: camera, model, network, and integration failures shall degrade one capability or source without taking down the command center.
- Measured claims: every accuracy, latency, cost, and scale claim must identify its test dataset, hardware, and measurement method.
- Privacy by design: minimize face and plate retention, restrict access, encrypt sensitive data, and support configured deletion.

## 5. Reference Architecture

```text
[Standard IP Cameras / Recorded Files]
		|
		v
[Secure Ingestion + Per-Camera Queues]
		|
		v
[Primary AI: Person and Vehicle Detection]
		|
		v
[Tracker: ID, Position, Direction, Dwell]
		|
	+-------+--------+
	|                |
	v                v
[Virtual Fence]   [Triggered Models]
		  Face / ANPR / Night / Behavior
	|                |
	+-------+--------+
		v
[Explainable Rule Engine + Deduplication]
		|
		v
[Alert + Encrypted Evidence + Hash Ledger]
		|
	+-------+--------+
	|                |
	v                v
[Operator UI]     [C2 Integration Adapter]
```

The architecture shall support edge deployment at a BOP for low-latency inference and intermittent connectivity. A central command center may receive alert metadata and selected evidence, while local buffering preserves events during link outages. The initial pilot may run all services on one supported workstation, provided the interfaces remain separable for later edge and central deployment.

## 6. Product Goals

1. Process real or recorded camera streams through a reliable ingestion pipeline.
2. Connect detector output to tracking, spatial rules, evidence capture, and alert persistence.
3. Protect every API, WebSocket, stream, evidence, and administrative operation.
4. Give operators clear workflows for monitoring, triage, review, export, and recovery.
5. Make system health, model status, data provenance, and degraded modes visible.
6. Establish measurable release gates for latency, accuracy, availability, and security.
7. Reduce deployment cost by reusing supported existing CCTV infrastructure instead of requiring dedicated FRS, ANPR, or smart-camera hardware.
8. Scale from a single BOP pilot to multiple sites through independent camera workers and a central alert service.

## 7. Scope

### In scope

- RTSP and local video-file ingestion.
- Multi-camera frame scheduling and bounded queues.
- YOLO inference with completed output parsing and configurable model loading for persons, vehicles, and approved threat classes.
- Persistent object tracking using a selected tracker implementation.
- Virtual fence configuration and intrusion rules.
- Face detection, with governed facial recognition as an optional controlled feature.
- ANPR plate detection and OCR with explicit unreadable handling.
- Suspicious activity rules including dwell, loitering, and configured abnormal movement.
- Night-time movement detection using camera schedule and low-light context.
- Evidence snapshots and optional pre/post event clips.
- Alert lifecycle, deduplication, acknowledgement, escalation, and audit history.
- Secure REST, WebSocket, and MJPEG/HLS access.
- PostgreSQL deployment profile with SQLite retained for local development.
- Operator, supervisor, and administrator workflows.
- Responsive dashboard, accessibility, empty states, error states, and mobile browser support.
- Automated tests, health checks, metrics, structured logs, and deployment documentation.

### Out of scope for this stage

- Fully autonomous tactical decision-making.
- Face recognition or watchlist matching without approved datasets, consent, and governance.
- Production C2 dispatch without an approved external integration contract.
- Public blockchain or cryptocurrency anchoring.
- Claims of detection accuracy in weather, terrain, or camera conditions that have not been evaluated.
- Autonomous tactical decisions or automatic use-of-force recommendations.
- Custom domain, public marketing site, fabricated reviews, or unverified product metrics.

## 8. Current-State Constraints

The next stage must explicitly preserve these truths:

- CAM-02 through CAM-04 currently use procedural OpenCV scenes.
- The browser uses TensorFlow.js COCO-SSD for CAM-01 webcam inference.
- The background rule engine currently generates periodic simulated events.
- The YOLO module loads an optional ONNX session but does not yet implement output post-processing.
- SQLite is the default database; PostgreSQL is not the active default.
- The local hash chain detects database edits but is not an independent immutable store.
- The frontend uses app-level page switching rather than URL routing.

A demo mode indicator shall be visible whenever generated streams or simulated events are active.

## 9. User Roles

| Role | Permissions |
|---|---|
| Operator | View authorized live streams, receive alerts, inspect evidence, acknowledge assigned alerts |
| Supervisor | All operator permissions, configure rules, export reports, review audit history, assign incidents |
| Administrator | All supervisor permissions, manage users, cameras, models, retention, and system settings |
| Service account | Internal ingestion and inference operations only; no interactive dashboard access |

Permissions shall be enforced server-side. Hiding a frontend control is not an authorization mechanism.

## 10. Functional Requirements

### FR-1: Camera and stream management

- FR-1.1: Administrators shall create, update, disable, and delete camera configurations.
- FR-1.2: A camera shall include a stable ID, display name, source type, source URI, location, timezone, enabled state, priority, and retention policy.
- FR-1.3: Source credentials shall be stored separately from display metadata and shall never be returned in API responses.
- FR-1.4: The system shall support local files for development and RTSP sources for pilot deployment.
- FR-1.5: Each stream shall expose connection state, last frame time, measured FPS, dropped-frame count, and last error.
- FR-1.6: A failed camera shall not block processing for other cameras.
- FR-1.7: Generated demo scenes shall be labelled as DEMO and shall not be mixed silently with real source status.

### FR-2: Ingestion and scheduling

- FR-2.1: The ingestion service shall decode frames asynchronously.
- FR-2.2: Each camera shall have a bounded queue with configurable overflow behavior.
- FR-2.3: The scheduler shall support per-camera sampling rate and maximum queue age.
- FR-2.4: Queue pressure and frame drops shall be observable through metrics and the dashboard.
- FR-2.5: The service shall reconnect with exponential backoff and a maximum retry interval.
- FR-2.6: Shutdown shall close decoder handles, queues, workers, and database sessions cleanly.

### FR-3: AI inference and tracking

- FR-3.1: The YOLO adapter shall implement model loading, tensor shape validation, confidence filtering, and non-maximum suppression.
- FR-3.2: Model classes and class IDs shall be loaded from model metadata or a versioned configuration file.
- FR-3.3: Inference errors shall be isolated to the affected frame and recorded with structured context.
- FR-3.4: The tracker shall assign stable IDs within a camera and expose bounding box, confidence, class, and last-seen time.
- FR-3.5: The system shall document that IDs are not guaranteed to persist across cameras unless cross-camera tracking is implemented and evaluated.
- FR-3.6: The AI pipeline shall expose model name, version, device, input size, inference latency, and processing FPS.
- FR-3.7: Browser inference shall remain an optional local demo capability and shall not be described as server-side CCTV inference.

### FR-4: Rules and alert lifecycle

- FR-4.1: Supervisors shall configure a virtual fence as a line or polygon per camera.
- FR-4.2: The rule engine shall evaluate tracked objects against the active rule configuration, not random event selection.
- FR-4.3: A crossing event shall be deduplicated by camera, rule, track ID, and cooldown window.
- FR-4.4: An alert shall contain source camera, event type, severity, confidence, track ID, event time in UTC, rule version, and provenance.
- FR-4.5: Alert states shall be `open`, `acknowledged`, `resolved`, or `false_positive`.
- FR-4.6: Supervisors shall be able to assign alerts and record resolution notes.
- FR-4.7: High-severity events shall require explicit acknowledgement and shall be visible until acknowledged.
- FR-4.8: Simulated alerts shall carry `provenance=simulation` and shall be filterable.

### FR-5: Evidence and retention

- FR-5.1: The system shall capture a snapshot from the source frame associated with the event.
- FR-5.2: The system should capture a configurable pre-event and post-event clip when buffering is enabled.
- FR-5.3: Evidence shall have a content hash, capture time, camera ID, alert ID, and retention expiry.
- FR-5.4: Evidence shall be encrypted at rest using a key supplied by deployment configuration or a managed secret store.
- FR-5.5: Evidence downloads shall require authorization and shall be audit logged.
- FR-5.6: Expired evidence shall be deleted by a scheduled retention worker and recorded in the audit log.
- FR-5.7: The UI shall distinguish missing evidence, unavailable evidence, and evidence still being processed.

### FR-6: API and real-time delivery

- FR-6.1: REST endpoints shall validate request bodies, query parameters, pagination, and resource ownership.
- FR-6.2: All protected REST endpoints shall reject missing, expired, malformed, or insufficient tokens.
- FR-6.3: The WebSocket endpoint shall authenticate before accepting the connection and shall close unauthorized connections with an appropriate code.
- FR-6.4: Stream endpoints shall authenticate and authorize access to the requested camera.
- FR-6.5: WebSocket messages shall include event type, schema version, event ID, server timestamp, and provenance.
- FR-6.6: The API shall provide pagination for alerts and audit logs.
- FR-6.7: The API shall provide a documented CSV export endpoint with authorization and export audit logging.
- FR-6.8: Error responses shall use a consistent structure with a machine-readable code and operator-safe message.

### FR-7: Authentication and authorization

- FR-7.1: Production startup shall fail when the JWT secret or encryption key is missing or unsafe.
- FR-7.2: Demo passwords shall not be enabled in pilot or production environments.
- FR-7.3: Passwords shall use a current adaptive password hash and account lockout/rate limiting.
- FR-7.4: Role checks shall be enforced in backend dependencies or service methods for every protected operation.
- FR-7.5: User sessions shall support expiration and revocation.
- FR-7.6: CORS shall use an explicit allowlist. Wildcard origins shall be prohibited outside local development.
- FR-7.7: Secrets shall not be committed to source control, logs, URLs, or client bundles.
- FR-7.8: Deployment shall use TLS for dashboard, API, streams, and WebSockets.

### FR-8: Dashboard workflows

- FR-8.1: The monitor shall show camera state, source type, stream health, inference state, and demo/production provenance.
- FR-8.2: Operators shall be able to filter alerts by camera, severity, type, state, provenance, and time range.
- FR-8.3: Empty, loading, offline, permission-denied, and request-failed states shall be explicit and actionable.
- FR-8.4: Mutating actions shall show success or failure feedback and shall not silently update local state when persistence fails.
- FR-8.5: The interface shall support keyboard navigation, visible focus, semantic labels, sufficient contrast, and reduced-motion preferences.
- FR-8.6: The interface shall be usable at 320px width without horizontal page overflow.
- FR-8.7: Navigation shall work with browser back/forward when URL routing is introduced.
- FR-8.8: Invalid routes shall render a custom 404 view and preserve a path back to the monitor.
- FR-8.9: Contact, privacy, and terms pages shall contain truthful project information and no fabricated claims.

### FR-9: Integrity and audit

- FR-9.1: Every alert shall receive a canonical event hash and chain position.
- FR-9.2: Ledger verification shall detect edits, deletions, missing records, duplicate sequence values, and broken links.
- FR-9.3: Ledger verification results shall identify the first broken record and verification timestamp.
- FR-9.4: Audit records shall cover login, logout, failed login, export, evidence access, review, assignment, configuration changes, and administrative actions.
- FR-9.5: Pilot deployment shall store ledger backups independently from the primary alert database.
- FR-9.6: The UI shall describe the local ledger as tamper-evident, not as a distributed blockchain.

### FR-10: Operations and observability

- FR-10.1: `/health` shall report service health, database connectivity, worker state, and model readiness separately.
- FR-10.2: A readiness endpoint shall fail until required dependencies are available.
- FR-10.3: Structured logs shall include request ID, camera ID where relevant, alert ID where relevant, and error code.
- FR-10.4: Metrics shall include stream uptime, reconnects, queue depth, dropped frames, inference latency, alert latency, WebSocket clients, and API errors.
- FR-10.5: Operators shall see a degraded-mode banner when backend, stream, model, or WebSocket services are unavailable.
- FR-10.6: The deployment guide shall document backup, restore, key rotation, migrations, and rollback.

## 11. Data Model Changes

The current `Alert` model shall be extended with:

- `state`
- `provenance`
- `rule_id`
- `rule_version`
- `source_frame_time`
- `assigned_to`
- `resolution_note`
- `resolved_at`
- `retention_expires_at`
- `evidence_hash`

New entities should include:

- `CameraCredential`
- `FenceRule`
- `ModelDeployment`
- `AlertAssignment`
- `EvidenceAsset`
- `RefreshToken` or session revocation record
- `SystemEvent`

Database migrations shall replace startup-only table creation before pilot deployment.

## 12. API Acceptance Contract

The following endpoints are required for the pilot:

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/ready` | Dependency and worker readiness |
| GET | `/cameras` | Authorized camera list |
| POST | `/cameras` | Create camera, admin only |
| PATCH | `/cameras/{id}` | Update camera, admin only |
| GET | `/cameras/{id}/stream` | Authorized stream access |
| GET | `/alerts` | Paginated, filterable alerts |
| POST | `/alerts` | Service or authorized alert creation |
| PATCH | `/alerts/{id}` | State, assignment, and resolution updates |
| GET | `/alerts/{id}/evidence` | Authorized evidence metadata |
| GET | `/alerts/export.csv` | Supervisor export with audit record |
| GET | `/ledger/verify` | Verify chain and return first failure |
| GET | `/audit-log` | Supervisor audit history |
| WS | `/ws/alerts` | Authenticated live alert delivery |

Every endpoint shall have an OpenAPI example for success and common failure responses.

## 13. Non-Functional Requirements

| Category | Pilot target |
|---|---|
| Alert latency | P95 source-frame-to-dashboard alert <= 2 seconds |
| Inference throughput | At least 10 processed FPS per stream on the supported reference machine |
| Concurrent streams | At least 4 streams without starvation or unbounded queue growth |
| Availability | 99% during an 8-hour pilot run, excluding planned restart |
| Recovery | Reconnect a failed stream within 60 seconds when the source returns |
| Data durability | No acknowledged alert lost after a service restart |
| Security | Zero critical findings in dependency, auth, and endpoint review |
| Mobile usability | No horizontal page overflow from 320px to 430px viewport widths |
| Accessibility | Keyboard-completable core workflows and no critical automated violations |
| Evidence integrity | Hash and ledger verification reproducible after restart |
| Hardware efficiency | Pilot capability must run on the named reference machine without dedicated FRS or ANPR camera hardware |
| Scale path | Architecture test demonstrates adding cameras without changing the alert, evidence, or dashboard contracts |

## 14. Testing Strategy

### Unit tests

- YOLO tensor and NMS parsing.
- Tracker lifecycle and ID behavior.
- Fence geometry and crossing direction.
- Cooldown and deduplication logic.
- Alert schema validation.
- Encryption/decryption and evidence hashes.
- Ledger append and tamper detection.
- RBAC permission matrix.

### Integration tests

- Camera failure isolation.
- Stream reconnect behavior.
- Alert persistence and WebSocket delivery.
- Authenticated stream and WebSocket rejection.
- CSV export and audit record creation.
- Database migration and restart recovery.

### End-to-end tests

- Operator receives an intrusion alert and acknowledges it.
- Supervisor exports a filtered report.
- Administrator changes a camera configuration.
- Evidence opens, downloads, and records an audit event.
- Invalid route opens the custom 404 view.
- Mobile navigation opens, closes, and reaches Contact without overflow.

### Security checks

- Dependency vulnerability scan.
- Static analysis and secret scan.
- Endpoint authorization matrix.
- Rate-limit and lockout tests.
- CORS and TLS configuration review.
- Direct database tamper and deletion verification.

## 15. Delivery Plan

### Stage 2A: Foundation and truthfulness

- Add environment validation and deployment profiles.
- Add migrations, PostgreSQL support, seed isolation, and structured configuration.
- Add explicit demo provenance and remove misleading production claims from UI and docs.
- Add API error schema, request IDs, and automated backend test scaffolding.

### Stage 2B: Real pipeline

- Implement YOLO post-processing.
- Add frame queues, scheduler, tracker, and real rule-engine inputs.
- Add stream health and reconnect workers.
- Add snapshot and clip evidence pipeline.

### Stage 2C: Security and operations

- Authenticate WebSockets and stream endpoints.
- Remove unsafe secrets and wildcard CORS in non-development environments.
- Add complete RBAC, audit coverage, rate limiting, readiness, metrics, and backups.

### Stage 2D: Operator release

- Add alert lifecycle and assignment workflows.
- Add CSV export endpoint and evidence permissions.
- Add URL routing, breadcrumbs where useful, 404 handling, and mobile QA.
- Run performance, security, accessibility, and 8-hour soak tests.

## 16. Release Gates

The pilot shall not be released until:

1. All protected endpoints pass the authorization matrix.
2. WebSocket and stream authentication are verified.
3. YOLO parsing produces tested detections from a checked-in fixture.
4. At least one real or recorded stream completes the end-to-end alert path.
5. No production environment uses default JWT secrets, demo credentials, or wildcard CORS.
6. Database migrations, backup, restore, and key configuration are documented and tested.
7. P95 latency and concurrency targets are measured on a named reference machine.
8. Mobile browser testing passes at 320px, 390px, and 430px widths.
9. All user-visible metrics identify whether they are measured, estimated, or simulated.
10. The operations team accepts the runbook and incident escalation procedure.

## 17. Decisions Required

Before implementation begins, the team must decide:

- Primary production database: PostgreSQL version and hosting model.
- Supported inference hardware and model format.
- Tracker library and license review.
- Evidence storage: local encrypted volume or object storage.
- Stream output format: MJPEG for prototype, HLS/WebRTC for pilot if needed.
- Retention periods by alert severity and evidence type.
- Approved watchlist and ANPR data governance, if those features are resumed.
- Ownership of production secrets, backups, and incident response.

## 18. Success Definition

The next stage succeeds when an authorized operator can monitor a real or recorded camera source, receive a detector-backed intrusion alert, inspect verifiable evidence, acknowledge and resolve the event, and export an auditable record. The system must remain responsive when another camera fails, must clearly expose degraded or simulated modes, and must provide measured evidence for every performance and security claim.
