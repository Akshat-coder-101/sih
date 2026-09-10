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

## 5. Backend Services Architecture

The backend (`ibvap-backend`) is built with **FastAPI**, **SQLAlchemy**, and **OpenCV**:

```
ibvap-backend/
├── app/
│   ├── main.py          # REST API endpoints & WebSocket broadcaster
│   ├── video_stream.py  # MJPEG camera stream simulator (OpenCV)
│   ├── yolo_detector.py # YOLOv8 ONNX object detection module
│   ├── rule_engine.py   # Event processor (tripwire, loiter, watchlist, ANPR)
│   ├── ledger.py        # SHA-256 cryptographic hash-chain ledger
│   ├── security.py      # AES-256-GCM encryption & JWT authentication
│   ├── models.py        # Database models (Camera, Alert, User, Ledger)
│   └── schemas.py       # Pydantic data validation schemas
```

* **`main.py`**: Handles user authentication, camera listings, alert management, and live WebSocket subscriptions.
* **`ledger.py`**: Calculates cumulative SHA-256 hashes linking each new alert to the previous alert, creating an immutable audit trail.
* **`security.py`**: Encrypts sensitive fields (alert details and JPEG snapshots) using AES-256 in Galois/Counter Mode (GCM).

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
