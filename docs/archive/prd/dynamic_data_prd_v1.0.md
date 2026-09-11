# IBVAP Dynamic Operations Data PRD

## 1. Objective

Replace presentation-only values with data derived from the backend, active camera state, browser sensors, or clearly labelled simulation. The command center must never display a seeded location, camera identity, performance value, or operational status as if it were live when it is not.

## 2. Scope

This requirement applies to the monitor, camera grid, alerts log, evidence modal, analytics, AI pipeline, sidebar, topbar, configuration, and operational modals.

## 3. Data Source Contract

| UI data | Source of truth | Refresh rule | Fallback |
| --- | --- | --- | --- |
| Camera name, location, coordinates, scene, status, priority | `GET /cameras` | Initial load and after camera mutations | Local seed data labelled as offline/demo state |
| Alert camera name and location | Alert response, joined from camera metadata on creation | WebSocket event or alert refresh | Existing alert payload only |
| Alert counts and threat breakdown | `GET /alerts` plus WebSocket events | On initial load and every incoming event | Local state with a disconnected indicator |
| Worker FPS, processed frames, latency, queue status | `GET /metrics` | Initial load and every 5 seconds while connected | `n/a` or camera metadata, explicitly labelled |
| Backend readiness, model state, active streams | `GET /ready` | On startup and when connection status changes | `Unknown` |
| Current time | Browser clock | Once per second where displayed | None |
| Browser webcam state and detector FPS | `MediaStream` and local detector loop | On stream/detector updates | `Detector Ready` or permission error |
| Terrain and tactical recommendation | Alert-specific backend endpoints | When an evidence modal opens | Omit the panel and show unavailable state |

## 4. Functional Requirements

### FR-DATA-1: Camera identity

1. Every camera-facing view MUST render name, location, and coordinates from the selected camera record.
2. Generated alerts, evidence snapshots, OSD overlays, demo events, and fallback alerts MUST use the camera record associated with the event.
3. Code MUST NOT assume `cam-1` when a selected or event camera is available.

### FR-DATA-2: Live telemetry

1. The frontend MUST consume `/metrics` for worker FPS, inference latency, worker count, queue telemetry, and last worker error.
2. Analytics MUST calculate average latency from available camera workers rather than display a fixed benchmark.
3. The AI pipeline MUST show current telemetry when connected and `n/a` or an explicitly labelled metadata fallback when disconnected.
4. Telemetry refresh failures MUST NOT replace the last known value with fabricated data.

### FR-DATA-3: Synchronization

1. Camera and alert data MUST be loaded from the backend after authentication.
2. WebSocket alerts MUST be merged by event ID without duplicates.
3. Local mutations MUST optimistically update the UI and reconcile with the backend response or show a sync error.
4. A disconnected backend MUST be visible through existing connection/status UI.

### FR-DATA-4: Simulation transparency

1. Simulation is allowed only when the backend is unavailable or an explicit demo action is used.
2. Simulated alerts MUST carry `provenance: simulation`.
3. Simulated values MUST NOT be labelled as measured, live, or production telemetry.
4. Seed records are permitted only as an offline bootstrap and MUST be replaced by backend records when available.

### FR-DATA-5: Empty and degraded states

1. Empty collections MUST render an intentional empty state instead of invented rows.
2. Missing telemetry MUST render `n/a`, `Unknown`, or an equivalent explicit state.
3. Missing coordinates MUST render `Location unavailable`, not a copied coordinate.
4. Offline cameras MUST not display online stream telemetry.

## 5. Acceptance Criteria

- Changing a camera's location in the backend is reflected in the monitor, grid, evidence modal, generated alert, and fullscreen OSD after refresh.
- Selecting another camera changes all camera identity labels and event metadata that are tied to the selection.
- Changing backend worker latency or FPS changes Analytics and AI Pipeline values within one refresh interval.
- With `/metrics` unavailable, no fixed latency or throughput value is presented as measured live data.
- A simulated fallback alert is visibly distinguishable by provenance and never claims detector origin.
- The frontend production build passes and backend PRD suites remain green.

## 6. Delivery Plan

### Phase 1: Shared data paths

- Centralize camera metadata usage in `AppContext`.
- Add typed `/metrics` API access and periodic refresh.
- Remove hard-coded camera identity from generated evidence and monitor labels.

### Phase 2: Surface audit

- Audit sidebar, topbar, configuration, patrol, evidence, and legal/about surfaces for remaining operational constants.
- Replace fixed operational values with backend fields or explicit unavailable states.
- Add automated checks for forbidden hard-coded live labels.

### Phase 3: Verification

- Add frontend component tests for camera-location propagation and telemetry fallback.
- Add an API integration test for `/metrics` shape and refresh behavior.
- Verify camera mutation, alert creation, WebSocket ingestion, and degraded backend behavior end to end.
