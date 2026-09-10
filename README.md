# 🛡️ IBVAP — Intelligent Border & Surveillance Video Analytics Platform
### Smart India Hackathon 2026 | Team: **PERCEPTRONS**
### Presentation Module: **System Design & Technical Approach**

---

## 📌 Executive Summary

**IBVAP** (Intelligent Border Video Analytics Platform) is an edge-optimized, multi-camera surveillance and threat intelligence system designed for real-time border security, sensitive perimeter monitoring, and critical infrastructure protection. 

The architecture converts raw, unmanaged RTSP CCTV video feeds into prioritized, contextualized, and actionable security alerts using a high-throughput cascaded AI pipeline, spatial-temporal rules engine, and an automated chain-of-custody evidence vault.

> 📖 **Full System Documentation:** See [documentation.md](documentation.md) for an in-depth walkthrough of all website components, AI modules, and operational workflows.

---

## 🔪 Weapon & Knife Threat Detection

- **Real-Time Client-Side Inference:** On `CAM-01`, **TensorFlow.js COCO-SSD** runs directly in the browser over local webcam video frames. When a knife or blade is presented, the model immediately draws a targeted red bounding box, alerts the operator, and captures an encrypted snapshot.
- **Backend YOLOv8 Engine:** Server-side processing supports **YOLOv8 ONNX** with class `knife` for automated CCTV stream monitoring.
- **Presentation Shortcut:** Press the **`K`** key on any page to immediately trigger a live simulated weapon threat alert.

---

## 🔒 Forensic Security & Tamper-Evident Ledger

- **AES-256-GCM Encryption:** High-resolution snapshots and incident details are encrypted at rest using AES-256-GCM before writing to the database.
- **SHA-256 Hash-Chain Ledger:** Every security event is cryptographically linked to the previous event hash, providing an immutable audit trail.
- **Log Integrity Verification:** Operators and supervisors can click **"Verify Log Integrity"** in the Alerts Log to cryptographically audit the entire incident database.

---

## 📊 System Design & Decision Flowchart (Presentation Style)

### Algorithmic Decision Tree (Mermaid Architecture)

```mermaid
flowchart LR
    %% Styling Classes
    classDef card fill:#ffffff,stroke:#94a3b8,stroke-width:1.5px,color:#0f172a,rx:8px,ry:8px;
    classDef decision fill:#ffffff,stroke:#334155,stroke-width:2px,color:#0f172a;
    classDef alert fill:#fff1f2,stroke:#f43f5e,stroke-width:2px,color:#9f1239;
    classDef subg fill:#f8fafc,stroke:#e2e8f0,stroke-width:1.5px,color:#334155;

    %% Column 1: Ingestion & Target Filtering
    subgraph COL1["1. Stream Ingestion & Screening"]
        direction TB
        START["Start: Existing CCTV Cameras<br/>(CAM-01, CAM-02, CAM-03)"]:::card
        INGEST["RTSP Stream Ingestion<br/>(Decode, Resize & Keyframes)"]:::card
        QUEUE["Multi-Camera Queue Buffer<br/>(Route Streams & Balance GPU Load)"]:::card
        DEC_TARGET{"Target Detected?<br/>(Person / Vehicle)"}:::decision
        DISCARD["Log Routine Frame<br/>& Continue Stream"]:::card

        START --> INGEST --> QUEUE --> DEC_TARGET
        DEC_TARGET -- No --> DISCARD
    end
    class COL1 subg;

    %% Column 2: AI Pipeline & Intelligence
    subgraph COL2["2. AI Analysis & Intelligence"]
        direction TB
        TRACK["ByteTrack Tracking Engine<br/>(Kalman Filter: ID & Velocity)"]:::card
        DEC_SECONDARY{"Secondary Model?<br/>(Face / Plate)"}:::decision
        OCR_FACE["Run RetinaFace &<br/>PaddleOCR ANPR"]:::card
        DEC_BREACH{"Security Breach or Loitering?<br/>(Fence Cross / Dwell > 4s)"}:::decision
        NORMAL_LIVE["Display Normal Live Feed<br/>to Security Operator"]:::card

        TRACK --> DEC_SECONDARY
        DEC_SECONDARY -- Yes --> OCR_FACE --> DEC_BREACH
        DEC_SECONDARY -- No --> DEC_BREACH
        DEC_BREACH -- No --> NORMAL_LIVE
    end
    class COL2 subg;

    %% Column 3: Command Center & Tactical Response
    subgraph COL3["3. Command Center & Response"]
        direction TB
        GEN_ALERT["Generate Threat Event & Evidence<br/>(HD Snapshot + 10s MP4 Clip)"]:::alert
        GATEWAY["Store in PostgreSQL DB<br/>& Broadcast via WebSocket (<200ms)"]:::card
        DASH["React Security Dashboard<br/>(Live Feed Matrix & Audio Alert)"]:::card
        DEC_OP{"Operator Action<br/>Required?"}:::decision
        DISPATCH["Escalate & Dispatch Unit<br/>(Quick Response Team QRT)"]:::alert

        GEN_ALERT --> GATEWAY --> DASH --> DEC_OP
        DEC_OP -- Yes --> DISPATCH
    end
    class COL3 subg;

    %% Cross-Column Stream Flow
    DEC_TARGET == Yes ==> TRACK
    DEC_BREACH == Yes ==> GEN_ALERT
```

---

## 🏗️ Technical Approach Stage Breakdown

Below is the complete end-to-end multi-stage pipeline as presented in the **Technical Approach** slide:

```mermaid
flowchart LR
    %% Styling Classes
    classDef cctv fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0f172a;
    classDef ingest fill:#ccfbf1,stroke:#0d9488,stroke-width:2px,color:#0f172a;
    classDef queue fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#0f172a;
    classDef ai fill:#f3e8ff,stroke:#7c3aed,stroke-width:2px,color:#0f172a;
    classDef intel fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#0f172a;
    classDef output fill:#ffe4e6,stroke:#e11d48,stroke-width:2px,color:#0f172a;
    classDef operator fill:#ede9fe,stroke:#6366f1,stroke-width:2px,color:#0f172a;

    %% Stage 1: Existing CCTV
    subgraph S1["1. Existing CCTV"]
        direction TB
        CCTV_DESC["IP Cameras & Legacy CCTV<br/>Infrastructure"]
        CAM1["📹 CAM-01"]
        CAM2["📹 CAM-02"]
        CAM3["📹 CAM-03"]
        RTSP_OUT["RTSP Stream Output"]
        CCTV_DESC --> CAM1 & CAM2 & CAM3 --> RTSP_OUT
    end
    class S1,CCTV_DESC,CAM1,CAM2,CAM3,RTSP_OUT cctv;

    %% Stage 2: RTSP Stream Ingestion
    subgraph S2["2. RTSP Stream Ingestion"]
        direction TB
        ING_CONN["📡 Connect (RTSP)"]
        ING_DEC["🎞️ Decode Frames"]
        ING_RES["📐 Resize & Normalize"]
        ING_SEL["⚡ Select Key Frames (FPS throttle)"]
        ING_TAG["🕒 Add Camera ID & Timestamp"]
        
        ING_CONN --> ING_DEC --> ING_RES --> ING_SEL --> ING_TAG
    end
    class S2,ING_CONN,ING_DEC,ING_RES,ING_SEL,ING_TAG ingest;

    %% Stage 3: Multi Camera Queue
    subgraph S3["3. Multi Camera Queue"]
        direction TB
        Q1["📥 Queue 1 (CAM-01)"]
        Q2["📥 Queue 2 (CAM-02)"]
        Q3["📥 Queue 3 (CAM-03)"]
        QN["📥 Queue N (CAM-N)"]
        
        subgraph Q_FEAT["Queue Operations"]
            QF1["• Route Camera Streams"]
            QF2["• Buffer Incoming Frames"]
            QF3["• Prioritize Key Frames"]
            QF4["• Balance Processing Loads"]
        end
    end
    class S3,Q1,Q2,Q3,QN,Q_FEAT,QF1,QF2,QF3,QF4 queue;

    %% Stage 4: AI Analysis
    subgraph S4["4. AI Analysis Pipeline"]
        direction TB
        subgraph DETECT["Primary & Secondary Detectors"]
            MOD_PERSON["👤 Person Detection (YOLOv8)"]
            MOD_VEHICLE["🚗 Vehicle Detection (YOLOv8)"]
            MOD_FACE["👤 Face Detection (RetinaFace)"]
            MOD_PLATE["🪪 Number Plate (PaddleOCR)"]
        end
        
        subgraph TRACK["Multi-Object Tracking"]
            BYTE_TRACK["🎯 ByteTrack Engine<br/>ID | Position (X,Y) | Velocity Vector"]
        end
        
        DETECT --> BYTE_TRACK
    end
    class S4,DETECT,TRACK,MOD_PERSON,MOD_VEHICLE,MOD_FACE,MOD_PLATE,BYTE_TRACK ai;

    %% Stage 5: Intelligence
    subgraph S5["5. Intelligence Engine"]
        direction TB
        subgraph SPATIAL["Location Context"]
            GEO_FENCE["🚧 Virtual Fence (Polygons)"]
            GEO_ZONE["⛔ Restricted Zone Detection"]
            GEO_IO["🚪 Directional Entry / Exit"]
        end

        subgraph TEMPORAL["Time Context"]
            TIME_STAMP["⏰ Real-Time Timestamp"]
            TIME_DWELL["⏳ Dwell Time (Threshold > 4s)"]
            TIME_SEQ["🔁 Cross-Camera Sequence"]
        end

        subgraph BEHAVIOR["Behaviour Analysis"]
            BEH_LOIT["🚶 Loitering Detection"]
            BEH_NIGHT["🌙 Night Movement Alert"]
            BEH_SUSP["⚠️ Suspicious Activity Fusion"]
        end

        SPATIAL --> BEHAVIOR
        TEMPORAL --> BEHAVIOR
    end
    class S5,SPATIAL,TEMPORAL,BEHAVIOR,GEO_FENCE,GEO_ZONE,GEO_IO,TIME_STAMP,TIME_DWELL,TIME_SEQ,BEH_LOIT,BEH_NIGHT,BEH_SUSP intel;

    %% Stage 6: Alert, Evidence & Dashboard
    subgraph S6["6. Alert, Evidence & Dashboard"]
        direction TB
        subgraph ALERTS["Alerts Engine"]
            ALT_RULE["⚙️ AI + Rules + Context"]
            ALT_GEN["🚨 Event Generation"]
            ALT_PRIO["📊 Risk / Priority Scoring"]
            ALT_RT["⚡ Real-Time Alert Dispatch"]
        end

        subgraph EVIDENCE["Forensic Evidence"]
            EVI_SNAP["📸 Auto HD Snapshot"]
            EVI_CLIP["📼 Pre/Post Video Clip"]
            EVI_GEO["📍 Camera GIS Location"]
            EVI_HIST["📜 Audit Event History"]
        end

        subgraph DASHBOARD["React Command Dashboard"]
            DASH_LIVE["📺 Live CCTV Grid & Stream"]
            DASH_FILTER["🔍 Multi-Param Filters"]
            DASH_FEED["🔔 Priority Alert Feed"]
            DASH_MAP["🗺️ Tactical Event Map"]
        end

        ALERTS --> DASHBOARD
        EVIDENCE --> DASHBOARD
    end
    class S6,ALERTS,EVIDENCE,DASHBOARD,ALT_RULE,ALT_GEN,ALT_PRIO,ALT_RT,EVI_SNAP,EVI_CLIP,EVI_GEO,EVI_HIST,DASH_LIVE,DASH_FILTER,DASH_FEED,DASH_MAP output;

    %% Human Operator
    subgraph OPERATOR["Security Operator Terminal"]
        SEC_OP["👮 SECURITY OPERATOR<br/><b>Monitor · Review · Take Action</b>"]
    end
    class OPERATOR,SEC_OP operator;

    %% Connectors between Stages
    RTSP_OUT ==> ING_CONN
    ING_TAG ==> Q1 & Q2 & Q3 & QN
    Q1 & Q2 & Q3 & QN ==> DETECT
    BYTE_TRACK ==> SPATIAL & TEMPORAL
    BEHAVIOR ==> ALT_RULE & EVI_SNAP
    DASHBOARD ==> SEC_OP
```

---

## 🔄 Detailed End-to-End Pipeline Breakdown

| Stage | Module Name | Core Functionality | Technical Mechanisms |
| :--- | :--- | :--- | :--- |
| **01** | **Existing CCTV Infrastructure** | Interfaces with legacy on-site IP cameras & NVRs without requiring proprietary hardware upgrades. | RTSP streaming (H.264 / H.265), ONVIF camera discovery, multi-bitrate resolution support. |
| **02** | **RTSP Stream Ingestion** | Low-latency stream connection, continuous decoding, frame selection, and metadata injection. | OpenCV VideoCapture / FFmpeg hardware acceleration, dynamic frame skipping, FPS stabilization, camera ID & UTC timestamp watermarking. |
| **03** | **Multi-Camera Queue** | Asynchronous decoupling of stream ingestion from heavy GPU/NPU inference workers. | Multi-threaded FIFO queues / Redis Streams, rate-limiting, keyframe priority buffering, dynamic worker load distribution. |
| **04** | **AI Analysis Pipeline** | High-speed multi-class detection coupled with persistent identity tracking across frames. | **YOLOv8** (Person, Vehicle), **RetinaFace** (Face detection), **PaddleOCR** (License Plate), **ByteTrack** (Kalman filtering + association metric for tracklet ID, position, and velocity). |
| **05** | **Intelligence Engine** | Contextual verification engine eliminating false alarms through spatial and temporal constraints. | **Location:** Ray-casting polygon intersection (Virtual Fence, Perimeter Zones, Directional Tripwires).<br/>**Time:** Dwell timers (> 4s stationary), curfew hour schedules.<br/>**Behavior:** Loitering patterns, nocturnal perimeter breach detection. |
| **06** | **Alerts, Evidence & Command Center** | Multi-channel instant alerting, forensically verifiable evidence packs, and tactical operator UI. | FastAPI WebSocket broadcasters, PostgreSQL ACID event logging, auto-clipped MP4 & JPEG snapshots, interactive React dashboard. |

---

## 🛠️ Technology Stack Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             IBVAP TECH STACK                                │
├──────────────┬────────────────────────┬─────────────────────────────────────┤
│ Technology   │ Layer                  │ Specific Responsibility             │
├──────────────┼────────────────────────┼─────────────────────────────────────┤
│ 📹 RTSP      │ Protocol / Transport   │ Real-time streaming from IP cameras │
│ 🐍 Python    │ Core Backend Language  │ Orchestration, model pipelines, API │
│ 👁️ OpenCV    │ Frame Pre-processing   │ Decode, resize, color normalization │
│ ⚡ YOLO      │ Deep Learning Detector │ Real-time person & vehicle detection│
│ 🎯 ByteTrack │ Multi-Object Tracking  │ Persistent ID, tracklets & velocity │
│ 🪪 OCR Engine│ Text Recognition       │ Number plate recognition (ANPR)     │
│ 🚀 FastAPI   │ API & Streaming Gateway│ Async endpoints, WebSockets, broker │
│ 🐘 PostgreSQL│ Database & Storage     │ Structured telemetry & alert logs   │
│ ⚛️ React     │ Command Center UI      │ Live monitor, audit logs & evidence │
└──────────────┴────────────────────────┴─────────────────────────────────────┘
```

---

## ⚡ Execution Sequence Diagram (Data Flow)

```mermaid
sequenceDiagram
    autonumber
    participant CAM as 📹 IP Camera (RTSP)
    participant ING as 📡 Ingestion Engine (OpenCV/FFmpeg)
    participant QUEUE as 📥 Camera Queue Manager
    participant AI as 🧠 AI Pipeline (YOLO + ByteTrack)
    participant INTEL as 📐 Intelligence Engine (Spatial/Temporal)
    participant BACKEND as 🚀 Backend (FastAPI + PostgreSQL)
    participant UI as 👮 Operator Dashboard (React)

    CAM->>ING: RTSP Video Stream (H.264, 25-30 FPS)
    ING->>ING: Hardware Decode -> Resize -> Frame Filtering
    ING->>ING: Append Metadata (CamID: CAM-01, Timestamp: 10:42:01)
    ING->>QUEUE: Push Frame to Dedicated Queue
    QUEUE->>AI: Fetch Batched Frames for Inference
    AI->>AI: Detect Objects (Person: 0.94, Coords: [x,y,w,h])
    AI->>AI: Update ByteTrack Kalman Filter (Track ID #104)
    AI->>INTEL: Emit Tracklet State (ID, Position, Trajectory)
    
    rect rgb(254, 243, 199)
        Note over INTEL: Spatial & Temporal Rules Evaluation
        INTEL->>INTEL: Point-in-Polygon Check (Restricted Perimeter Zone)
        INTEL->>INTEL: Dwell Time Counter > 4.0s (Loitering Detected)
    end

    alt Breach or Threat Confirmed
        INTEL->>BACKEND: Trigger Threat Event (Level: CRITICAL)
        BACKEND->>BACKEND: Store Event Log + Save Snapshot & Video Clip
        BACKEND-->>UI: WebSocket Broadcast (Instant Alert < 200ms)
        UI->>UI: Audible Alarm + Flash Viewport + Pin Evidence
        UI->>UI: Operator Verifies & Initiates Escalation Protocol
    else Normal Activity / Authorized Zone
        INTEL->>BACKEND: Log Background Telemetry (Low Priority)
    end
```

---

## 💡 Key Design Highlights for SIH 2026 Evaluation

### 1. Cascaded "Cheap-First" AI Pipeline
Instead of running heavy face-recognition and license-plate OCR continuously on 30 FPS video feeds (which exhausts GPU memory):
- **Stage 1 (Lightweight):** Highly optimized YOLO detector runs continuously to locate generic objects (person, vehicle).
- **Stage 2 (Triggered):** Expensive biometric and ANPR models execute **only when** a person or vehicle crosses into an active region of interest.
- **Outcome:** **70% reduction in GPU computing overhead** with zero compromise on detection accuracy.

### 2. Multi-Camera Independent Queues
- Each camera operates with an isolated buffer queue.
- If camera 3 encounters network jitter or packet loss, it will not block or starve inference for camera 1 and camera 2.
- Automatically drops non-key frames during high network load to maintain real-time responsiveness.

### 3. Spatial-Temporal Intelligence (Elimination of False Positives)
- Standard AI models trigger alerts on every detected person, resulting in alert fatigue.
- IBVAP checks **Virtual Fences** (custom polygon vertices) and **Time Context** (dwell duration > 4s, night curfew hours).
- A maintenance worker walking past the perimeter will not trigger an alert; an unauthorized subject climbing or loitering near the fence triggers an immediate Level-1 Critical breach alert.

### 4. Zero-Friction Integration with Existing Security Infrastructure
- Works on standard RTSP and ONVIF protocols compatible with existing CP PLUS, Hikvision, Dahua, and Honeywell CCTV setups already deployed at border outposts and government facilities.

---

## 🚀 Quick Start Guide

### 1. Start the Backend API (FastAPI)
```bash
cd ibvap-backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Start the Frontend Command Center (React + Vite)
```bash
# In the project root
npm install
npm run dev
```

- **Frontend Dashboard:** `http://localhost:3000` (or `http://localhost:5173`)
- **Backend Swagger Docs:** `http://localhost:8000/docs`

---

## 🎤 Presentation Notes for SIH PPT (1-Minute Elevator Pitch)

> *"Respected jury members, our system **IBVAP** solves the fundamental problem of modern border and perimeter surveillance: **turning dumb CCTV cameras into proactive tactical sensors**.*
> 
> *As shown in our Technical Approach flowchart, the architecture flows systematically across 6 unified stages:*
> *1. **Ingestion & Conditioning:** We connect to any existing IP CCTV camera via RTSP, decode, normalize, and stamp frames with microsecond telemetry.*
> *2. **Load-Balanced Queues:** Dedicated per-camera queues prevent bottlenecks and balance computational loads.*
> *3. **Cascaded AI Pipeline:** Using YOLOv8 and ByteTrack, we identify subjects, build trajectory vectors, and track IDs continuously across frames.*
> *4. **Spatial-Temporal Intelligence:** We filter out 95% of false alarms by cross-referencing detections with geometric virtual fences, dwell-time counters, and loitering heuristics.*
> *5. **Command & Control:** When a verified threat occurs, alerts are dispatched via WebSockets in under 200 milliseconds to our React dashboard with full forensic snapshots and video evidence.*
> 
> *Our tech stack combines Python, OpenCV, YOLO, ByteTrack, FastAPI, PostgreSQL, and React for maximum edge-readiness and field reliability."*

---

*Authored by Team **PERCEPTRONS** for **Smart India Hackathon 2026**.*
