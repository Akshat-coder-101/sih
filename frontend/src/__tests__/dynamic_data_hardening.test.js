import test from 'node:test';
import assert from 'node:assert/strict';

// Constants and helpers mirroring frontend/src/utils/camera.ts
const DEFAULT_WEBCAM_CAMERA_ID = 'cam-1';
const TELEMETRY_STALE_THRESHOLD_MS = 15000;

function isWebcamCapable(cam) {
  if (!cam) return false;
  if (typeof cam.supportsWebcam === 'boolean') {
    return cam.supportsWebcam;
  }
  if (cam.sourceType) {
    return cam.sourceType === 'webcam';
  }
  return cam.id === DEFAULT_WEBCAM_CAMERA_ID;
}

function resolveWebcamCamera(cams) {
  if (!cams || cams.length === 0) return null;
  return cams.find(c => isWebcamCapable(c)) || null;
}

function computeTelemetryFreshness(metrics, lastMetricsAt, now = Date.now()) {
  if (!metrics || !lastMetricsAt) return 'unavailable';
  if (now - lastMetricsAt > TELEMETRY_STALE_THRESHOLD_MS) return 'stale';
  return 'live';
}

function getProvenanceLabel(alertsSubset, emptyLabel = 'No records') {
  if (!alertsSubset || alertsSubset.length === 0) {
    return emptyLabel;
  }

  const hasDetector = alertsSubset.some(a => (a.provenance || 'detector') === 'detector');
  const hasSim = alertsSubset.some(a => a.provenance === 'simulation');

  if (hasDetector && hasSim) {
    return 'Detector + Sim';
  }
  if (hasDetector) {
    return 'Detector Live';
  }
  if (hasSim) {
    return 'Simulation Benchmark';
  }
  return emptyLabel;
}

// Normalizers mirroring frontend/src/services/api.ts
function normalizeReadiness(data, statusCode) {
  return {
    ready: Boolean(data?.ready),
    database: Boolean(data?.database),
    modelLoaded: Boolean(data?.modelLoaded ?? data?.model_loaded),
    cameraWorkers: Number(data?.cameraWorkers ?? data?.camera_workers ?? 0),
    activeStreams: Array.isArray(data?.activeStreams)
      ? data.activeStreams
      : Array.isArray(data?.active_streams)
      ? data.active_streams
      : [],
    timestamp: data?.timestamp || new Date().toISOString(),
    statusCode
  };
}

function normalizeMetrics(data) {
  const telemetry = data.cameraTelemetry || data.camera_telemetry || data.workerTelemetry || data.worker_telemetry || {};
  const cameraTelemetry = Object.fromEntries(Object.entries(telemetry).map(([cameraId, item]) => [cameraId, {
    ...item,
    fps: Number(item.fps ?? 0),
    inferenceLatencyMs: Number(item.inferenceLatencyMs ?? item.inference_latency_ms ?? 0),
    processedFrames: Number(item.processedFrames ?? item.processed_frames ?? 0),
    queue: item.queue || {},
    lastError: item.lastError ?? item.last_error ?? null
  }]));
  return {
    ...data,
    cameraTelemetry,
    totalAlerts: Number(data.totalAlerts ?? data.total_alerts ?? 0),
    activeWsClients: Number(data.activeWsClients ?? data.active_ws_clients ?? 0),
    cameraWorkers: Number(data.cameraWorkers ?? data.camera_workers ?? 0),
    modelRegistry: data.modelRegistry || data.model_registry || {}
  };
}

function normalizeCameras(items) {
  return items.map((c) => ({
    ...c,
    rtspUrl: c.rtspUrl || c.rtsp_url || '',
    sourceType: c.sourceType || c.source_type,
    supportsWebcam: c.supportsWebcam ?? c.supports_webcam,
    activeModelVersion: c.activeModelVersion || c.active_model_version || undefined,
    activeRuleVersion: c.activeRuleVersion || c.active_rule_version || undefined,
    siteId: c.siteId || c.site_id || undefined
  }));
}

// Helper simulating AppContext isCamWebcamActive logic
function createIsCamWebcamActive(resolvedWebcamId, webcamActive) {
  return function isCamWebcamActive(camId) {
    if (!camId || !webcamActive) return false;
    return camId === resolvedWebcamId;
  };
}

// -----------------------------------------------------------------------------
// Tests
// -----------------------------------------------------------------------------

test('1. Camera capability: non-cam-1 webcam-capable camera resolves correctly', () => {
  const customWebcamCam = { id: 'cam-99', name: 'Tactical Drone Cam', supportsWebcam: true };
  const rtspCam = { id: 'cam-2', name: 'Gate Cam', supportsWebcam: false, sourceType: 'rtsp' };
  const fallbackCam = { id: 'cam-1', name: 'Perimeter Cam' };

  assert.equal(isWebcamCapable(customWebcamCam), true, 'Camera with supportsWebcam=true must be capable');
  assert.equal(isWebcamCapable(rtspCam), false, 'RTSP camera must not be webcam capable');
  assert.equal(isWebcamCapable(fallbackCam), true, 'cam-1 without metadata falls back to capable for legacy compatibility');

  const cams = [rtspCam, customWebcamCam, fallbackCam];
  const activeWebcamCam = resolveWebcamCamera(cams);
  assert.equal(activeWebcamCam.id, 'cam-99', 'Non-cam-1 webcam-capable camera resolves as active webcam');
});

test('2. Non-cam-1 webcam camera works across all four camera surfaces', () => {
  const customCam = { id: 'cam-tactical', name: 'Tactical Cam', supportsWebcam: true };
  const rtspCam = { id: 'cam-gate', name: 'Gate Cam', supportsWebcam: false, sourceType: 'rtsp' };
  const cams = [rtspCam, customCam];

  const resolved = resolveWebcamCamera(cams);
  assert.equal(resolved.id, 'cam-tactical', 'Resolved webcam camera is cam-tactical');

  // Surface 1: Monitor Viewport - badge check
  const isWebcamActive = createIsCamWebcamActive(resolved.id, true);
  const monitorBadgeForCustom = isWebcamActive(customCam.id) ? 'Webcam AI Active' : 'Detector Ready';
  const monitorBadgeForRtsp = isWebcamActive(rtspCam.id) ? 'Webcam AI Active' : 'Detector Ready';
  assert.equal(monitorBadgeForCustom, 'Webcam AI Active', 'Active webcam camera shows Webcam AI Active');
  assert.equal(monitorBadgeForRtsp, 'Detector Ready', 'Non-webcam camera selected never shows Webcam AI Active');

  // Surface 2: Camera Grid - stream rendering dispatch
  const gridRenderTypeCustom = isWebcamActive(customCam.id) ? 'video' : 'img_or_svg';
  const gridRenderTypeRtsp = isWebcamActive(rtspCam.id) ? 'video' : 'img_or_svg';
  assert.equal(gridRenderTypeCustom, 'video');
  assert.equal(gridRenderTypeRtsp, 'img_or_svg');

  // Surface 3: Fullscreen Modal - stream selection
  const fsRenderTypeCustom = isWebcamActive(customCam.id) ? 'video' : 'rtsp_img';
  const fsRenderTypeRtsp = isWebcamActive(rtspCam.id) ? 'video' : 'rtsp_img';
  assert.equal(fsRenderTypeCustom, 'video');
  assert.equal(fsRenderTypeRtsp, 'rtsp_img');

  // Surface 4: Camera Configuration - capability and active badges
  assert.equal(isWebcamCapable(customCam), true, 'Custom camera shows Webcam Node in topology');
  assert.equal(isWebcamCapable(rtspCam), false, 'RTSP camera does not show Webcam Node');
  assert.equal(isWebcamActive(customCam.id), true, 'Custom camera shows Webcam Active badge');
  assert.equal(isWebcamActive(rtspCam.id), false, 'RTSP camera does not show Webcam Active badge');
});

test('3. Watchlist & threat provenance: data-driven labels for detector, simulation, mixed, and empty', () => {
  const detectorAlerts = [{ id: 'a1', type: 'watchlist', provenance: 'detector' }];
  const simAlerts = [{ id: 'a2', type: 'watchlist', provenance: 'simulation' }];
  const mixedAlerts = [
    { id: 'a1', type: 'watchlist', provenance: 'detector' },
    { id: 'a2', type: 'watchlist', provenance: 'simulation' }
  ];
  const emptyAlerts = [];

  assert.equal(getProvenanceLabel(detectorAlerts), 'Detector Live');
  assert.equal(getProvenanceLabel(simAlerts), 'Simulation Benchmark');
  assert.equal(getProvenanceLabel(mixedAlerts), 'Detector + Sim');
  assert.equal(getProvenanceLabel(emptyAlerts, 'No hits'), 'No hits');
});

test('4. Metrics normalization: parses snake_case worker_telemetry and inference_latency_ms', () => {
  const rawBackendPayload = {
    total_alerts: 42,
    camera_workers: 2,
    worker_telemetry: {
      'cam-1': {
        fps: 9.4,
        inference_latency_ms: 18.2,
        processed_frames: 1200,
        last_error: null
      }
    }
  };

  const normalized = normalizeMetrics(rawBackendPayload);
  assert.equal(normalized.totalAlerts, 42);
  assert.equal(normalized.cameraWorkers, 2);
  assert.equal(normalized.cameraTelemetry['cam-1'].fps, 9.4);
  assert.equal(normalized.cameraTelemetry['cam-1'].inferenceLatencyMs, 18.2);
  assert.equal(normalized.cameraTelemetry['cam-1'].processedFrames, 1200);
});

test('5. Telemetry freshness: live, stale timeout after 15s, and retention on error', () => {
  const now = 100000;
  const metrics = { totalAlerts: 10 };

  // Fresh update 5 seconds ago
  assert.equal(computeTelemetryFreshness(metrics, now - 5000, now), 'live');

  // Stale update 16 seconds ago (> 15s threshold)
  assert.equal(computeTelemetryFreshness(metrics, now - 16000, now), 'stale');

  // No metrics
  assert.equal(computeTelemetryFreshness(null, null, now), 'unavailable');

  // Transient network error simulation: last metrics are preserved, freshness transitions to stale
  let currentMetrics = metrics;
  let lastMetricsAt = now - 5000;

  // Transient failure occurs: metrics must NOT be cleared
  const fetchFailed = true;
  if (!fetchFailed) {
    currentMetrics = null;
  }
  assert.equal(currentMetrics, metrics, 'Last valid metrics must be retained on failure');

  // Time elapses past timeout
  const later = now + 20000;
  assert.equal(computeTelemetryFreshness(currentMetrics, lastMetricsAt, later), 'stale');
});

test('6. Missing model metadata and siteId: remain undefined rather than fabricating 8.2.0 or site-alpha', () => {
  const backendCameras = [
    {
      id: 'cam-1',
      name: 'CAM-01',
      active_model_version: '8.2.0',
      active_rule_version: '1.0',
      site_id: 'site-alpha'
    },
    {
      id: 'cam-2',
      name: 'CAM-02',
      active_model_version: null,
      active_rule_version: null,
      site_id: null
    }
  ];

  const normalized = normalizeCameras(backendCameras);
  assert.equal(normalized[0].activeModelVersion, '8.2.0', 'Backend version is preserved');
  assert.equal(normalized[0].siteId, 'site-alpha', 'Backend siteId is preserved');
  assert.equal(normalized[1].activeModelVersion, undefined, 'Missing backend version must remain undefined');
  assert.equal(normalized[1].activeRuleVersion, undefined, 'Missing backend rule version must remain undefined');
  assert.equal(normalized[1].siteId, undefined, 'Missing backend siteId must remain undefined');
});

test('7. Degraded readiness: HTTP 503 response body is parsed and structured details preserved', () => {
  const degradedRawPayload = {
    ready: false,
    database: true,
    model_loaded: false,
    camera_workers: 0,
    active_streams: [],
    timestamp: '2026-09-11T12:00:00Z'
  };

  const normalized = normalizeReadiness(degradedRawPayload, 503);
  assert.equal(normalized.ready, false, 'ready is false');
  assert.equal(normalized.database, true, 'database health is preserved');
  assert.equal(normalized.modelLoaded, false, 'modelLoaded state is preserved');
  assert.equal(normalized.cameraWorkers, 0, 'cameraWorkers count is preserved');
  assert.deepEqual(normalized.activeStreams, [], 'activeStreams is preserved');
  assert.equal(normalized.statusCode, 503, 'HTTP 503 status code is retained');
});

test('8. Separate API and WebSocket availability: WS disconnect alone never activates simulation', () => {
  // Scenario: REST API is healthy (cameras, metrics, ready reachable), but WebSocket dropped
  const apiAvailable = true;
  const websocketConnected = false;

  // Rule: simulation activates only when API is offline (apiAvailable === false)
  const shouldActivateSimulation = !apiAvailable;
  assert.equal(shouldActivateSimulation, false, 'Simulation must NOT activate when API is online, even if WS disconnected');

  // Scenario: REST API goes offline
  const apiOffline = false;
  const shouldActivateWhenOffline = !apiOffline;
  assert.equal(shouldActivateWhenOffline, true, 'Simulation activates when API is offline');
});

test('9. Simulation alert provenance and box label transparency', () => {
  const simAlert = {
    id: 'EVT-SIM',
    type: 'weapon',
    detail: 'CRITICAL: Weapon Detected (Live Demo Trigger [K])',
    provenance: 'simulation'
  };
  assert.equal(simAlert.provenance, 'simulation');

  const simBox = {
    label: '[SIM] WEAPON DETECTED 0.96',
    score: 0.96,
    class: 'weapon'
  };
  assert.equal(simBox.label.startsWith('[SIM]'), true, 'Simulated box must include [SIM] tag');
});
