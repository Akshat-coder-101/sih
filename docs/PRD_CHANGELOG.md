# IBVAP Product Requirements Document (PRD) Changelog & Evolution History

## 1. Document Control & Evolution Matrix

| Version | Release Title / Focus | Source Document | Status | Key Architectural Evolution |
|---|---|---|---|---|
| **v1.1** | Prototype / Hackathon Scope | `prototype_PRD.md` | Archived | Initial SIH prototype scoping; defined Tier 1 (Core), Tier 2 (Extended), Tier 3 (Future); lightweight local SHA-256 hash chain for auditability. |
| **v1.0.0** | Full Edge-to-Cloud Platform Blueprint | `ibvap_full_prd_v1.md` | Archived | Enterprise blueprint; PostGIS spatial database, edge ingestion nodes, message broker (Kafka/RabbitMQ), terrain context enrichment, tactical recommendations, legal holds, C2 webhooks. |
| **v2.0** | Secure Multi-Camera Operations Platform | `next_stage_PRD.md` | Archived | Shifted prototype toward multi-camera support; per-camera queues; direction-aware intrusion rules; AES-256-GCM encryption of sensitive fields; versioned C2 adapter. |
| **v3.0** | Critical Gap Closure & Pilot Hardening | `next_stage_PRD_v3.md` | Archived | Critical gap register (G-01 to G-04); bounded frame queues to prevent memory leaks; true worker-to-detector path; authenticated WebSocket/stream access; truthful readiness reporting. |
| **v4.0** | Verified Pilot Release & Production Readiness | `next_stage_PRD_v4.md` | Archived | Established deterministic verification baseline; verified capture -> bounded queue -> YOLO ONNX -> tracker -> fence rules -> evidence -> ledger -> WebSocket pipeline with 10 unit tests. |
| **v5.0** | Controlled Field Pilot & Operational Scale | `next_stage_PRD_v5.md` | Archived | Multi-site tenancy (`SiteMembership`); camera credential isolation; model registry (`ModelDeployment`, `ModelPromotion`); evaluation datasets & reporting; backup/restore with key rotation. |
| **v6.0** | Field Validation, Governance & Operational Readiness | `next_stage_PRD_v6.md` | Archived | Field readiness evidence package; persisted site memberships; real labelled-data evaluation; mandatory governance approvals (`GovernanceApproval`) for face/ANPR; auditable operator disposition tracking (`AlertDisposition`). |
| **Frontend v1.0** | Watermelon Command Center Experience | `next_stage_PRD_frontend_v1.md` | Archived | Comprehensive frontend redesign; "Watermelon Command" dark palette; signal hierarchy; accessibility (WCAG AA); responsive desktop/tablet/mobile layouts; Leaflet geospatial integration. |
| **Dynamic Data v1.0** | Dynamic Operations Data Hardening | `dynamic_data_prd.md` | Archived | Eliminated hardcoded `cam-1` assumptions; data-driven metrics from `/metrics`; honest simulation vs detector provenance labels; graceful degradation and explicit empty states. |
| **Blockchain v1.0** | Advanced Blockchain Integrity Layer | `advanced_blockchain_features_prd.md` | Archived | Deterministic Merkle inclusion proofs (`/alerts/{id}/merkle-proof`); cryptographic AI model & rule provenance hashing; 2-of-3 multisignature threshold governance (`IBVAP_ANCHOR_PROPOSAL_V1`); EVM smart contracts (`ILedgerAnchor`, `LedgerAnchor`). |
| **Current (v7.0 Canonical)** | Unified Authoritative Product PRD | `docs/PRODUCT_PRD.md` | **Active** | **Consolidated Single Source of Truth.** Integrates all core video analytics, multi-site security, governance, tactical intelligence, dynamic data hardening, and 3-tier cryptographic integrity into one definitive specification. |

---

## 2. Detailed Evolution Analysis

### Stage 1: Prototype Inception (v1.1 & Full Blueprint v1.0.0)
- **Initial Baseline**: The initial hackathon prototype (`prototype_PRD.md`) demonstrated client-side inference, simulated CCTV generators, and a local SHA-256 hash chain to prove that commodity CCTV cameras could be augmented with AI software without smart hardware.
- **Enterprise Blueprint (`ibvap_full_prd_v1.md`)**: Extended the vision to edge-to-cloud border operations with terrain intelligence, PostGIS spatial models, and tactical recommendations. 
- **Evolutionary Tension**: The blueprint assumed heavy cloud infrastructure (PostgreSQL/PostGIS, Kafka), while field edge deployments required lightweight, resilient local operation (SQLite / embedded edge runtime).

### Stage 2: Multi-Camera Architecture & Hardening (v2.0 & v3.0)
- **Multi-Camera Ingestion**: Added `capture_worker.py` to ingest real RTSP streams and video files concurrently.
- **Bounded Queuing**: Solved memory leaks and latency lag by implementing drop-oldest bounded frame queues (`maxsize=30`) per camera.
- **Security Baseline**: Added AES-256-GCM authenticated encryption for sensitive database fields (`detail_enc`, `snapshot_enc`, `coords_enc`). Enforced JWT bearer token authentication across API endpoints and WebSockets.

### Stage 3: Verification, Multi-Site & Governance (v4.0, v5.0, v6.0)
- **Verified Execution Path**: Replaced procedural demo paths with true runtime pipelines connecting capture workers, YOLO ONNX inference, CentroidTracker, virtual tripwire/polygon rules, encrypted evidence creation, local ledger commits, and authenticated WebSocket broadcasts.
- **Multi-Site Scoping**: Added `sites`, `users`, and `site_memberships` tables. Enforced strict site-level authorization preventing cross-border-post data leakage.
- **Model Registry & Governance**: Added `ModelDeployment`, `ModelPromotion`, and `GovernanceApproval` models. Strict governance gating enforced: face recognition and ANPR are disabled by default until explicit legal approval records are active.
- **Auditable Dispositions**: Added `alert_dispositions` tracking operator triage (`acknowledged`, `resolved`, `false_positive`) with mandatory reason codes and justification notes.

### Stage 4: UX & Data Hardening (Frontend v1.0 & Dynamic Data v1.0)
- **Watermelon Command Palette**: Established a calm, high-contrast operational aesthetic (dark graphite `#0f1216`, melon red threat tones, fresh leaf green operational tones, and cyan instrumentation).
- **Decoupling from Hardcoded Assumptions**: Eliminated all coupling to `cam-1`. All camera views, video surfaces, overlays, and alert dialogs dynamically resolve to the selected camera record.
- **Simulation Honesty**: Enforced strict provenance tags (`detector`, `simulation`, `fixture`, `replay`). Synthetic simulation events are visibly branded and prohibited from masquerading as live detector alerts.

### Stage 5: Advanced Blockchain Integrity Layer (Blockchain v1.0)
- **Three-Tier Cryptographic Architecture**:
  1. *Tier 1 (Local)*: Append-only local SHA-256 hash chain.
  2. *Tier 2 (Merkle & Provenance)*: Deterministic Merkle tree inclusion proofs (`/alerts/{id}/merkle-proof`) allowing O(log N) verification of individual alerts without full ledger scans; canonical AI model and rule configuration hashing.
  3. *Tier 3 (External Anchoring)*: External EVM smart contract commitments (`ILedgerAnchor`, `LedgerAnchor`) governed by 2-of-3 multisignature threshold consensus (`IBVAP_ANCHOR_PROPOSAL_V1`).
- **Privacy by Design**: Strictly off-chain privacy guarantees. No surveillance footage, coordinates, images, or credentials ever touch the blockchain.

---

## 3. Decisions & Conflict Resolutions Summary

1. **Database Strategy**:
   - *Conflict*: v1.0.0 blueprint specified PostgreSQL/PostGIS; prototype and v2-v6 used SQLite.
   - *Resolution*: Dual-mode architecture. SQLite is the default edge/pilot engine; PostgreSQL + PostGIS schema is retained for central multi-site deployments with identical SQLAlchemy ORM interfaces.
2. **Blockchain Implementation**:
   - *Conflict*: Prototype PRD warned against full distributed blockchain networks; Advanced Blockchain PRD implemented smart contracts and EVM providers.
   - *Resolution*: External anchoring is decoupled and fail-safe. IBVAP operates completely self-sufficiently without blockchain dependencies; when enabled, commitments are published as lightweight 32-byte cryptographic hashes via standard JSON-RPC to EVM testnets (Sepolia/Base) or in-memory mock providers.
3. **AI Model Execution & Weapon Detection**:
   - *Conflict*: Documentation referenced client-side TensorFlow.js knife detection, while v2-v6 PRDs emphasized backend YOLOv8 ONNX workers.
   - *Resolution*: Both are officially codified. Backend YOLOv8 ONNX processes all multi-camera CCTV streams (COCO classes including person, vehicle, and weapon/knife); client-side TensorFlow.js provides an instant operator webcam check and demonstration utility.
4. **Governed Capabilities (Face & ANPR)**:
   - *Conflict*: Prototype Tier 2 listed face and plate recognition as "should-have"; v5/v6 restricted them due to legal/privacy concerns.
   - *Resolution*: Categorized as **Governed Features**. Fully supported in architecture, but hard-gated at runtime behind active `GovernanceApproval` records.

---

## 4. Archive Index

All original PRD versions are archived in `docs/archive/prd/`:
- `prototype_PRD_v1.1.md`
- `ibvap_full_prd_v1.0.md`
- `next_stage_PRD_v2.0.md`
- `next_stage_PRD_v3.0.md`
- `next_stage_PRD_v4.0.md`
- `next_stage_PRD_v5.0.md`
- `next_stage_PRD_v6.0.md`
- `next_stage_PRD_frontend_v1.0.md`
- `dynamic_data_prd_v1.0.md`
- `advanced_blockchain_features_prd_v1.0.md`
