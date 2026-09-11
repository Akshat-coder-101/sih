# Product Requirements Document
## IBVAP: End-to-End Edge-to-Cloud Border Video Analytics Platform

| Field | Value |
|---|---|
| Document version | 1.0.0 |
| Status | Proposed implementation blueprint |
| Product domain | AI/ML, computer vision, geospatial intelligence, edge computing, full-stack web |
| Product name | Intelligent Border Video Analytics Platform (IBVAP) |
| Target release | Controlled end-to-end field pilot |
| Supersedes | Prototype and frontend-only PRDs |
| Primary owner | Team PERCEPTRONS |

## 1. Executive Summary

IBVAP transforms standard IP-based CCTV infrastructure into a software-defined surveillance and intelligence network. Edge nodes ingest RTSP camera feeds, perform low-latency computer vision, detect and track people and vehicles, evaluate configurable virtual fences, and publish lightweight event metadata through a resilient message broker.

The central platform persists events in PostgreSQL with PostGIS spatial geometry, enriches events with terrain context, produces structured tactical recommendations using approved intelligence inputs, and delivers alerts to a React command dashboard through authenticated WebSockets. Operators can inspect live camera state, alert evidence, terrain context, confidence, provenance, and recommended next actions.

The platform is decision support. It does not autonomously authorize force, dispatch personnel without human approval, or replace command procedures.

## 2. Problem Statement

Border Out Posts, check posts, border roads, and strategic installations commonly depend on conventional CCTV systems that provide live viewing and recording but require continuous human attention. Advanced capabilities such as intrusion detection, object tracking, facial recognition, and ANPR often require dedicated hardware or proprietary systems, which increases cost and complicates deployment in remote locations.

IBVAP addresses this problem by adding an AI and geospatial software layer to supported existing camera infrastructure. It reduces manual monitoring load, prioritizes actionable events, preserves evidence, and provides context for human response while tolerating intermittent connectivity and edge resource limits.

## 3. Goals

1. Reuse supported standard IP cameras without requiring dedicated FRS, ANPR, or smart-camera hardware.
2. Detect and track people and vehicles at the edge with measurable latency and resource use.
3. Detect virtual fence and zone violations using configurable spatial rules.
4. Deliver alerts reliably across intermittent edge-to-central network connections.
5. Store events as spatial records and enrich them with terrain and nearby-event context.
6. Provide concise, source-grounded tactical recommendations with human approval.
7. Give operators a responsive desktop and mobile-capable command interface.
8. Establish auditable security, privacy, model, configuration, and evidence workflows.

## 4. Non-Goals

- Fully autonomous tactical action or use-of-force decisions.
- Treating AI output as confirmed identity or intent without human review.
- Guaranteeing zero frame drops under arbitrary network or hardware load.
- Exposing or storing hidden model chain-of-thought reasoning.
- Nationwide or internet-scale deployment in the first release.
- Enabling face recognition or ANPR without legal, organizational, and privacy approval.
- Replacing existing command-and-control procedures with an unverified integration.

## 5. Personas and User Stories

### 5.1 Command Center Operator

Needs a high-signal live dashboard that makes urgent events easy to find and assess.

- As an operator, I want to see live camera health and event provenance so I know whether a feed is real, replayed, or simulated.
- As an operator, I want new alerts pushed immediately with location, evidence, and confidence so I can assess them quickly.
- As an operator, I want to acknowledge, resolve, or mark false positives with a reason so the event history remains accountable.
- As an operator, I want a map fly-to interaction when selecting an alert so I can understand its location in context.

### 5.2 Field Patrol Unit

Needs concise, mobile-friendly event details and approved dispatch information.

- As a patrol user, I want the event location, terrain conditions, nearest access route, timestamp, and evidence summary in one view.
- As a patrol user, I want the interface to work on a low-bandwidth mobile connection.
- As a patrol user, I want stale or unavailable data clearly labelled so I do not act on outdated information.

### 5.3 Supervisor

Needs quality, operational, and audit oversight.

- As a supervisor, I want to review alert dispositions and false-positive trends by site and camera.
- As a supervisor, I want to approve model, rule, governance, and integration changes.
- As a supervisor, I want to export an auditable report without exposing unauthorized site data.

### 5.4 System Administrator

Needs to operate a distributed platform safely.

- As an administrator, I want to onboard sites, cameras, edge nodes, and credentials without leaking secrets.
- As an administrator, I want to monitor CPU, memory, queue pressure, storage, connectivity, and model state.
- As an administrator, I want to roll back a model or configuration version without losing historical provenance.

## 6. Product Scope

### In scope

- Edge RTSP/video-file ingestion.
- GStreamer or OpenCV capture adapter.
- Motion filtering and configurable frame sampling.
- YOLO-family person, vehicle, and approved threat detection.
- DeepSORT, ByteTrack, or approved tracker implementation.
- Virtual line and polygon fence rules.
- Kafka or Redis Streams event transport.
- Local edge spool and chronological resynchronization.
- FastAPI REST and WebSocket services.
- PostgreSQL/PostGIS spatial event persistence.
- GIS terrain enrichment using approved GDAL/GRASS-compatible data workflows.
- Structured tactical recommendation generation using approved LLM tooling.
- React/Tailwind command dashboard with map and live alerts.
- Authentication, RBAC, site isolation, encryption, audit, retention, and observability.
- Automated unit, integration, end-to-end, security, performance, and browser tests.

### Deferred or optional

- Facial recognition/watchlist matching.
- Production ANPR recognition quality beyond a controlled approved pilot.
- Cross-camera identity tracking.
- Public blockchain anchoring.
- Full QGIS desktop integration.
- Multi-region active-active deployment.

## 7. End-to-End Architecture

```text
[IP Cameras / Recorded Files]
          |
          v
[Edge Capture: GStreamer/OpenCV]
          |
          v
[Motion Filter + Bounded Frame Queue]
          |
          v
[Edge Inference: YOLO + Tracker]
          |
          v
[Virtual Fence / Behavior Rules]
          |
          v
[Local Event Store + Broker Publisher]
          |                         \
          |                          \ network outage
          v                           v
[Kafka / Redis Streams]       [Encrypted Edge Spool]
          |
          v
[FastAPI Ingestion + Validation]
          |
          +------------------+
          |                  |
          v                  v
[PostgreSQL/PostGIS]   [GIS Enrichment Worker]
          |                  |
          +--------+---------+
                   v
       [Correlation + Recommendation Service]
                   |
          +--------+---------+
          |                  |
          v                  v
[Authenticated WebSocket] [C2 Integration Adapter]
          |
          v
[React Command Dashboard]
```

### Deployment modes

1. **Local development:** synthetic or recorded sources, SQLite-compatible test profile, local broker or in-process adapter.
2. **Staging:** production-like PostgreSQL/PostGIS, broker, approved test sources, staging C2 receiver, no real biometric data.
3. **Edge pilot:** one or more cameras connected to an edge node with local buffering and central synchronization.
4. **Central operations:** multi-site API, event store, GIS data, recommendation service, dashboard, audit, and operations tooling.

## 8. Core Domain Concepts

- **Site:** A BOP, check post, border road sector, or strategic installation.
- **Camera node:** A camera source owned by a site, with health, capability, and credential references.
- **Edge node:** Compute instance running capture, inference, tracking, rules, and local event buffering.
- **Detection:** A model output for an object in a frame.
- **Track:** A camera-scoped identity across frames with position, direction, and dwell state.
- **Rule:** Versioned spatial or temporal condition applied to tracks.
- **Alert:** A deduplicated event requiring operator assessment.
- **Evidence asset:** Encrypted snapshot, clip, or derived artifact associated with an alert.
- **Terrain context:** Versioned GIS-derived attributes near an event point.
- **Recommendation:** Structured, source-grounded response guidance requiring human review.
- **Provenance:** Origin such as `real`, `fixture`, `simulation`, `replay`, or `manual`.

## 9. Functional Requirements

### FR-1: Edge video ingestion

- FR-1.1: The edge node shall support RTSP and local recorded files through a pluggable capture adapter.
- FR-1.2: Capture shall expose source status, codec, resolution, frame rate, timestamp, reconnect count, and last error.
- FR-1.3: Capture shall use bounded per-camera queues with a documented overflow policy.
- FR-1.4: Motion filtering and frame sampling shall be configurable per camera.
- FR-1.5: A camera failure shall not stop unrelated camera pipelines.
- FR-1.6: The pipeline shall preserve the newest useful frame under overload and report dropped frames.
- FR-1.7: Source credentials shall be referenced through a secret store and excluded from logs and normal API responses.

**Acceptance:** A source disconnect, reconnect, frame decode error, and queue overload are handled without process termination, and telemetry reflects each condition.

### FR-2: Edge detection and tracking

- FR-2.1: The edge inference service shall support an approved YOLO model artifact for person and vehicle classes.
- FR-2.2: Model artifacts shall have version, checksum, class map, thresholds, device, and approval state.
- FR-2.3: Detection output shall include class, confidence, pixel box, normalized box, model version, and source-frame time.
- FR-2.4: The tracker shall assign stable camera-scoped IDs and expose direction, dwell, missed frames, and last-seen time.
- FR-2.5: Inference errors shall be isolated to the affected frame and reported as system events.
- FR-2.6: Model fallback or fixture detection shall be explicitly labelled and disabled in production mode.

**Acceptance:** A checked-in model fixture and approved model artifact produce deterministic class and coordinate results, and track IDs persist through the defined movement scenario.

### FR-3: Virtual fencing and behavior rules

- FR-3.1: Authorized users shall configure versioned line and polygon rules per camera.
- FR-3.2: Rules shall define target classes, direction, severity, cooldown, active schedule, and site ownership.
- FR-3.3: Tripwire rules shall evaluate consecutive track positions and configured direction.
- FR-3.4: Zone rules shall support entry, exit, dwell, and loiter conditions.
- FR-3.5: Rule validation shall reject invalid coordinates, unsupported classes, and unsafe thresholds.
- FR-3.6: Deduplication shall preserve related-event references instead of silently discarding context.

**Acceptance:** A deterministic crossing produces one alert within the latency target, repeated frames remain within cooldown, and unrelated cameras/tracks are independent.

### FR-4: Resilient event transport

- FR-4.1: Edge nodes shall publish validated event envelopes to Kafka or Redis Streams.
- FR-4.2: Event envelopes shall include schema version, event ID, site ID, edge node ID, camera ID, source-frame time, provenance, model version, rule version, and payload checksum.
- FR-4.3: When central transport is unavailable, events shall be written to an encrypted local spool.
- FR-4.4: The spool shall preserve chronological order, bounded storage, retry state, and idempotency keys.
- FR-4.5: Synchronization shall resume after reconnection without duplicate central alerts.
- FR-4.6: Broker retention, consumer groups, dead-letter handling, and replay policy shall be configured per environment.

**Acceptance:** A simulated network outage preserves events locally, recovery synchronizes them in order, and duplicate delivery does not create duplicate alerts.

### FR-5: Backend ingestion and persistence

- FR-5.1: FastAPI shall validate event envelopes and reject malformed or unauthorized site events.
- FR-5.2: PostgreSQL/PostGIS shall store alert location as `POINT(longitude latitude)` with SRID 4326.
- FR-5.3: The backend shall persist cameras, sites, edge nodes, detections, tracks, rules, alerts, evidence, terrain context, recommendations, audit records, and delivery attempts.
- FR-5.4: Spatial indexes shall support radius and time-window queries.
- FR-5.5: Alert creation, evidence metadata, ledger/hash record, and broker acknowledgement shall have defined transaction and retry semantics.
- FR-5.6: All alert writes shall be idempotent by event ID and source identity.

**Acceptance:** A valid edge event is persisted once, spatially queryable, retrievable by site-scoped API, and recoverable after service restart.

### FR-6: GIS terrain enrichment

- FR-6.1: The enrichment service shall query approved raster/vector datasets around the alert point.
- FR-6.2: Terrain context may include elevation, slope, land cover, vegetation density, road distance, water proximity, and data freshness.
- FR-6.3: Each terrain attribute shall include source dataset, version, coordinate reference, extraction timestamp, and confidence/quality indicator.
- FR-6.4: Missing or stale GIS data shall produce a clearly labelled partial result and shall not block alert persistence.
- FR-6.5: GIS processing shall be asynchronous for expensive operations and shall expose job status.

**Acceptance:** A known test point returns deterministic terrain attributes, and missing raster coverage results in a partial enrichment state rather than a fabricated value.

### FR-7: Correlation and tactical recommendations

- FR-7.1: The service shall correlate nearby alerts using configurable radius and time windows.
- FR-7.2: Recommendations shall be generated from structured inputs: alert facts, terrain facts, nearby-event facts, confidence, provenance, and data freshness.
- FR-7.3: The service shall return a concise recommendation, contributing factors, uncertainty, source references, and generated timestamp.
- FR-7.4: The system shall not expose or persist hidden chain-of-thought reasoning.
- FR-7.5: Recommendations shall be marked `draft`, `reviewed`, `approved`, `rejected`, or `stale`.
- FR-7.6: LLM failure, timeout, unsupported output, or prompt-injection-like source content shall not block alert creation.
- FR-7.7: The model shall not invent terrain facts, identities, coordinates, or operational capabilities absent from structured inputs.
- FR-7.8: High-impact recommendations shall require human review before display as an approved action or C2 dispatch.

**Acceptance:** Given a fixed structured input, the service produces a schema-valid recommendation with cited inputs; an unavailable LLM produces a safe fallback summary.

### FR-8: Face and ANPR governance

- FR-8.1: Face recognition and ANPR shall be disabled by default for new sites.
- FR-8.2: Activation shall require recorded legal/organizational approval, purpose, retention period, and responsible approver.
- FR-8.3: Restricted mode shall mask or discard identifying output and sensitive crops.
- FR-8.4: Watchlist and plate registries shall be versioned, access-controlled, and auditable.
- FR-8.5: Approval expiry shall disable persistence and create an operator-visible governance alert.

**Acceptance:** The same test frame produces masked output without approval, governed output with approval, and restricted output after approval expiry.

### FR-9: Alert lifecycle and evidence

- FR-9.1: Alerts shall support `open`, `acknowledged`, `escalated`, `resolved`, and `false_positive` states.
- FR-9.2: Every alert shall contain site, camera, event time, source-frame time, class, confidence, track ID, rule/model versions, location, provenance, and evidence status.
- FR-9.3: Evidence shall be encrypted at rest and associated with content hashes and key versions.
- FR-9.4: Evidence retrieval, download, retention, deletion, and legal hold shall be audited.
- FR-9.5: Operators shall provide a reason code for false positives and resolutions.
- FR-9.6: Alerts shall remain locally available when C2 or central services are unavailable.

**Acceptance:** An operator can inspect evidence, acknowledge an event, resolve it with a reason, and reconstruct the full provenance chain.

### FR-10: C2 integration

- FR-10.1: C2 integrations shall be configured per site and environment.
- FR-10.2: Outbound messages shall use a versioned schema and include event ID, site ID, alert ID, timestamp, signature, and idempotency key.
- FR-10.3: Delivery shall use bounded timeouts, retries, replay protection, and dead-letter handling.
- FR-10.4: C2 delivery shall never be required for local alert persistence.
- FR-10.5: Production dispatch shall require explicit enablement and human approval policy.

**Acceptance:** Staging receives a signed event, rejects stale or duplicate messages, and the platform retains the alert when staging C2 is unavailable.

### FR-11: Authentication, authorization, and audit

- FR-11.1: All APIs, WebSockets, streams, evidence, broker consumers, and administrative actions shall authenticate and authorize requests.
- FR-11.2: Authorization shall be site-scoped and server-side.
- FR-11.3: Roles shall include operator, supervisor, administrator, and restricted service account.
- FR-11.4: Secrets shall not use development defaults in staging or production.
- FR-11.5: JWT/session expiry, revocation, rate limiting, and failed-login lockout shall be supported.
- FR-11.6: Audit logs shall cover authentication, site membership, camera/rule/model changes, evidence access, exports, recommendations, C2 delivery, and data deletion.
- FR-11.7: Production CORS and TLS configuration shall use explicit allowlists and deployment-managed certificates.

**Acceptance:** The full authorization matrix prevents anonymous, wrong-role, wrong-site, expired-token, revoked-token, and malformed-token access.

### FR-12: Frontend command dashboard

- FR-12.1: The React dashboard shall show site/camera health, event provenance, alert state, evidence status, model/rule versions, and data freshness.
- FR-12.2: The live monitor shall display camera feeds, detection overlays, fence state, and current alert queue.
- FR-12.3: The map shall display camera nodes, alert points, selected-event fly-to behavior, severity styling, and stale-data indicators.
- FR-12.4: The alert feed shall update through authenticated WebSockets and recover from reconnects.
- FR-12.5: Alert detail shall show evidence, coordinates, terrain context, recommendation status, contributing factors, and source references.
- FR-12.6: Users shall filter alerts by site, camera, type, severity, state, provenance, model, rule, and time range.
- FR-12.7: Mobile patrol view shall prioritize location, severity, timestamp, evidence, terrain summary, and approved recommendation.
- FR-12.8: Theme toggle shall support strict light and dark modes with readable contrast.
- FR-12.9: All screens shall provide loading, empty, offline, error, forbidden, stale, and success states.
- FR-12.10: The UI shall never present simulation, replay, or draft recommendation data as live operational fact.

**Acceptance:** Browser tests pass desktop and mobile core workflows, including map selection, live alert arrival, evidence inspection, disposition, reconnect, and offline recovery.

## 10. Data Model

### Core tables

- `sites`
- `site_memberships`
- `edge_nodes`
- `cameras`
- `camera_credentials`
- `model_deployments`
- `rule_sets`
- `rule_versions`
- `detections`
- `tracks`
- `alerts`
- `alert_dispositions`
- `evidence_assets`
- `evidence_access_logs`
- `terrain_enrichments`
- `recommendations`
- `governance_approvals`
- `evaluation_datasets`
- `evaluation_reports`
- `c2_integrations`
- `c2_delivery_attempts`
- `audit_logs`
- `system_events`
- `backup_restore_jobs`

### Spatial fields

- Camera location: `geometry(Point, 4326)`.
- Alert location: `geometry(Point, 4326)`.
- Optional movement path: `geometry(LineString, 4326)`.
- Terrain coverage: dataset-specific raster/vector references, not arbitrary unverified values.

### Required integrity controls

- Unique event ID per source and site.
- Unique alert-to-evidence relationship according to evidence policy.
- Foreign-key ownership validation.
- Indexed site, camera, timestamp, severity, state, provenance, and spatial fields.
- Version fields on models, rules, recommendations, and governance approvals.

## 11. API Contract

### Authentication

- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/revoke`
- `GET /auth/me`

### Sites and cameras

- `GET /api/sites`
- `POST /api/sites`
- `GET /api/sites/{site_id}/memberships`
- `POST /api/sites/{site_id}/memberships`
- `PATCH /api/sites/{site_id}/memberships/{membership_id}`
- `GET /api/cameras?site_id=`
- `POST /api/cameras`
- `PATCH /api/cameras/{camera_id}`
- `POST /api/cameras/{camera_id}/test`
- `GET /api/cameras/{camera_id}/stream`

### Events and alerts

- `POST /api/ingest/events`
- `GET /api/alerts`
- `GET /api/alerts/{alert_id}`
- `POST /api/alerts/{alert_id}/disposition`
- `GET /api/alerts/{alert_id}/evidence`
- `GET /api/alerts/export.csv`
- `GET /api/alerts/reports/quality-feedback`

### Rules, models, and governance

- `GET /api/sites/{site_id}/rules`
- `POST /api/sites/{site_id}/rules`
- `POST /api/models/stage`
- `POST /api/models/{model_id}/promote`
- `POST /api/models/{model_id}/rollback`
- `GET /api/models/status`
- `GET /api/governance/status?site_id=`
- `POST /api/governance/approvals`

### GIS and recommendations

- `GET /api/alerts/{alert_id}/terrain`
- `POST /api/alerts/{alert_id}/enrich`
- `GET /api/alerts/{alert_id}/recommendation`
- `POST /api/recommendations/{recommendation_id}/review`
- `GET /api/evaluation/datasets`
- `POST /api/evaluation/run`
- `GET /api/evaluation/reports/{report_id}`

### Operations and integrations

- `GET /health`
- `GET /ready`
- `GET /metrics`
- `GET /api/system/events`
- `POST /api/system/backup`
- `POST /api/system/restore/validate`
- `POST /api/system/restore/activate`
- `GET /api/c2/deliveries`
- `POST /api/c2/deliveries/{delivery_id}/retry`
- `WS /ws/alerts?site_id=`

All protected endpoints require OpenAPI examples, consistent error envelopes, request IDs, site authorization, and audit behavior where appropriate.

## 12. Frontend Requirements

### Visual language

Use a restrained Watermelon Command direction:

- Graphite/charcoal workspace surfaces.
- Watermelon red for critical threat states.
- Leaf green for healthy/online states.
- Pale rind neutrals for text and dividers.
- Cyan or blue only for instrumentation, links, and selected navigation.
- No purple-dominant gradients, fabricated metrics, fake testimonials, or decorative marketing hero.

### Layout

- Desktop: sidebar, top status bar, main workspace, optional detail rail.
- Tablet: collapsible sidebar and two-column operational views.
- Mobile: drawer navigation, stacked monitor/alerts, dedicated patrol detail mode.
- Target widths: 320px, 390px, 430px, 768px, 1024px, and 1440px.
- No horizontal document overflow.

### Accessibility

- Semantic landmarks and heading hierarchy.
- Keyboard navigation and visible focus.
- Accessible names and tooltips for icon-only controls.
- Status never communicated by color alone.
- Focus-trapped dialogs with Escape handling.
- Reduced-motion support.
- WCAG 2.2 AA target for text and essential controls.

### Frontend state contract

Every network-backed surface shall support:

- `loading`
- `ready`
- `empty`
- `error`
- `offline`
- `forbidden`
- `stale`
- `saving`
- `saved`
- `save_failed`

## 13. Security and Privacy

- TLS for camera-to-edge, edge-to-broker, broker-to-backend, backend-to-dashboard, and C2 transport.
- Site-scoped RBAC on every resource and message subscription.
- Secret-provider references instead of plaintext camera credentials.
- AES-256-GCM or approved equivalent for sensitive evidence at rest.
- Versioned key rotation with historical decryption support.
- Signed event envelopes and tamper-evident alert ledger.
- Input validation and output encoding for camera metadata, GIS data, operator notes, and external event content.
- LLM prompt-injection resistance through structured tool inputs, source separation, output schema validation, and no direct execution of generated commands.
- Data minimization for face and plate artifacts.
- Configurable retention, legal hold, deletion, and access audit.
- Dependency, secret, container, API, and infrastructure security scans.

## 14. Non-Functional Requirements

| Category | Target |
|---|---|
| Edge inference | >= 15 processed FPS on named Jetson/reference hardware for approved model |
| Alert latency | P95 physical/source-frame event to dashboard <= 2.5 seconds under approved workload |
| Broker recovery | Resume synchronization within 60 seconds after link restoration |
| Scale | Pilot architecture test with 500 edge-node identities and documented capacity limits |
| Availability | >= 99% during the controlled pilot window, excluding planned maintenance |
| Queue behavior | Bounded memory and documented drop policy under overload |
| Data durability | No acknowledged alert loss during tested service, database, or broker restart |
| Recommendation reliability | Timeout/failure fallback within 2 seconds of recommendation request |
| Mobile usability | No horizontal overflow from 320px to 430px |
| Accessibility | No critical automated accessibility violations in core workflows |
| Security | No unresolved critical findings before field pilot |
| Evidence retention | Raw cropped images default to 30 days; metadata retention requires governance approval |

The 500-node target is a capacity-validation target, not a promise that one workstation can process 500 video feeds.

## 15. Testing Strategy

### Unit tests

- Frame sampling and motion filtering.
- Queue overflow, ordering, and spool recovery.
- Detector parsing, NMS, coordinate conversion, and tracker stability.
- Fence geometry, direction, dwell, cooldown, and deduplication.
- Event schema, idempotency, signatures, and error envelopes.
- PostGIS coordinate conversion and spatial queries.
- Terrain extraction adapters and partial-result handling.
- Recommendation input/output schema and fallback behavior.
- Encryption, key rotation, ledger verification, and retention rules.

### Integration tests

- RTSP/file capture to broker publication.
- Broker outage and chronological replay.
- Backend ingestion to PostGIS alert persistence.
- GIS enrichment job and missing-data behavior.
- Recommendation generation from fixed structured inputs.
- Site-scoped REST, WebSocket, stream, evidence, export, and metrics authorization.
- C2 signature, replay, retry, timeout, and dead-letter behavior.
- Database migration, backup, restore, and restart recovery.

### End-to-end tests

- Recorded camera fixture through edge capture, detector, tracker, rule, broker, backend, PostGIS, evidence, ledger, WebSocket, and dashboard.
- Operator receives and dispositions a live alert.
- Supervisor reviews feedback and exports a site-scoped report.
- Administrator onboards a camera and activates a rule/model version.
- Patrol user opens a mobile alert detail with map and terrain context.
- Governance approval enables and later restricts face/ANPR output.

### Performance and resilience tests

- Four-camera local pilot.
- Named Jetson/reference edge benchmark.
- Broker and central-link outage.
- 24-hour then 72-hour soak.
- Database restart and restore.
- Disk pressure, memory pressure, queue pressure, and clock drift.
- LLM timeout, invalid output, and unavailable GIS data.
- C2 outage and recovery.

### Frontend/browser tests

- Desktop and mobile viewports listed in the frontend requirements.
- No horizontal overflow.
- Drawer, dialogs, map fly-to, WebSocket reconnect, empty/error/offline states.
- Alert filters, disposition, export, evidence, theme toggle, and keyboard workflows.
- Lighthouse/performance checks for non-model views.

## 16. Delivery Roadmap

### Phase 1: Edge foundation

- Define event envelope and provenance contract.
- Implement capture adapters, bounded queues, motion filter, and local spool.
- Implement configured detector, tracker, and virtual fence path.
- Produce deterministic fixture and edge telemetry.

### Phase 2: Data highway and backend core

- Deploy Kafka or Redis Streams.
- Implement authenticated ingestion and idempotency.
- Introduce PostgreSQL/PostGIS and migrations.
- Implement site/camera/alert/evidence APIs and WebSocket delivery.

### Phase 3: GIS and recommendation services

- Load approved terrain datasets.
- Implement asynchronous terrain enrichment and spatial correlation.
- Implement structured recommendation service with citations, confidence, fallback, and human review.
- Add governance controls for face and ANPR capabilities.

### Phase 4: Full command dashboard

- Add map, camera nodes, alert markers, fly-to behavior, terrain panels, and recommendation review.
- Implement Watermelon Command design system and responsive patrol mode.
- Add loading, empty, stale, error, offline, permission, and success states.

### Phase 5: Pilot hardening

- Complete security review, capacity testing, soak testing, backup/restore, and incident runbook.
- Onboard one approved site in shadow mode.
- Measure quality, latency, false positives, uptime, and operator response.
- Expand only after a formal readiness decision.

## 17. Definition of Done

The end-to-end pilot is complete only when:

1. A supported RTSP or recorded source reaches the dashboard through the configured edge-to-broker-to-backend path.
2. A detector-backed event is spatially persisted in PostGIS with evidence and provenance.
3. A virtual fence crossing produces a deduplicated alert within the approved latency target.
4. Network outage and recovery preserve events without duplicate alerts.
5. GIS enrichment returns versioned terrain context or an explicit partial/unavailable state.
6. Recommendations are structured, source-grounded, reviewable, and resilient to LLM failure.
7. No hidden chain-of-thought is stored or exposed.
8. Face and ANPR outputs respect governance approval and restricted mode.
9. Site-scoped authorization prevents cross-site access on every API and WebSocket path.
10. Evidence encryption, key rotation, retention, backup, restore, and audit are verified.
11. C2 staging delivery is signed, idempotent, replay-protected, retryable, and non-blocking to local alerts.
12. The dashboard works on desktop and mobile with no horizontal overflow.
13. All P0 security, E2E, resilience, and data-integrity tests pass.
14. The release report records hardware, model, dataset, dependency versions, test results, known limitations, and approved operating envelope.

## 18. Release Gates

The pilot shall not be activated unless:

- The approved model artifact checksum matches the deployed artifact.
- The named reference hardware meets inference and latency targets.
- The representative evaluation dataset meets approved per-class thresholds.
- The full authorization matrix passes.
- Backup and restore pass in an isolated environment.
- The 72-hour soak has no unbounded resource growth or unresolved data-loss event.
- Governance approvals exist for any biometric or ANPR capability enabled at the site.
- C2 staging contract tests pass and production dispatch is explicitly approved.
- Operators complete training and the incident/runbook exercise.
- All user-visible claims identify measured, estimated, simulated, or unavailable values.

## 19. Open Decisions

Before implementation starts, decide:

- YOLO model version and licensing.
- Tracker implementation and licensing.
- GStreamer versus OpenCV as the primary capture adapter.
- Kafka versus Redis Streams as the broker.
- Celery, dedicated workers, or broker-native consumers.
- PostgreSQL/PostGIS hosting and migration tool.
- GDAL/GRASS dataset sources, refresh frequency, and coverage.
- LLM provider or local model, data boundary, cost limit, and retention policy.
- Recommendation approval policy and C2 dispatch authority.
- Supported Jetson/reference hardware.
- Camera credential and deployment secret management.
- Site retention, legal hold, privacy, and biometric governance policy.
