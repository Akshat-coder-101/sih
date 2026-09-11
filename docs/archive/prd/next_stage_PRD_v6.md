# Product Requirements Document
## IBVAP v6: Field Validation, Governance, and Operational Readiness

| Field | Value |
|---|---|
| Document version | 6.0 |
| Status | Proposed field-readiness PRD |
| Supersedes | PRD v5 Controlled Field Pilot and Operational Scale |
| Baseline | v5 implementation with 24 backend tests and successful frontend build |
| Target outcome | Evidence-backed, governed, field-ready deployment |
| Primary owner | Team PERCEPTRONS |

## 1. Purpose

PRD v5 established the design for controlled field operation. The repository now contains multi-site entities, site-scoped authorization helpers, model lifecycle services, evaluation reporting, backup and key rotation services, C2 replay protection, governance services, and passing automated suites.

The next risk is not the absence of more features. It is whether those capabilities are persisted, enforced through actual HTTP workflows, evaluated against real labelled data, and supported by operational evidence. PRD v6 closes that gap before expansion beyond a controlled pilot.

## 2. Verified Baseline

### Verified

- v5 master suite: 8/8 passed.
- v4, v3, and v2 suites: 16/16 passed.
- Combined backend test result: 24/24 passed in the configured workspace environment.
- Frontend TypeScript and production build pass.
- Multi-site models, governance, evaluation, backup, model registry, disposition, metrics, and C2 modules exist.
- Worker-driven fixture path, bounded queues, evidence creation, ledger creation, and signed mock C2 delivery are covered by tests.

### Not yet field-verified

- Site access is assigned from persisted `SiteMembership` records rather than login-role defaults.
- Evaluation metrics are calculated from labelled media rather than seeded or simulated values.
- Model promotion and rollback survive service restart and are backed by database records.
- Face and ANPR governance decisions are enforced inside inference and evidence output paths.
- Backup manifests are independently verified before restore and all records are reconstructed.
- All claimed site-scoped routes have HTTP-level authorization tests.
- A checked-in walkthrough contains reproducible commands, outputs, versions, and limitations.
- Long-running field behavior is measured on representative hardware and network conditions.

## 3. Release Objective

Produce a field-readiness evidence package proving that one approved site can operate safely and measurably:

```text
Persisted site membership
  -> authorized camera access
  -> approved model and rule versions
  -> real labelled-data evaluation
  -> governed inference output
  -> alert and evidence lifecycle
  -> independently verified backup
  -> recoverable C2 delivery
  -> auditable operator disposition
  -> field readiness decision
```

A synthetic fixture remains a pipeline regression test only. It shall not be used as the sole basis for accuracy, cost, or field-readiness claims.

## 4. Release Classes

| Class | Meaning | Allowed use |
|---|---|---|
| Development | Local engineering with explicit demo defaults | Synthetic data and guest test access permitted |
| Test | Isolated automated environment | Deterministic fixtures and injected dependencies |
| Staging | Production-like environment | Approved test data and C2 staging only |
| Field pilot | One approved operational site | Real sources, governed capabilities, named operators |
| Production | Expansion beyond pilot | Requires field-readiness approval and support ownership |

Environment class shall be visible in `/health`, `/ready`, logs, metrics, and the operator interface.

## 5. Critical Gap Register

| ID | Gap | Priority | Exit evidence |
|---|---|---:|---|
| V6-01 | Login assigns hardcoded site scopes instead of persisted memberships | P0 | Membership CRUD and cross-site HTTP tests pass |
| V6-02 | Evaluation engine uses seeded/simulated metrics | P0 | Metrics reproduce from labelled frames and model artifact |
| V6-03 | Model registry state is not durable across restart | P0 | Promotion, rollback, and active version survive restart |
| V6-04 | Governance helpers are not proven on inference outputs | P0 | Unapproved face/plate outputs are masked or blocked end-to-end |
| V6-05 | Backup restore lacks independent manifest verification | P0 | Tampered archive is rejected before mutation |
| V6-06 | Route-level authorization coverage is incomplete | P0 | Full endpoint matrix passes with site isolation |
| V6-07 | Verification walkthrough is missing or not reproducible | P1 | Checked-in walkthrough runs from a clean environment |
| V6-08 | Field soak and network resilience evidence is incomplete | P1 | 72-hour pilot report passes operational thresholds |
| V6-09 | Key rotation and retention are not exercised against restored data | P1 | Historical evidence remains readable after rotation and restore |
| V6-10 | Operator quality feedback is not linked to model promotion gates | P1 | Promotion requires approved evaluation and feedback thresholds |
| V6-11 | Site onboarding and support workflow is not fully automated | P1 | New site reaches readiness through documented checks |
| V6-12 | Metrics and reports contain synthetic defaults | P1 | User-visible metrics identify measured, estimated, or simulated values |

## 6. Functional Requirements

### FR-1: Persisted site membership and authorization (P0)

- FR-1.1: Administrators shall create, update, suspend, and revoke site memberships.
- FR-1.2: Login shall resolve effective site access from active memberships and role policy.
- FR-1.3: A token shall contain a membership snapshot or membership version that can be invalidated after revocation.
- FR-1.4: Site access shall be checked against persisted ownership for cameras, alerts, evidence, rules, evaluations, backups, metrics, and C2 integrations.
- FR-1.5: Global administrators shall be explicitly distinguished from site-scoped administrators.
- FR-1.6: Site membership changes shall be audited with actor, target user, site, previous role, new role, and timestamp.
- FR-1.7: Cross-site resource identifiers shall not reveal unauthorized resource existence where concealment is required.

**Acceptance:** HTTP tests create two sites and memberships, issue tokens, and prove that users can access only the sites assigned to them across every protected route.

### FR-2: Durable model and rule lifecycle (P0)

- FR-2.1: Model deployments shall be persisted with artifact hash, version, class map, thresholds, device, approval, and status.
- FR-2.2: Rule sets shall be versioned and persisted per site and camera.
- FR-2.3: Promotion shall require an approved evaluation report, approver identity, reason, and change record.
- FR-2.4: Rollback shall restore a previously approved deployment without changing historical alert version fields.
- FR-2.5: Active model and rule versions shall be loaded from the database during startup.
- FR-2.6: A restart shall preserve promotion history, active versions, and audit records.
- FR-2.7: Unapproved or hash-mismatched artifacts shall not be activated.

**Acceptance:** Stage, promote, restart, query active status, roll back, and reconstruct an alert using the exact model/rule versions that produced it.

### FR-3: Real field-quality evaluation (P0)

- FR-3.1: Evaluation shall consume versioned labelled media or detection annotations rather than hardcoded metric values.
- FR-3.2: Dataset metadata shall include source, site/condition, annotation version, privacy approval, split, and checksum.
- FR-3.3: The evaluator shall calculate per-class precision, recall, F1, false-positive rate, false-negative count, confidence calibration, and latency.
- FR-3.4: Evaluation shall distinguish detection metrics from end-to-end alert metrics.
- FR-3.5: Reports shall include sample counts, evaluation configuration, model artifact hash, and generated timestamp.
- FR-3.6: Failed or incomplete annotations shall produce an invalid report, not optimistic metrics.
- FR-3.7: Synthetic fixtures shall be reported as regression fixtures and excluded from field-quality claims.

**Acceptance:** Running the same dataset, annotations, model artifact, and configuration produces the same report checksum and metrics within documented tolerance.

### FR-4: Enforced biometric and ANPR governance (P0)

- FR-4.1: Face recognition and ANPR shall require active site approval before model execution or persistence of identifying output.
- FR-4.2: Restricted mode shall disable or mask face embeddings, watchlist identities, plate text, and sensitive crops according to policy.
- FR-4.3: Governance state shall be checked in the inference pipeline, not only in API or UI code.
- FR-4.4: Approval changes shall take effect without requiring code changes and shall be audited.
- FR-4.5: Evidence created while a capability is restricted shall contain only policy-allowed data.
- FR-4.6: Watchlist and plate registries shall be versioned, access-controlled, and auditable.
- FR-4.7: Governance approval shall expire or require review according to configured policy.

**Acceptance:** The same frame produces masked output without approval, governed output with approval, and an audited denial after approval expiry.

### FR-5: Cryptographically verified backup and restore (P0)

- FR-5.1: Every archive shall contain a canonical manifest listing included records, schema version, site, key versions, and content checksums.
- FR-5.2: The manifest shall be authenticated or signed using a deployment-controlled key.
- FR-5.3: Restore shall verify archive path, manifest signature, checksum, schema compatibility, site target, and ledger integrity before database mutation.
- FR-5.4: Restore shall be atomic or use an isolated staging database followed by controlled activation.
- FR-5.5: Restore shall reconstruct evidence assets, audit records, memberships, models, rules, and delivery status.
- FR-5.6: Restore shall preserve encryption key references and support historical key versions.
- FR-5.7: Expired or tampered archives shall be rejected and logged without partial restore.

**Acceptance:** A modified archive, wrong-site archive, unsupported-schema archive, and valid archive produce distinct outcomes; only the valid archive activates.

### FR-6: Complete route and authorization contract (P0)

- FR-6.1: Every protected route shall have an HTTP or WebSocket integration test for anonymous, invalid, expired, revoked, wrong-site, insufficient-role, and valid access.
- FR-6.2: Site list, camera onboarding, streams, alerts, dispositions, evidence, exports, model lifecycle, evaluations, backups, governance, metrics, and C2 status shall be covered.
- FR-6.3: Route responses shall use consistent error codes and operator-safe messages.
- FR-6.4: WebSocket subscriptions shall receive only authorized site events.
- FR-6.5: Metrics and evaluation reports shall not leak data from unauthorized sites.
- FR-6.6: OpenAPI documentation shall match implemented request and response schemas.

**Acceptance:** The route matrix runs in CI and fails on any cross-site read/write or unauthorized operation.

### FR-7: Field resilience and operational evidence (P1)

- FR-7.1: The field profile shall run a minimum 72-hour soak with the approved camera and workload configuration.
- FR-7.2: The system shall measure CPU, memory, disk, queue age, dropped frames, worker restarts, model latency, alert latency, database latency, and C2 delivery latency.
- FR-7.3: Controlled failures shall cover camera loss, central-link loss, database restart, disk pressure, clock drift, model failure, and C2 outage.
- FR-7.4: Local alert persistence shall continue during central-link loss and synchronize after recovery without duplicates.
- FR-7.5: Operators shall receive actionable alerts for stale frames, worker crash loops, disk pressure, and governance expiry.
- FR-7.6: The field report shall record hardware, camera count, network conditions, software versions, model versions, and known limitations.

**Acceptance:** The 72-hour report meets approved availability, resource, recovery, and data-durability thresholds.

### FR-8: Evidence lifecycle, key rotation, and retention (P1)

- FR-8.1: Evidence records shall identify encryption key version, policy version, retention deadline, and access history.
- FR-8.2: Key rotation shall create new evidence under the active key while preserving decryption of retained historical evidence.
- FR-8.3: Restore shall verify evidence hashes after key rotation.
- FR-8.4: Retention cleanup shall be idempotent, auditable, and site-scoped.
- FR-8.5: Legal hold shall prevent deletion until explicitly released by an authorized supervisor.

**Acceptance:** Evidence created under multiple key versions survives backup, restore, access, retention evaluation, and approved deletion.

### FR-9: Quality feedback and promotion gates (P1)

- FR-9.1: Operators shall submit disposition reason codes and optional notes for every reviewed alert.
- FR-9.2: Quality reports shall aggregate false-positive rate, acknowledgement time, resolution time, and alert volume per camera-hour.
- FR-9.3: Model promotion shall require a report for the target operating envelope and approved feedback thresholds.
- FR-9.4: Feedback data shall be exportable for offline evaluation without automatically changing production thresholds.
- FR-9.5: Related duplicate events shall remain traceable.

**Acceptance:** A candidate model cannot be promoted without an approved evaluation report and current feedback review.

### FR-10: Verification documentation and support (P1)

- FR-10.1: Check in `walkthrough.md` or an equivalent release report.
- FR-10.2: Documentation shall state exact interpreter, dependency, database, migration, test, build, startup, health, readiness, metrics, backup, restore, and rollback commands.
- FR-10.3: Documentation shall record actual test counts, execution time, outputs, environment class, and known limitations.
- FR-10.4: Site onboarding shall include source validation, rule assignment, model approval, governance review, and operator training.
- FR-10.5: A support runbook shall define severity, owner, escalation path, recovery objective, and rollback procedure.
- FR-10.6: User-visible metrics shall be tagged measured, estimated, or simulated.

**Acceptance:** A new engineer and a trained site operator can reproduce verification and complete onboarding using only the checked-in documentation.

## 7. Data Model and API Changes

### New or extended entities

- `SiteMembership` with status, role, membership version, created/updated/revoked timestamps.
- `ModelDeployment` with artifact hash, approval status, active status, and promotion history.
- `RuleSetVersion` with site/camera ownership and activation history.
- `EvaluationDataset`, `EvaluationAnnotation`, and `EvaluationReport` with checksums.
- `GovernanceApproval` with expiry, review date, policy version, and capability scope.
- `BackupManifest` and `BackupRestoreJob` with signature, schema version, and verification result.
- `EvidenceAccessLog`, `LegalHold`, and `C2DeliveryAttempt`.

### Required endpoints

- `POST/PATCH/DELETE /api/sites/{site_id}/memberships`
- `GET /api/sites/{site_id}/memberships`
- `GET /api/models/deployments`
- `POST /api/models/{id}/promote`
- `POST /api/models/{id}/rollback`
- `POST /api/evaluation/run`
- `GET /api/evaluation/reports/{id}`
- `GET /api/governance/status`
- `POST /api/governance/approvals`
- `POST /api/system/backup`
- `POST /api/system/restore/validate`
- `POST /api/system/restore/activate`
- `GET /api/system/c2-delivery`

All endpoints must be site-scoped where applicable and must produce audit records for mutations or sensitive reads.

## 8. Test Plan

### P0

- Persisted membership authorization matrix.
- Model/rule promotion and restart persistence.
- Real labelled-data evaluation reproducibility.
- Governance masking/blocking through inference.
- Signed manifest verification and atomic restore.
- Complete route-level authorization matrix.
- Alert/evidence/ledger consistency after restart.

### P1

- 72-hour soak and failure injection.
- Key rotation, restore, retention, and legal hold.
- Model promotion based on quality feedback.
- Site onboarding and support runbook exercise.
- OpenAPI contract validation.
- Mobile and low-bandwidth browser matrix.

### Required evidence package

- Combined test output and dependency lock information.
- Route authorization report.
- Dataset card, annotation checksum, and evaluation report.
- Model promotion and rollback records.
- Backup manifest and restore report.
- Governance approval and restricted-mode report.
- 72-hour soak and failure-injection report.
- Security review and known-limitations document.
- Checked-in verification walkthrough.

## 9. Delivery Sequence

### Phase 6A: Authorization and persistence

- Implement membership-driven token scopes.
- Persist model/rule lifecycle and audit changes.
- Add route-level authorization tests.
- Establish migration and PostgreSQL field profile.

### Phase 6B: Evaluation and governance

- Replace synthetic evaluation metrics with labelled-data execution.
- Enforce governance at inference and evidence boundaries.
- Add dataset/report checksums and promotion gates.

### Phase 6C: Recovery and resilience

- Add signed manifests, preflight restore validation, and atomic activation.
- Complete key rotation, retention, legal hold, and evidence recovery.
- Run failure injection and 72-hour soak.

### Phase 6D: Field-readiness decision

- Onboard one approved site in shadow mode.
- Run monitored alerting with trained operators.
- Review quality and incident reports.
- Approve, restrict, or reject expansion based on evidence.

## 10. Definition of Done

V6 is complete only when:

1. Site access is derived from persisted memberships and cross-site route tests pass.
2. Model and rule lifecycle state survives restart and historical alerts remain reconstructable.
3. Evaluation reports are computed from approved labelled data, not seeded values.
4. Face and ANPR governance is enforced in inference, evidence, API, and UI paths.
5. Backup manifests are authenticated and restore is verified before activation.
6. Key rotation, retention, legal hold, and restored evidence are tested.
7. C2 staging delivery is replay-protected and observable through persisted attempts.
8. A 72-hour soak and controlled failure report meets approved thresholds.
9. The verification walkthrough is checked in and reproducible.
10. No unresolved P0 blocker remains.

## 11. Release Decision

The system may enter a field pilot only after all P0 requirements pass and an authorized review board approves the dataset, model operating envelope, privacy controls, backup/restore evidence, and support plan.

Expansion beyond the first site requires a new readiness decision. Passing synthetic fixtures, unit tests, or simulated evaluation metrics alone is not sufficient evidence for operational deployment.
