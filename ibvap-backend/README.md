# IBVAP — Backend Microservice

The **IBVAP Backend** is a high-performance Python FastAPI service providing real-time video stream generation, neural network object detection, automated perimeter rule evaluation, cryptographic tamper-evident audit ledgers, and AES-256-GCM data encryption at rest.

---

## 🏗️ Architecture & Modules

```
ibvap-backend/
├── app/
│   ├── main.py          # FastAPI application, route handlers, and WebSocket manager
│   ├── video_stream.py  # MJPEG camera video generator & tactical OpenCV HUD overlays
│   ├── yolo_detector.py # YOLOv8 ONNX object detection module (80 classes, including knife)
│   ├── rule_engine.py   # Event processor (tripwire, dwell time, watchlist, ANPR, C2 dispatch)
│   ├── ledger.py        # SHA-256 cryptographic hash-chain ledger
│   ├── security.py      # AES-256-GCM encryption, JWT authentication, PBKDF2 hashing & RBAC
│   ├── models.py        # SQLAlchemy database models (Camera, Alert, User, AuditLog, Ledger)
│   ├── schemas.py       # Pydantic v2 schemas with camelCase automatic serialization
│   ├── seed.py          # Initial database seed (cameras, demo accounts, alerts)
│   ├── ws_manager.py    # WebSocket connection manager and broadcast bus
│   └── database.py      # SQLite database engine and session factory
├── .env.example         # Template for environment configuration
└── requirements.txt     # Python dependencies
```

---

## 🚀 Getting Started

### 1. Installation
```bash
cd ibvap-backend
pip install -r requirements.txt
```

### 2. Run the Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup, the service automatically:
1. Creates the SQLite database (`ibvap.db`).
2. Generates an AES-256 cryptographic key at `.aes_key`.
3. Seeds initial cameras, alerts, and demo users.
4. Starts the background rule engine worker.

- **API Base URL:** `http://localhost:8000`
- **Interactive Swagger Documentation:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

## 👥 Demo User Accounts (RBAC)

| Role | Username | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin123` | Full control: toggle cameras, configure streams, run tamper demo, manage users. |
| **Supervisor** | `supervisor` | `supervisor123` | Acknowledge & review alerts, export CSV reports, view analytics and audit logs. |
| **Operator** | `operator` | `operator123` | Monitor live streams, view alerts, toggle night vision mode. |

---

## 📡 API Endpoint Reference

All endpoints return JSON keys formatted in **camelCase** for seamless frontend integration.

### Authentication & Users
| Method | Path | Auth | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | None | Authenticates user; locks account for 15 mins after 5 failed attempts. |
| `GET` | `/auth/me` | Bearer Token | Returns user profile and current role. |

### Cameras & Video Streams
| Method | Path | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/cameras` | Operator+ | Returns list of registered cameras and telemetry. |
| `GET` | `/cameras/{cam_id}/stream` | None | Real-time MJPEG multipart stream (`multipart/x-mixed-replace; boundary=frame`). |
| `PATCH` | `/cameras/{cam_id}/toggle` | Admin | Toggles camera online/offline state. |
| `PATCH` | `/cameras/{cam_id}/night` | Operator+ | Toggles IR night mode and enhances low-light contrast. |

### Alerts & Incidents
| Method | Path | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/alerts` | Operator+ | Returns filtered alerts (`type`, `sev`, `camId`, `reviewed`). Plaintext AES decrypted on read. |
| `POST` | `/alerts` | Operator+ | Creates alert, encrypts snapshot with AES-256-GCM, appends to hash ledger, and pushes to WebSocket. |
| `PATCH` | `/alerts/{id}/reviewed` | Supervisor+ | Marks an alert as acknowledged and reviewed. |

### Cryptographic Ledger (Tamper Evidence)
| Method | Path | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/ledger/verify` | Operator+ | Recalculates full SHA-256 hash-chain to verify database integrity. |
| `POST` | `/ledger/tamper-demo/{id}` | Admin | **Demo endpoint:** Directly modifies a record in the database bypassing the ledger to prove live tamper detection. |

### Human Audit Log (FR-9.4)
| Method | Path | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/audit-log` | Supervisor+ | Returns records of administrative and operator actions. |
| `GET` | `/audit-log/export-csv` | Supervisor+ | Downloads audit log as a CSV file. |

### Real-Time WebSocket Feed
| Method | Path | Description |
| :--- | :--- | :--- |
| `WS` | `/ws/alerts` | Broadcasts real-time events (`new_alert`) to connected browser clients. |

---

## 🔒 Security Architecture

1. **AES-256-GCM Encryption:**
   - Forensic snapshots (`snapshot_enc`) and incident details (`detail_enc`) are encrypted at rest using AES-256-GCM before writing to the database.
   - Plaintext evidence never touches disk unencrypted.
2. **SHA-256 Tamper-Evident Ledger:**
   - Every alert is cryptographically linked to the previous record hash:
     $$\text{Hash}_n = \text{SHA-256}(\text{Hash}_{n-1} + \text{alert\_id} + \text{cam\_id} + \text{type} + \text{sev} + \text{ts})$$
   - Any unauthorized modification breaks the hash chain and is immediately flagged by `/ledger/verify`.
3. **Password Security:**
   - Salted and hashed using PBKDF2-SHA256.
   - Brute-force lockout enforces a 15-minute lock after 5 consecutive bad login attempts.
