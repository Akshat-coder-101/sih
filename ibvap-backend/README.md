# IBVAP Backend (Phase 1 + Phase 4 of the Antigravity build plan)

A working FastAPI backend for the IBVAP dashboard covering: real persistence,
JWT auth + RBAC, encryption at rest, a WebSocket alert feed, an audit log,
and the SHA-256 hash-chain tamper-evidence ledger (FR-9 and FR-10 from the
PRD). Video ingestion, YOLOv8 detection, ANPR, and face-watchlist matching
(Phase 2/3) are **not** in this drop — see "What's not here" below.

## Run it

```bash
cd ibvap-backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

On first run it creates `ibvap.db` (SQLite), generates an AES-256 key at
`.aes_key`, and seeds the same cameras/alerts your frontend was faking in
`AppContext.tsx`, plus three demo accounts (**change these before any real
deployment**):

| role | username | password |
|---|---|---|
| admin | admin | admin123 |
| supervisor | supervisor | supervisor123 |
| operator | operator | operator123 |

Interactive API docs: `http://localhost:8000/docs`

## Endpoint map

| Method | Path | Role | Notes |
|---|---|---|---|
| POST | `/auth/login` | — | returns JWT; locks account after 5 bad attempts (FR-9.5) |
| GET | `/cameras` | operator+ | |
| PATCH | `/cameras/{id}/toggle` | admin | |
| GET | `/alerts?type=&sev=&camId=&reviewed=` | operator+ | matches `AlertsLog.tsx` filters exactly |
| POST | `/alerts` | operator+ | writes DB row → appends to ledger → broadcasts over WS, in one request |
| PATCH | `/alerts/{id}/reviewed` | supervisor+ | |
| GET | `/ledger/verify` | operator+ | powers the "Verify Log Integrity" button (FR-8.6) |
| POST | `/ledger/tamper-demo/{alertId}` | admin | **demo-only**, edits a record bypassing the ledger so you can show Verify flip from intact→broken live |
| GET | `/audit-log` | supervisor+ | separate from the AI alert log, per FR-9.4 |
| WS | `/ws/alerts?token=...` | — | pushes `{event:"new_alert", data:{...}}` the instant an alert is created |

Every response uses **camelCase** field names (`camId`, `trackId`, `ts`,
`accessToken`, etc.) matching your existing `Camera`/`Alert` TypeScript
interfaces in `index.ts`, so the frontend swap is mostly "point fetch calls
here" rather than restructuring components.

## What's real vs. what this doesn't do

**Real:**
- Alerts and cameras persist in an actual database, survive restarts.
- `detail` and `snapshot` fields are AES-256-GCM encrypted at rest (FR-9.3) — you can `sqlite3 ibvap.db "select detail_enc from alerts limit 1;"` and see ciphertext, not plaintext.
- Passwords are hashed (pbkdf2_sha256), JWTs expire in 8h, RBAC is enforced server-side (tested: operator gets a real 403 hitting an admin route, not just a hidden UI button).
- The hash-chain ledger is genuinely recomputed from live DB rows on every `/ledger/verify` call — tested end-to-end above: seed data verifies intact, a live-created alert keeps it intact, and the `tamper-demo` endpoint (admin-only) breaks it at the exact record, which `/ledger/verify` correctly detects and reports.
- WebSocket broadcast tested: an alert posted via `/alerts` arrives on a connected `/ws/alerts` client in well under a second.

**Not real / not built (this is exactly Phase 2 and Phase 3 from the build plan):**
- No RTSP/video-file ingestion — there's nowhere yet for CAM-02/03/04 to get real frames from.
- No YOLOv8, no ByteTrack, no server-side inference at all. The frontend's client-side TF.js COCO-SSD loop for CAM-01's webcam is untouched by this backend and can keep running as-is, or you can point it at `POST /alerts` to persist its detections instead of calling `setAlerts` locally.
- No ANPR, no face/watchlist matching. The `anpr`/`watchlist` alert *types* are supported end-to-end (DB, ledger, encryption, RBAC) — you just don't have a model producing them yet. Post to `/alerts` with `type: "anpr"` and real plate text in `detail` once that model exists, and everything downstream (encryption, ledger, WS push, filtering, CSV export) already works.
- No TLS/SRTP wiring in this dev run (`uvicorn --reload` is plaintext HTTP). For the demo, put it behind an nginx reverse proxy with a self-signed cert to satisfy FR-9.1, or run `uvicorn --ssl-keyfile ... --ssl-certfile ...` directly.

## Wiring it into the existing React app

In `AppContext.tsx`:
1. Replace the `INITIAL_CAMS`/`INITIAL_ALERTS` constants with a `fetch('/cameras')` / `fetch('/alerts')` call on mount, storing the JWT (from a new login screen) in memory or `sessionStorage`.
2. Replace the 12-second `setInterval` random-alert generator with a `new WebSocket('ws://.../ws/alerts')` subscription that calls the existing `addAlert()` — no other component needs to change, since `addAlert` is already threaded through the whole app.
3. Replace `markReviewed`'s local `setAlerts` call with `PATCH /alerts/:id/reviewed`, then update local state from the response (or just let the next WS/poll refresh handle it).
4. Replace `toggleCamOnline`'s local `setCams` call with `PATCH /cameras/:id/toggle`.
5. Add the "Verify Log Integrity" button to `AlertsLog.tsx` next to "Export CSV", calling `GET /ledger/verify` and showing the result.
