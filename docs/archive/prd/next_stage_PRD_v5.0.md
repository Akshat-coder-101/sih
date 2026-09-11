# Product Requirements Document
## IBVAP v5: Controlled Field Pilot and Operational Scale

| Field | Value |
|---|---|
| Document version | 5.0 |
| Status | Proposed operational PRD |
| Supersedes | PRD v4 Verified Pilot Release and Production Readiness |
| Baseline | v4 implementation with 16 backend tests passing and frontend build passing |
| Target outcome | Controlled, measurable, supportable field pilot |
| Primary owner | Team PERCEPTRONS |

## 1. Purpose

PRD v4 established the release-hardening bar for a detector-backed pilot slice. The current repository now contains a working capture-to-alert path, bounded queues, authenticated access, model registry, evidence assets, signed C2 delivery, readiness and metrics endpoints, and automated backend suites.

PRD v5 moves the product from technical pilot verification toward controlled field operation. It focuses on deployment repeatability, camera/site onboarding, model quality measurement, alert trust, privacy governance, resilience, and multi-site operations.

This PRD does not treat passing unit/integration tests as proof of field accuracy. Field release requires measured performance on representative data and documented operational controls.

## 2. Verified Baseline

The following verification was completed before this PRD:

- `test_v4_release_suite.py`: 6 tests pass.
- `test_p0_p1_suite.py`: 6 tests pass.
- `test_ibvap_pipeline.py`: 4 tests pass.
- Combined backend result: 16 tests pass.
- Frontend TypeScript and production build pass.
- Worker-driven fixture path covers capture, bounded queue, detector/fixture adapter, tracker, rules, alert, evidence, ledger, and C2 test delivery.
- WebSocket and stream authorization behavior is tested.

The field-pilot baseline still has limitations:

- The checked-in fixture uses a deterministic synthetic scene and is not representative of all BOP conditions.
- The default deployment may use a fixture/simulation detector when model weights are not configured.
- The system uses SQLite by default unless deployment configuration selects another database.
- C2 tests use a local mock receiver, not a live command system.
- Face recognition, ANPR quality, cross-camera identity, and adverse-weather performance require separate evaluation.
- Long-running soak, backup/restore, migration, and multi-site tests remain required.

## 3. Operational Outcomes

IBVAP v5 shall enable an authorized deployment team to:

1. Register a site and onboard supported cameras without source credentials leaking to operators.
2. Validate camera connectivity, stream quality, time synchronization, and model readiness before activation.
3. Run analytics continuously with bounded resource use and independent camera failure handling.
4. Present alerts with enough context for a human operator to assess and act.
5. Measure false positives, missed detections, latency, uptime, and evidence availability.
6. Upgrade models and services with rollback and no silent loss of alerts or evidence.
7. Operate multiple sites from a central view while preserving site-level authorization and auditability.

## 4. Field-Pilot Principles

- Human-in-the-loop: an alert is decision support, not an autonomous command.
- Provenance first: real, fixture, simulation, replay, and manually created events remain distinguishable.
- Quality before breadth: a small set of validated capabilities is preferable to unsupported analytics claims.
- Local resilience: a site continues buffering and recording alert metadata during central-link outages.
- Least privilege: users, services, sites, cameras, evidence, and integrations receive only required access.
- Reversible change: model, rule, and configuration changes are versioned and rollbackable.
- Evidence-based operations: every field claim has a dataset, environment, measurement period, and owner.

## 5. Scope

### In scope

- Site and camera onboarding workflow.
- Camera health validation and stream-quality checks.
- Production deployment profile using PostgreSQL and versioned migrations.
- Model and rule version management.
- Evaluation datasets, quality dashboards, and operator feedback labels.
- Alert prioritization, assignment, escalation, and resolution reporting.
- Evidence retention, export, backup, restore, and key rotation procedures.
- Multi-site tenancy and site-scoped authorization.
- C2 integration configuration, delivery monitoring, and replay protection.
- 24-hour soak testing and controlled failure exercises.
- Deployment runbook, incident response, training, and support procedures.

### Out of scope

- Autonomous tactical response or use-of-force decisions.
- Unvalidated facial recognition deployment.
- Nationwide or internet-scale deployment.
- Public marketing claims based on synthetic benchmark data.
- Public blockchain anchoring.
- Automatic model retraining from operator feedback without review and approval.

## 6. Release Blockers

| ID | Blocker | Priority | Exit evidence |
|---|---|---:|---|
| V5-01 | No representative field evaluation dataset | P0 | Approved dataset with labelled scenarios and governance record |
| V5-02 | Simulation and real model modes can be confused operationally | P0 | Deployment banner, API provenance, and readiness policy are verified |
| V5-03 | PostgreSQL, migration, backup, and restore path is unproven | P0 | Clean install, upgrade, backup, and restore test passes |
| V5-04 | Multi-site authorization is not defined | P0 | Site/camera/evidence authorization matrix passes |
| V5-05 | Long-running resource and failure behavior is unmeasured | P0 | 24-hour soak and controlled failure report passes |
| V5-06 | Model quality and false-positive rates are not reported | P0 | Per-class precision/recall and alert-rate report is approved |
| V5-07 | C2 integration is only validated against a mock receiver | P1 | Contract test, staging receiver, and replay-protection evidence |
| V5-08 | Operator feedback is not connected to quality reporting | P1 | Review labels produce measurable false-positive and resolution reports |
| V5-09 | Model/rule/config changes lack approval and rollback | P1 | Versioned change workflow and rollback test pass |
| V5-10 | Evidence retention and key rotation are not operationally exercised | P1 | Retention, restore, rotation, and access audit report passes |
| V5-11 | No site onboarding or support runbook | P1 | New site can be onboarded by a trained operator using the runbook |
| V5-12 | Mobile/low-bandwidth behavior is not field-tested | P2 | Bandwidth and device matrix is documented and accepted |

## 7. Functional Requirements

### FR-1: Site and camera onboarding (P0)

- FR-1.1: Administrators shall create a site with identity, region, timezone, connectivity profile, and retention policy.
- FR-1.2: Administrators shall add cameras with source type, URI reference, location, capabilities, and site ownership.
- FR-1.3: Camera credentials shall be stored in a secret provider or encrypted credential store and excluded from normal API responses.
- FR-1.4: Onboarding shall validate source reachability, frame dimensions, FPS, timestamp behavior, and supported codec.
- FR-1.5: A camera shall not enter active analytics state until health checks and a rule/model assignment pass.
- FR-1.6: Onboarding shall provide a safe test pattern or recorded source when no live camera is available.

**Acceptance:** A new site can be created, a camera tested, a rule assigned, and the camera activated without exposing credentials or producing an unlabelled simulation stream.

### FR-2: Multi-site tenancy and authorization (P0)

- FR-2.1: Every camera, alert, evidence asset, rule, audit record, and integration shall have site ownership where applicable.
- FR-2.2: Users shall be granted site-scoped roles in addition to global role class.
- FR-2.3: Operators shall not read, stream, acknowledge, export, or retrieve evidence from an unauthorized site.
- FR-2.4: Service accounts shall be restricted to assigned sites and camera workers.
- FR-2.5: Authorization decisions shall be server-side and tested for cross-site leakage.
- FR-2.6: Audit records shall include site ID and authorization subject.

**Acceptance:** Cross-site access tests fail for REST, WebSocket, stream, evidence, export, rules, and metrics endpoints.

### FR-3: Model and rule lifecycle (P0)

- FR-3.1: Each model deployment shall have name, version, artifact hash, class map, thresholds, device, and approval status.
- FR-3.2: Each camera shall identify its active model deployment and rule-set version.
- FR-3.3: Model and rule changes shall be staged, reviewed, approved, activated, and rolled back independently.
- FR-3.4: Inference events shall include model version and rule version for later reconstruction.
- FR-3.5: A missing, invalid, or unapproved model shall prevent production activation.
- FR-3.6: Simulation and replay adapters shall be explicit deployment choices and visible in readiness and UI.

**Acceptance:** A model or rule can be promoted and rolled back while existing alerts retain the versions that generated them.

### FR-4: Field-quality evaluation (P0)

- FR-4.1: Create an approved evaluation dataset representing day/night, weather, camera angles, occlusion, distance, network degradation, people, and vehicle scenarios.
- FR-4.2: Store dataset provenance, annotation version, privacy approval, and evaluation split.
- FR-4.3: Report precision, recall, false-positive rate, false-negative review rate, confidence calibration, and latency by class, site, camera, and condition.
- FR-4.4: Report alert volume per camera-hour and operator acknowledgement rate.
- FR-4.5: Separate detector metrics from end-to-end alert metrics.
- FR-4.6: Quality reports shall identify confidence intervals or sample counts where meaningful.
- FR-4.7: No model shall be promoted based only on the synthetic crossing fixture.

**Acceptance:** The pilot quality report is reproducible from versioned data and identifies approved operating conditions and known failure modes.

### FR-5: Alert operations and feedback (P1)

- FR-5.1: Alerts shall support open, acknowledged, resolved, false-positive, and escalated states.
- FR-5.2: Operators shall record a disposition and optional reason code when resolving an alert.
- FR-5.3: Supervisors shall view alert-rate, false-positive, acknowledgement-time, and resolution-time reports.
- FR-5.4: Feedback shall be exportable for reviewed model evaluation without automatically changing production thresholds.
- FR-5.5: High-severity alerts shall support escalation targets, acknowledgement deadlines, and missed-acknowledgement notifications.
- FR-5.6: Alert deduplication shall preserve related-event links rather than silently discarding context.

**Acceptance:** A supervisor can trace an alert from source frame through disposition and include the outcome in a quality report.

### FR-6: Evidence, retention, and recovery (P0)

- FR-6.1: Evidence assets shall have lifecycle state, content hash, capture metadata, owner site, retention deadline, and encryption-key reference.
- FR-6.2: Retention policies shall be configurable by site, severity, and asset type.
- FR-6.3: Backup shall include alerts, ledger records, audit records, rules, model metadata, and evidence metadata.
- FR-6.4: Restore shall verify ledger, evidence hashes, foreign-key relationships, and authorization metadata.
- FR-6.5: Key rotation shall preserve access to retained evidence through versioned key references.
- FR-6.6: Deletion and expiry shall be auditable and irreversible after policy confirmation.

**Acceptance:** A backup is restored into an isolated environment and passes integrity, evidence, and access tests.

### FR-7: C2 staging and delivery (P1)

- FR-7.1: Integrations shall be configured per site with endpoint, signing key reference, schema version, timeout, retry, and delivery policy.
- FR-7.2: Staging and production endpoints shall be separate and visibly labelled.
- FR-7.3: Each delivery shall include event ID, site ID, alert ID, timestamp, signature, idempotency key, and schema version.
- FR-7.4: Delivery status shall be persisted as pending, delivered, retrying, failed, or dead-lettered.
- FR-7.5: Replay protection shall reject stale timestamps and duplicate event IDs according to policy.
- FR-7.6: Integration failure shall never delete or hide the local alert.

**Acceptance:** Staging delivery passes signature, timeout, retry, duplicate, stale-event, and recovery tests before production enablement.

### FR-8: Reliability and observability (P0)

- FR-8.1: The system shall run a 24-hour soak with configured camera count and representative workload.
- FR-8.2: Metrics shall include CPU, memory, disk, queue depth, frame age, dropped frames, worker restarts, model latency, alert latency, and integration status.
- FR-8.3: Alerts shall be raised for disk pressure, clock drift, stale frames, worker crash loops, model failure, and database connectivity loss.
- FR-8.4: A failed camera or site link shall not interrupt unrelated sites.
- FR-8.5: Restart recovery shall preserve alert ordering, evidence references, and audit continuity.
- FR-8.6: Operators shall have a site-level degraded-mode view.

**Acceptance:** The soak report contains no unbounded queue or memory growth, and controlled failures produce expected recovery and notifications.

### FR-9: Deployment and support operations (P1)

- FR-9.1: Provide repeatable deployment artifacts for development, staging, edge site, and central service profiles.
- FR-9.2: Provide database migration, rollback, backup, restore, secret rotation, and model promotion commands.
- FR-9.3: Provide a site onboarding checklist and camera troubleshooting guide.
- FR-9.4: Provide incident severity definitions, escalation contacts, and recovery objectives.
- FR-9.5: Record release version, configuration version, model versions, and migration revision in the system status.
- FR-9.6: Every production change shall have an owner, approval, timestamp, and rollback plan.

**Acceptance:** A trained operator can deploy a staging site, restore it, rotate a secret, and roll back a model using only the runbook.

### FR-10: Privacy and governance (P0)

- FR-10.1: Site activation shall record legal/organizational approval for face, plate, and evidence processing.
- FR-10.2: Face and plate data shall have purpose limitation, access controls, retention limits, and deletion workflows.
- FR-10.3: Watchlist changes shall be approved, versioned, audited, and reversible.
- FR-10.4: The system shall support masking or disabling face/plate capture where policy requires.
- FR-10.5: Operators shall see a notice when a capability is unavailable, disabled, or operating in a restricted mode.
- FR-10.6: Model and dataset access shall be audited separately from alert review access.

**Acceptance:** Governance approval, restricted-mode, access, retention, and deletion tests pass before biometric or ANPR features are enabled.

## 8. Data and API Changes

Required entities or extensions:

- `Site` and `SiteMembership`
- `CameraCredentialReference`
- `ModelDeployment` and `ModelPromotion`
- `RuleSetVersion`
- `AlertDisposition` and `AlertEscalation`
- `EvidenceRetentionPolicy`
- `C2Integration` and `C2DeliveryAttempt`
- `EvaluationDataset` and `EvaluationReport`
- `BackupRestoreJob`
- `ReleaseRecord`

Required API capabilities:

- Site-scoped camera, alert, evidence, rule, metrics, and audit queries.
- Model/rule promotion and rollback endpoints.
- Evaluation report retrieval.
- Backup/restore job status.
- C2 delivery status and retry inspection.
- Site onboarding health checks.

All new endpoints require OpenAPI examples, authorization tests, audit behavior, and documented error codes.

## 9. Test and Evidence Plan

### P0 release tests

- Cross-site authorization matrix.
- Production configuration and secret validation.
- Model approval and readiness transitions.
- Real recorded-source E2E path with approved model artifact.
- Queue, memory, disk, and frame-age soak tests.
- Database migration, backup, restore, and ledger verification.
- Worker, database, network, and C2 failure isolation.
- Evidence encryption, retention, key rotation, and deletion.
- Clock drift and stale-frame detection.

### P1 release tests

- C2 staging contract, signature, retry, replay, and idempotency tests.
- Alert disposition and feedback reporting.
- Model/rule promotion and rollback.
- Site onboarding workflow.
- Operator runbook exercise.
- Accessibility and mobile/low-bandwidth browser matrix.

### Required evidence package

- Combined test output with interpreter and dependency versions.
- Field evaluation dataset card and annotation report.
- Performance and latency report.
- 24-hour soak report.
- Authorization review.
- Backup/restore report.
- Model and rule promotion record.
- C2 staging contract report.
- Known limitations and approved operating envelope.

## 10. Delivery Sequence

### Phase 5A: Deployment foundation

- Add site tenancy and scoped authorization.
- Establish PostgreSQL and migrations as the field profile.
- Add backup/restore and secret/key rotation procedures.
- Add deployment and support runbooks.

### Phase 5B: Quality and governance

- Build approved field dataset and evaluation tooling.
- Add model/rule registry approval workflow.
- Add operator disposition and quality feedback reporting.
- Define face/plate governance and restricted modes.

### Phase 5C: Reliability and integrations

- Add 24-hour soak automation and failure injection.
- Add C2 staging integration, delivery persistence, and replay protection.
- Add site-level health, resource alerts, and recovery workflows.

### Phase 5D: Controlled field pilot

- Onboard one approved site.
- Run shadow mode before alerting operators.
- Measure quality and operational metrics.
- Review incidents weekly and approve or reject promotion.
- Expand only after exit criteria pass.

## 11. Definition of Done

V5 is complete only when:

1. At least one approved site operates with site-scoped authorization.
2. Production uses versioned migrations, documented backups, and tested restore.
3. Real model mode and simulation mode are visibly and technically distinct.
4. An approved representative dataset produces a reproducible quality report.
5. A 24-hour soak passes with bounded resource use and failure recovery.
6. Evidence retention, key rotation, restore, and deletion are verified.
7. C2 staging delivery is real, signed, retryable, idempotent, and observable.
8. Model, rule, and configuration changes are approved and rollbackable.
9. Operators can disposition alerts and supervisors can review quality trends.
10. Privacy and biometric/ANPR governance approvals are recorded before enablement.
11. The full evidence package is attached to the release record.
12. No unresolved P0 blocker remains.

## 12. Success Metrics

Metrics must be reported by site, camera, model version, and operating condition where possible:

- >= 99% service availability during the field pilot window.
- >= 99% alert persistence across planned restarts and tested outages.
- P95 source-frame-to-dashboard alert latency <= 2 seconds under approved workload.
- Zero unauthorized cross-site reads or writes.
- Zero unbounded queue or memory growth during the 24-hour soak.
- 100% of production exports and evidence accesses represented in audit logs.
- 100% of production alerts include model/rule version and provenance.
- C2 delivery status visible for 100% of high-severity alerts.
- Quality thresholds approved separately for each detector class and site condition.

## 13. Release Decision

The field pilot may expand beyond the first approved site only after the P0 test matrix, quality report, governance review, backup/restore exercise, and 24-hour soak are complete. Synthetic fixture success, passing unit tests, or a successful mock C2 request alone are insufficient evidence for field expansion.
