# IBVAP — Intelligent Border Video Analytics Platform
## System Documentation & Architecture Guide

Welcome to the **IBVAP** (Intelligent Border Video Analytics Platform) documentation. This document explains how the platform operates, how AI detections work (including knife and suspicious activity detection), and breaks down each system component in an easy-to-understand way.

---

## 1. What is IBVAP?

**IBVAP** is an AI-powered surveillance and border monitoring command center. It turns regular CCTV and camera feeds into an intelligent perimeter security network that:
- Detects unauthorized border crossings (**Virtual Tripwire / Intrusion**)
- Flags weapons, blades, and suspicious objects (**Knife & Threat Detection**)
- Tracks individuals lingering near sensitive perimeters (**Loitering Analysis**)
- Recognizes license plates (**ANPR**) and matches faces against surveillance databases (**Watchlist**)
- Stores evidence securely with **AES-256-GCM encryption** and a **SHA-256 blockchain-style audit ledger** to prevent tampering

---

## 2. How the System Works (In Plain English)

Think of IBVAP as a digital security team with three main parts working together:

```
[ Camera Feeds ] ───▶ [ AI Inference Layer ] ───▶ [ Security & Ledger ] ───▶ [ Tactical Command UI ]
   (Webcam/CCTV)         (Detects Objects/Rules)       (AES Encrypt & Hash)       (Real-Time Alerts)
```

1. **Video Ingestion:**
   Cameras positioned along the border (or your local computer webcam) continuously stream video frames to the system.
2. **AI Object Detection:**
   Every frame is inspected in real time to locate people, vehicles, license plates, and prohibited objects (knives, blades, and weapons).
3. **Rule & Perimeter Evaluation:**
   The system tests detections against virtual boundaries. For example:
   * Did a person cross the 72% depth line? $\rightarrow$ **Intrusion Alert**
   * Has a person stayed stationary for more than 4 seconds? $\rightarrow$ **Loitering Alert**
   * Is a person holding a blade or weapon? $\rightarrow$ **Threat Alert**
4. **Encrypted Evidence & Cryptographic Ledger:**
   When an alert is triggered, a full-resolution snapshot is captured. The snapshot and event details are encrypted with **AES-256-GCM** before touching disk. The event is chained into a **SHA-256 ledger** so no record can be deleted or secretly edited.
5. **Real-Time Operator Alerting:**
   The event immediately appears on the operator's dashboard via WebSockets with an audible chime, red visual alert, and GPS coordinates.

---

## 3. Weapon & Suspicious Activity Detection

### A. Knife & Weapon Detection
* **Real-Time Webcam Detection (CAM-01):**
  Uses **TensorFlow.js COCO-SSD** running client-side inside the browser. When an operator points a knife (or testing proxy like scissors) at the camera, the AI immediately flags the class `knife`, draws a red bounding box, and creates a **Critical Threat Alert** with a forensic snapshot.
* **Instant Demo Shortcut:**
  Press the **`K`** key on your keyboard or click the **`Demo Threat [K]`** button in the top navigation bar to trigger an instant knife detection event for presentations.
* **Backend YOLOv8 Engine:**
  The backend includes a **YOLOv8 ONNX** detector configured with 80 classes, including class `43` (`knife`), for server-side CCTV stream analysis.

### B. Suspicious Activities Monitored

| Suspicious Activity | How It Works | Priority Level |
| :--- | :--- | :--- |
| **Virtual Fence Intrusion** | Monitors an invisible perimeter line at 72% depth. When an individual crosses, a breach warning triggers. | **Critical (High)** |
| **Loitering / Dwell Timer** | Uses centroid tracking to measure stationary time. If someone remains in one sector for $\ge 4$ seconds, an alert is raised. | **Warning (Medium)** |
| **Watchlist Matching** | Compares detected persons against a database of flagged individuals of interest. | **Critical (High)** |
| **ANPR Vehicle Flag** | Scans vehicle license plates at border checkpoints against a stolen/flagged vehicle registry. | **Warning (Medium)** |
| **Night / Infrared Anomaly** | Enhances low-light streams and flags infrared motion anomalies. | **Info / Low** |

---

## 4. Website Components Breakdown

The user interface is divided into clean, focused operational modules:

### 1. Tactical Live Monitor (`LiveMonitor`)
* **Live Viewport:** Displays the selected camera feed with tactical corner reticles, virtual tripwires, OSD overlays (GPS, timestamps), and live AI bounding boxes.
* **Real Webcam Support:** Switch to `CAM-01` to enable live video from your laptop webcam with in-browser AI detection.
* **Alerts Panel:** Right-hand sliding panel showing incoming alerts in real time with quick filters and sound notifications.

### 2. Camera Grid (`CameraGrid`)
* **2x2 Multi-Feed Wall:** Displays all configured tactical cameras (`CAM-01` through `CAM-04`) simultaneously on one screen.
* Clicking any camera immediately opens a focused, full-screen view.

### 3. Alerts Log (`AlertsLog`)
* **Search & Filters:** Filter events by severity (Critical, Warning, Info), camera source, and detection type.
* **Verify Log Integrity:** Validates the SHA-256 hash chain to prove that no alert has been tampered with or modified in the database.
* **Export CSV:** Exports filtered tactical events for incident reports (available to Supervisor and Admin roles).

### 4. Operational Analytics (`Analytics`)
* **Threat Distribution Donut:** Visual breakdown of incident types (Intrusion, Weapons, Loitering, etc.).
* **Incidents per Camera Bar Chart:** Identifies high-activity border sectors requiring reinforcement.
* **System KPIs:** Real-time uptime stats, alert volume, and average inference latency (~14ms).

### 5. AI Inference Pipeline (`AiPipeline`)
* Diagnostic view of all cascaded neural network models:
  * *Stage 1:* MobileNetV2 / COCO-SSD (Fast continuous detector)
  * *Stage 2:* ByteTrack / DeepSORT (Object trajectory tracking)
  * *Stage 3:* Rules Engine (Tripwire, Dwell timers, Facial embeddings, ANPR)

### 6. Camera Configuration (`CameraConfig`)
* **Stream Management:** Admin interface to manage RTSP URLs, camera priority, and toggle cameras online or offline.
* Protected by **Role-Based Access Control (RBAC)** (Admin access only).

### 7. Forensic Evidence Modal (`EvidenceModal`)
* Clicking on any alert opens a forensic inspection card showing:
  * Full-resolution snapshot with bounding box overlays
  * Exact UTC timestamp and GPS coordinates
  * Tracking ID and AI confidence percentage
  * Cryptographic integrity status

---

## 5. Backend Services & API Documentation

The backend service (`ibvap-backend`) is built with **FastAPI**, **SQLAlchemy ORM**, **OpenCV**, and **PyCryptodome**, providing production-grade persistence, real-time video streaming, neural network inference, and cryptographic verification.

```
ibvap-backend/
├── app/
│   ├── main.py          # FastAPI application, routing, and WebSocket manager
│   ├── video_stream.py  # MJPEG camera stream simulator & tactical HUD overlay
│   ├── yolo_detector.py # YOLOv8 ONNX object detection module
│   ├── rule_engine.py   # Event processor (tripwire, loiter, watchlist, ANPR, C2 dispatch)
│   ├── ledger.py        # SHA-256 cryptographic hash-chain ledger
│   ├── security.py      # AES-256-GCM encryption, JWT authentication, & RBAC
│   ├── models.py        # SQLAlchemy database models
│   ├── schemas.py       # Pydantic v2 data validation schemas (camelCase conversion)
│   ├── seed.py          # Initial database seed (cameras, demo users, alerts)
│   ├── ws_manager.py    # WebSocket connection pool and broadcaster
│   └── database.py      # SQLite / SQLAlchemy engine and session factory
├── .env.example         # Template for environment configuration
└── requirements.txt     # Python dependencies
```

---

### A. REST API Endpoints

All responses automatically format keys in **camelCase** to match frontend TypeScript interfaces.

#### 1. Authentication & Users
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Public | Validates credentials, checks account lockout (max 5 attempts), returns 8h JWT token. |
| `GET` | `/auth/me` | Authenticated | Returns username and active RBAC role (`operator`, `supervisor`, `admin`). |

#### 2. Camera Management & Video Streaming
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/cameras` | Operator+ | Lists all registered camera nodes with online status, GPS anchors, and FPS telemetry. |
| `GET` | `/cameras/{cam_id}/stream` | Public | Live MJPEG multipart video stream (`multipart/x-mixed-replace; boundary=frame`) for NVR displays. |
| `PATCH` | `/cameras/{cam_id}/toggle` | Admin | Toggles camera online/offline state and logs an action to the audit ledger. |
| `PATCH` | `/cameras/{cam_id}/night` | Operator+ | Toggles infrared night-vision mode and applies synthetic IR color grading in real time. |

#### 3. Alerts & Incident Management
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/alerts` | Operator+ | Queries alerts with query filters: `type`, `sev`, `camId`, `reviewed`. Decrypts AES fields on read. |
| `POST` | `/alerts` | Operator+ | Creates a new security alert: encrypts snapshot with AES-256, appends to hash ledger, and broadcasts to WebSocket clients. |
| `PATCH` | `/alerts/{id}/reviewed` | Supervisor+ | Marks an alert as acknowledged and reviewed with audit trail entry. |

#### 4. Tamper-Evident Ledger
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/ledger/verify` | Operator+ | Recomputes and verifies the entire SHA-256 hash-chain to prove zero records were modified. |
| `POST` | `/ledger/tamper-demo/{id}` | Admin | *Demo endpoint:* Intentionally modifies a record bypassing the ledger to demonstrate live tamper detection. |

#### 5. Human Audit Logs (FR-9.4)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/audit-log` | Supervisor+ | Returns records of human operator actions (logins, exports, camera state toggles). |
| `GET` | `/audit-log/export-csv` | Supervisor+ | Exports the audit log to CSV for compliance inspection. |

---

### B. Real-Time WebSockets (`/ws/alerts`)

- **Protocol:** `ws://localhost:8000/ws/alerts`
- When any alert is created (via AI detection, background rule engine, or manual creation), the server immediately broadcasts JSON:
```json
{
  "event": "new_alert",
  "data": {
    "id": "EVT-0015",
    "type": "weapon",
    "sev": "high",
    "camId": "cam-1",
    "camName": "CAM-01 · North Perimeter",
    "location": "BOP Alpha — North Fence Line",
    "confidence": 96,
    "trackId": "#184",
    "detail": "CRITICAL: Weapon Detected (Blade / Edged Weapon)",
    "reviewed": false,
    "ts": "2026-09-10T10:45:00Z",
    "snapshot": "data:image/jpeg;base64,..."
  }
}
```

---

### C. Video Streaming & Computer Vision (`video_stream.py`)

- **MJPEG Generator:** Generates high-efficiency multipart JPEG frames at ~12 FPS for CAM-02, CAM-03, and CAM-04.
- **Procedural Tactical Scenes:**
  - `fence`: Barbed wire fence posts with dynamic patrolling officers and virtual fence boundaries.
  - `gate`: Border checkpoint booth with barrier poles and animated vehicles displaying license plates.
  - `night`: Infrared night-vision filter with synthetic IR sensor noise and high-contrast thermal silhouettes.
- **HUD Reticles & OSD Overlays:** OpenCV overlays timestamps, camera IDs, GPS coordinates, and corner targeting reticles onto every frame.

---

### D. Automated Rule Engine (`rule_engine.py`)

Runs as an asynchronous background worker continuously evaluating incoming telemetry:
1. **Virtual Fence Crossing:** Flags any entity crossing the boundary line at 72% depth.
2. **Loiter Dwell Time:** Measures how long an object remains within a 15% radius; triggers a loiter warning if $\ge 4$ seconds.
3. **ANPR Hotlist Matching:** Compares detected number plates (e.g. `PB-11-AK-4471`) against flagged vehicle lists.
4. **Watchlist Matching:** Cross-references facial embeddings against surveillance profiles (e.g. `WL-009`, `WL-014`).
5. **C2 Relay Webhook:** Automatically dispatches high-severity alerts to external military Command & Control systems.

---

### E. Cryptographic Ledger (`ledger.py`)

IBVAP implements an immutable, blockchain-style hash chain:
- **Hashing Formula:**
  $$\text{Record Hash}_n = \text{SHA-256}(\text{Record Hash}_{n-1} + \text{alert\_id} + \text{cam\_id} + \text{type} + \text{sev} + \text{ts})$$
- If any attacker modifies a past alert directly in the database (e.g., altering a timestamp or changing severity), the hash chain breaks from that record forward.
- The `/ledger/verify` endpoint recalculates all hashes from genesis to head, pinpointing the exact compromised record if tampering occurs.

---

### F. Encryption & Security (`security.py`)

- **Field-Level Encryption at Rest (AES-256-GCM):**
  - Incident details and JPEG snapshots are encrypted using AES-256 in Galois/Counter Mode before being saved to disk.
  - Encryption key is stored securely in `.aes_key` (generated with `os.urandom(32)`).
  - Plaintext data is never written to disk unencrypted.
- **Password Security:** Passwords are salted and hashed with **PBKDF2-SHA256**.
- **Brute-Force Lockout (FR-9.5):** After 5 consecutive failed login attempts, the account is locked for 15 minutes.


---

## 6. User Roles & Permissions

The platform includes built-in Role-Based Access Control (RBAC):

| Role | Permissions |
| :--- | :--- |
| **Operator** | Monitor live feeds, view alerts, mark alerts as reviewed, toggle night vision. |
| **Supervisor** | All Operator capabilities + export forensic CSV reports and inspect system analytics. |
| **Admin** | Full system control + camera toggling, RTSP configuration, and system arming/disarming. |

Operators can quickly test roles during demonstrations using the **Role Switcher** in the top bar.

---

## 7. How to Run the Platform

### Running the Backend
```bash
cd ibvap-backend
# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Running the Frontend
```bash
# In the project root
npm install
npm run dev
```

Once running:
- **Frontend:** `http://localhost:3000` (or `http://localhost:5173`)
- **Backend API:** `http://localhost:8000`
- **Interactive API Docs:** `http://localhost:8000/docs`
