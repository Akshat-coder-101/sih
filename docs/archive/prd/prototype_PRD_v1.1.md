
# Product Requirements Document (PRD)
## IBVAP – Intelligent Border Video Analytics Platform (Prototype Scope)

| | |
|---|---|
| **Document Version** | 1.1 (Prototype / Hackathon Scope) |
| **Owner** | [Team Name] |
| **Status** | Draft |
| **Scope Covered** | Tier 1 (Core) + Tier 2 (Extended) + Security/Blockchain Ledger Layer |

---

## 1. Overview

IBVAP is an AI-driven software platform that converts existing IP-based CCTV infrastructure at Border Out Posts (BOPs) and check posts into an intelligent surveillance network — without requiring dedicated FRS, ANPR, or smart-camera hardware. The platform ingests live/recorded video streams and applies computer vision models to detect people, vehicles, and boundary intrusions, then raises real-time alerts and logs events for review.

This PRD defines the requirements for the **prototype build**, limited to the following features:

**Tier 1 (Core — must-have):**
1. Human detection & tracking
2. Vehicle detection & classification
3. Virtual fence / intrusion detection
4. Real-time alert generation & event logging

**Tier 2 (Extended — should-have):**
5. Face detection (+ optional watchlist matching)
6. Automatic Number Plate Recognition (ANPR)

**Security & Trust Layer (cross-cutting — should-have):**
7. Cybersecurity controls (encrypted transport/storage, authentication, RBAC, audit trail)
8. Blockchain-based tamper-proof event ledger (hash-chain integrity for alert/evidence logs)

Suspicious activity detection, night-time enhancement, and C2 system integration (Tier 3) are explicitly **out of scope** for this version and noted only as future roadmap items.

> **Note on scope honesty:** A full permissioned blockchain network (e.g., Hyperledger Fabric) is unrealistic to stand up and secure within a hackathon timeline. This PRD scopes "blockchain" as a lightweight cryptographic hash-chain — the same tamper-evidence property a blockchain provides — with an optional stretch of anchoring to a public testnet. This keeps the claim demonstrable rather than decorative.

---

## 2. Problem Statement

Border security forces rely on manual, continuous human observation of CCTV feeds. This is labor-intensive, error-prone over long shifts, and does not scale across remote locations. Dedicated smart-camera hardware (FRS/ANPR-enabled) is expensive and difficult to deploy at scale in remote terrain. There is a need for a software-only layer that adds intelligence on top of existing camera infrastructure.

---

## 3. Goals & Objectives

- Demonstrate a working end-to-end pipeline: video ingestion → AI inference → rule-based alerting → logging → dashboard visualization.
- Prove that standard IP-CCTV footage (no special hardware) is sufficient input for meaningful analytics.
- Provide real-time, low-latency alerts for intrusion events.
- Provide a foundation architecture that can later scale to more cameras and more analytics modules (Tier 3+).

### Non-Goals (for this prototype)
- Production-grade accuracy/hardening for adversarial conditions (fog, heavy rain, camouflage).
- Multi-camera fleet management at scale (100s of feeds).
- Full integration with real command-and-control (C2) systems (a mock webhook is sufficient).

---

## 4. Target Users / Stakeholders

| User | Need |
|---|---|
| Border security personnel (control room operator) | Live dashboard, instant alerts, reduced manual monitoring load |
| Post commander / supervisor | Event history, exportable logs, situational summary |
| System integrator / procurement (evaluator) | Proof that software-only analytics work on generic CCTV, scalability story |

---

## 5. Use Cases

1. **UC-1:** An operator watches a live feed dashboard; a person is detected walking, tracked with a persistent ID and bounding box.
2. **UC-2:** A vehicle enters the frame; the system classifies it (car/truck/motorcycle) and boxes it.
3. **UC-3:** A person or vehicle crosses a pre-defined virtual boundary line/polygon; the system immediately raises a visual + logged "INTRUSION ALERT" with snapshot and timestamp.
4. **UC-4:** Every alert (intrusion, or optionally any detection) is written to an event log with timestamp, camera ID, event type, and a snapshot image, viewable later in a history panel.
5. **UC-5 (Tier 2):** A face is detected within a frame and boxed; optionally matched against a small pre-loaded watchlist and flagged if matched.
6. **UC-6 (Tier 2):** A vehicle's license plate is detected, cropped, OCR'd, and the recognized plate number is attached to that vehicle's log entry.

---

## 6. Functional Requirements

### FR-1: Video Ingestion
- FR-1.1: System shall ingest video from local file (looped, to simulate CCTV) and/or RTSP/IP camera stream.
- FR-1.2: System shall support at least 2 simultaneous camera/video sources for the demo.
- FR-1.3: Frames shall be sampled/processed at a configurable rate (e.g., every Nth frame) to balance load vs. real-time feel.

### FR-2: Human Detection & Tracking
- FR-2.1: Detect all persons in each processed frame with bounding boxes and confidence scores.
- FR-2.2: Assign a persistent tracking ID to each detected person across frames.
- FR-2.3: Maintain track continuity through brief occlusion (few frames).

### FR-3: Vehicle Detection & Classification
- FR-3.1: Detect vehicles in frame with bounding boxes.
- FR-3.2: Classify each vehicle into at least: car, truck/heavy-vehicle, motorcycle.
- FR-3.3: Assign persistent tracking ID per vehicle.

### FR-4: Virtual Fence / Intrusion Detection
- FR-4.1: Allow an operator/admin to define a virtual boundary (line or polygon) on a given camera's frame via a simple config UI or config file.
- FR-4.2: For each tracked person/vehicle, determine if its position crosses/enters the defined boundary.
- FR-4.3: On crossing, trigger an alert within ≤1–2 seconds of the crossing event.
- FR-4.4: Visually highlight the intruding object (e.g., red box) and overlay an "INTRUSION ALERT" indicator on the live feed.

### FR-5: Real-Time Alert Generation & Event Logging
- FR-5.1: Every intrusion event shall generate an alert record: {camera_id, timestamp, event_type, object_type, snapshot_image, track_id}.
- FR-5.2: Alerts shall be pushed to the dashboard in real time (WebSocket/Socket.IO or polling ≤2s).
- FR-5.3: All events shall be persisted to a database (SQLite/PostgreSQL) for later retrieval.
- FR-5.4: Dashboard shall provide a searchable/filterable event history (by camera, date range, event type).
- FR-5.5: Each alert shall have an associated snapshot thumbnail stored on disk/object storage and linked in the DB record.

### FR-6: Face Detection (Tier 2)
- FR-6.1: Detect human faces within frames where a person is present, with bounding box.
- FR-6.2 (optional/stretch): Compare detected face against a small pre-loaded watchlist (5–10 reference images) and flag a match with similarity score.

### FR-7: Automatic Number Plate Recognition (Tier 2)
- FR-7.1: Detect license plate region on a classified vehicle.
- FR-7.2: Run OCR on the cropped plate region to extract plate text.
- FR-7.3: Attach recognized plate text (and confidence) to the vehicle's event/log record.
- FR-7.4: Handle OCR failure gracefully (log as "unreadable" rather than crash/block pipeline).

### FR-8: Dashboard / UI
- FR-8.1: Live view panel showing annotated video feed(s) (boxes, IDs, labels) per camera.
- FR-8.2: Alerts panel showing real-time incoming alerts with snapshot, type, and time.
- FR-8.3: Event history/log panel with filters.
- FR-8.4: Basic camera/config management (add virtual fence, select active cameras).
- FR-8.5: Login screen; UI elements shown/hidden based on the logged-in user's role (see FR-9).
- FR-8.6: "Verify Log Integrity" action/button that runs the hash-chain check (see FR-10) and displays a pass/fail result.

### FR-9: Cybersecurity & Data Protection
- FR-9.1: All video stream transport (camera→server, server→dashboard) shall use encrypted transport (TLS 1.2+; SRTP for RTSP where feasible) — no plaintext video on the network.
- FR-9.2: Dashboard/API access shall require authentication (JWT or OAuth2), with role-based access control (RBAC) across at least three roles: Operator (view live feed + alerts), Supervisor (+ event history, exports), Admin (+ camera/fence config, user management).
- FR-9.3: Stored snapshots, event logs, and any identifying data (face crops, plate numbers) shall be encrypted at rest (AES-256).
- FR-9.4: Every user action (login, export, config change) shall write a separate audit-log entry (user, action, timestamp) distinct from the AI event log.
- FR-9.5: Login shall rate-limit/lock out after repeated failed attempts.
- FR-9.6 (deployment recommendation, not built in prototype): Camera network should sit on a segmented VLAN/VPN, isolated from general office networks — documented as a deployment guideline for real BOP rollout.

### FR-10: Blockchain-Based Tamper-Proof Event Ledger
- FR-10.1: Every alert/event record shall be hashed (SHA-256) and chained to the hash of the immediately preceding record, forming an append-only hash-chain (blockchain-style tamper-evidence) alongside the normal database entry.
- FR-10.2: Any retroactive edit to a historical event record shall be detectable — recomputing the chain will produce a hash mismatch from that point forward.
- FR-10.3: The "Verify Log Integrity" dashboard action (FR-8.6) shall walk the full chain and report whether it is intact, and if not, at which record it breaks.
- FR-10.4 (optional/stretch — time permitting): Periodically publish the latest chain hash to a public test blockchain (e.g., Ethereum Sepolia or Polygon Mumbai via `web3.py`) as an externally verifiable timestamp anchor, demonstrating tamper-evidence independent of the team's own database.

---

## 7. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Latency** | Detection-to-alert latency ≤ 2 seconds for intrusion events |
| **Throughput** | Support ≥ 2 concurrent video streams at ≥ 10 FPS processed rate on prototype hardware (single GPU or modern CPU) |
| **Accuracy (demo target)** | ≥ 80% detection recall on curated demo clips for person/vehicle detection |
| **Reliability** | Pipeline should not crash on a single frame/OCR failure — must degrade gracefully (skip/log error) |
| **Scalability (design intent, not built)** | Architecture should allow adding more camera streams / analytics modules without redesign (documented, not necessarily load-tested) |
| **Usability** | Dashboard understandable by a non-technical operator within a short walkthrough |
| **Portability** | Should run on a single machine (laptop/workstation with GPU) for demo purposes |
| **Security** | Video/API traffic encrypted in transit (TLS); stored data encrypted at rest (AES-256); RBAC enforced on dashboard; event log tamper-evidence verifiable via hash-chain check |

---

## 8. System Architecture (High-Level)

```
[CCTV / Sample Video Files / RTSP]  ── TLS/SRTP encrypted transport ──
        │
        ▼
[Frame Ingestion Layer] (OpenCV / RTSP client)
        │
        ▼
[AI Inference Module]
   ├─ Person/Vehicle Detector (YOLOv8) + Tracker (ByteTrack/DeepSORT)
   ├─ Face Detector (RetinaFace / OpenCV DNN) [+ optional face match]
   └─ Plate Detector + OCR (YOLO/Haar + EasyOCR/Tesseract)
        │
        ▼
[Rule Engine] — virtual fence boundary check on tracked object positions
        │
        ▼
[Alert Manager] — creates alert record, snapshot, pushes to dashboard
        │
        ├──▶ [Database] (SQLite/PostgreSQL, AES-256 at rest) — event & log storage
        ├──▶ [Hash-Chain Ledger] — SHA-256 chained records, tamper-evidence (+ optional testnet anchor)
        └──▶ [Auth/RBAC Layer] (JWT/OAuth2, TLS)
                    │
                    ▼
            [Dashboard Backend] (FastAPI/Flask + WebSocket)
                    │
                    ▼
            [Web Dashboard UI] (live feed, alerts, history, "Verify Integrity")
```

---

## 9. Suggested Tech Stack

| Layer | Technology |
|---|---|
| Detection | YOLOv8 (Ultralytics), pretrained on COCO (person/vehicle classes) |
| Tracking | ByteTrack or DeepSORT |
| Face Detection | RetinaFace / OpenCV DNN face detector |
| Face Matching (optional) | `face_recognition` (dlib) or InsightFace |
| Plate Detection | Small fine-tuned YOLO model or Haar cascade |
| OCR | EasyOCR or Tesseract |
| Backend / API | FastAPI or Flask + WebSocket (Socket.IO) |
| Database | SQLite (prototype) / PostgreSQL (if time allows) |
| Frontend | React or simple HTML/JS dashboard |
| Video Handling | OpenCV, FFmpeg |
| Transport Security | TLS (Nginx reverse proxy / self-signed cert for demo) |
| Auth & RBAC | JWT (e.g., `fastapi-users`/`PyJWT`) or OAuth2 |
| Encryption at Rest | AES-256 via Python `cryptography` library |
| Tamper-Proof Ledger | Custom SHA-256 hash-chain (Python) — optional stretch: `web3.py` + Ethereum Sepolia / Polygon Mumbai testnet anchor |

---

## 10. Data Requirements

- Sample/simulated CCTV footage (public surveillance-style clips or datasets like VisDrone) played on loop via OpenCV to emulate live feeds.
- 2–3 curated demo clips prepared in advance:
  - One clip: person crossing virtual boundary.
  - One clip: vehicle with clearly readable plate.
  - One clip: mixed pedestrian + vehicle scene for general detection/tracking demo.
- Small watchlist image set (5–10 sample face photos) if face-matching is included.
- No real border/operational footage required or used.

---

## 11. Success Metrics (Prototype Demo)

- End-to-end pipeline runs live without crashing for the full demo duration.
- Virtual fence intrusion correctly triggers a visible alert within target latency on the prepared clip.
- Vehicle plate correctly OCR'd on at least the curated "clean" demo clip.
- Event log correctly stores and displays all triggered alerts with snapshots.
- Dashboard clearly communicates "software-only intelligence on standard CCTV" value proposition to evaluators.
- Login enforces role-based access (e.g., an Operator account cannot reach Admin config) during the demo.
- "Verify Log Integrity" correctly reports "intact" on the untouched log, and correctly flags a deliberately edited record as tampered — proving the immutability claim live rather than just describing it.

---

## 12. Assumptions & Constraints

- Demo runs on pre-recorded/looped video rather than a live physical camera (acceptable substitute for prototype).
- Detection models used are pretrained (COCO) — no custom training pipeline required for Tier 1/2 scope.
- OCR accuracy on real-world border plates is not guaranteed; demo relies on curated, reasonably clean samples.
- Single-machine deployment; no distributed infrastructure needed for prototype.

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Low-light/poor-quality footage reduces detection accuracy | Use CLAHE/histogram equalization preprocessing on darker clips; select good demo footage |
| OCR fails on angled/dirty plates | Pre-select clean-plate demo clip as primary; show failure handling gracefully as a feature, not a bug |
| Real-time performance lag on modest hardware | Reduce processed frame rate / resolution; process every Nth frame |
| Face matching false positives with tiny watchlist | Keep face-match as a stretch/optional demo, not a core claim |
| Attempting a full blockchain network (e.g., Hyperledger) is too heavy for the timeline | Build the local SHA-256 hash-chain as the real, working deliverable; treat public-testnet anchoring as an optional stretch, never a dependency for the core demo |
| Security features get added as slideware without working code | Implement TLS + JWT/RBAC + AES-256 storage for real, even minimally, so the claim survives a technical question from judges |

---

## 14. Out of Scope (Deferred to Roadmap / Tier 3)

- Suspicious activity detection (loitering, running, abnormal behavior)
- Night-time/IR-specific movement detection beyond basic low-light preprocessing
- Real integration with existing command & control systems (mock webhook only, if shown at all)
- Multi-site, multi-hundred-camera scale deployment
- Hardened performance under adverse weather/camouflage conditions

---

## 15. Milestone Plan (Suggested)

| Phase | Deliverable |
|---|---|
| 1 | Video ingestion + YOLO detection + tracking working on sample clips |
| 2 | Virtual fence rule engine + alert trigger + snapshot capture |
| 3 | Dashboard (live feed + alerts panel) + DB logging |
| 4 | Face detection + ANPR modules integrated into pipeline |
| 5 | Security layer: TLS setup, JWT/RBAC auth, AES-256 storage encryption, hash-chain ledger + "Verify Integrity" UI action |
| 6 | Polish, curated demo clips, rehearsal, pitch deck alignment |
