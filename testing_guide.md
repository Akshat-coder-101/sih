# IBVAP — Step-by-Step Testing & Verification Guide

This guide walks you through verifying all features of the **Intelligent Border Video Analytics Platform (IBVAP)** after starting the application.

---

## 🛠️ Step 0: Launch the Application

Ensure both the backend API and frontend dev server are running in separate terminal windows.

### Terminal 1 (Backend FastAPI)
```bash
cd ibvap-backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
* API runs at: `http://localhost:8000`
* Interactive API Documentation: `http://localhost:8000/docs`

### Terminal 2 (Frontend Command Center)
```bash
cd frontend
npm install
npm run dev
```
* Dashboard runs at: **`http://localhost:3000/`**

---

## 🔪 Step 1: Test Real-Time Knife & Blade Detection (Live Webcam)

This tests client-side in-browser neural network inference using TensorFlow.js COCO-SSD.

1. In your browser, open **`http://localhost:3000/`**.
2. On the **Live Monitor** view, make sure **`CAM-01 · North Perimeter`** is selected.
3. In the center of the video box, click the cyan **`Start Webcam`** button.
4. Click **Allow** when your browser requests camera permissions. Your live webcam video will appear immediately.
5. **Hold a knife (or scissors, cutlery, or phone) in front of the camera:**
   * **Targeting Bounding Box:** A red bounding box will track the object labeled `WEAPON (KNIFE) [Score]`.
   * **Screen Breach Flash:** The viewport border will flash bright red with a **`FENCE BREACH`** visual alarm.
   * **Real-Time Alert Created:** A High-Severity alert (`CRITICAL: Weapon Detected (Blade / Edged Weapon)`) pops up at the top of the **Live Alerts** panel on the right.
   * **Backend Sync:** The event is automatically encrypted with AES-256-GCM and saved to the backend database and SHA-256 ledger.

---

## ⚡ Step 2: Test One-Click Threat Presentation Shortcut (Key `K`)

For quick demonstrations without holding a physical object:

1. Press the **`K`** key on your keyboard anytime, **or** click the red **`Demo Threat [K]`** button in the top navigation bar.
2. The platform will:
   * Instantly trigger a simulated concealed blade breach.
   * Switch the monitor view to `CAM-01`.
   * Flash the red **`FENCE BREACH`** alarm.
   * Add a High-Severity weapon threat alert with a captured evidentiary frame.

---

## 📹 Step 3: Test CCTV Streams & Night Vision (CAM-02, CAM-03, CAM-04)

1. Click the **`CAM-02 · Check Post Gate`** tab:
   * Displays the border checkpoint gate with animated barrier poles, passing vehicles, and license plates (`ANPR`).
2. Click the **`CAM-03 · Border Road`** tab:
   * Displays the border approach road in enhanced **IR Night Vision Mode**.
3. **Toggle Night Vision Mode:**
   * Click the **Moon Icon** at the top right of the video viewport.
   * Observe the feed smoothly transition between daylight optical mode and green infrared thermal mode in real time.

---

## 🔲 Step 4: Test 2×2 Multi-Camera Grid

1. In the left sidebar, click **`Camera Grid`**.
2. All 4 tactical border cameras (`CAM-01` through `CAM-04`) will stream simultaneously in a 2×2 tactical surveillance wall.
3. Click any camera card to immediately open a focused full-screen view.

---

## 🔍 Step 5: Test Forensic Evidence Lightbox Modal

1. In the **Live Alerts** panel on the right (or from the **Alerts Log** page), **click on any alert**.
2. The **Forensic Evidence Modal** will pop up:
   * Shows the captured high-resolution snapshot with bounding boxes burned in.
   * Displays forensic metadata: **Sector Location**, **GPS Coordinates**, **AI Confidence %**, **Track ID**, and **UTC Timestamp**.
3. Click **Mark as Reviewed** to acknowledge the incident. Notice the status badge updates to `Verified & Reviewed`.

---

## 🛡️ Step 6: Test 3-Tier Cryptographic Ledger Integrity

IBVAP chains every incident into an immutable cryptographic framework to prevent unauthorized tampering.

### A. Local SHA-256 Hash Chain Verification
1. In the left sidebar, navigate to **`Alerts Log`**.
2. Click the cyan **`Verify Log Integrity`** button in the top right.
3. A modal opens showing the ledger audit:
   * The server walks and re-hashes every record from genesis to head.
   * Confirms **`Ledger Intact`** and displays the count of verified records.

### B. Deterministic Merkle Inclusion Proof & AI Model Provenance
1. Click on any alert in the **Alerts Log**.
2. Notice the **AI Model Provenance** section displaying:
   * Model Artifact SHA-256 hash (verifying untampered neural network weights).
   * Active rule coordinate configuration hash.
   * Runtime execution engine (e.g. `onnxruntime-cpu`).
3. Click **"Verify Merkle Proof"** (or execute `GET /alerts/{id}/merkle-proof`):
   * Calculates the binary Merkle inclusion path to the batch root.
   * Demonstrates independent $O(\log N)$ mathematical proof of existence without exposing full database contents.

### C. 2-of-3 Multisignature Blockchain Anchoring
1. Query active on-chain anchors via `GET /anchoring/status`.
2. Inspect the confirmed EVM block number, transaction hash, and sequence interval committed by Admin and Supervisor signature threshold consensus.

---

## 👤 Step 7: Test Role-Based Access Control (RBAC)

In the top bar, locate the **`ROLE`** switcher buttons:

| Role | What to Test |
| :--- | :--- |
| **`operator`** | Default monitoring view. Notice `Camera Config` in the sidebar has a lock icon and blocks access. |
| **`supervisor`** | Navigate to `Alerts Log` $\rightarrow$ the **`Export CSV`** button is now unlocked and downloads a CSV report. |
| **`admin`** | Unlocks full control. Click **`Camera Config`** in the sidebar $\rightarrow$ use the toggle switches to turn camera streams online or offline. |

---

## 💡 Troubleshooting Tips

* **Webcam Doesn't Turn On:** Make sure camera permissions are allowed in your browser address bar (look for the camera icon next to `http://localhost:3000`). Click `Start Webcam` to re-trigger.
* **Backend Disconnected / Fallback Mode:** Verify the FastAPI backend is running on `http://localhost:8000`. If offline, the frontend automatically switches to client-side simulated fallback mode.
* **Port 3000 in Use:** If port 3000 is occupied, Vite will assign port `5173`. Check your terminal output for the exact URL.
