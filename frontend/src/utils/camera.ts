import { Camera, Alert } from '../types';

/**
 * Centralized fallback camera ID for webcam binding when camera records
 * do not explicitly declare source capability.
 */
export const DEFAULT_WEBCAM_CAMERA_ID = 'cam-1';

/**
 * Named freshness threshold: telemetry without updates for >15s is marked stale.
 */
export const TELEMETRY_STALE_THRESHOLD_MS = 15000;

/**
 * Determines whether a camera is capable of acting as the edge browser webcam input.
 * Priority:
 * 1. Explicit `supportsWebcam` flag (boolean)
 * 2. Explicit `sourceType === 'webcam'`
 * 3. Centralized legacy fallback to DEFAULT_WEBCAM_CAMERA_ID
 */
export function isWebcamCapable(cam: Camera | null | undefined): boolean {
  if (!cam) return false;
  if (typeof cam.supportsWebcam === 'boolean') {
    return cam.supportsWebcam;
  }
  if (cam.sourceType) {
    return cam.sourceType === 'webcam';
  }
  return cam.id === DEFAULT_WEBCAM_CAMERA_ID;
}

/**
 * Resolves the primary webcam-capable camera from a list of cameras.
 */
export function resolveWebcamCamera(cams: Camera[]): Camera | null {
  if (!cams || cams.length === 0) return null;
  return cams.find(c => isWebcamCapable(c)) || null;
}

/**
 * Computes telemetry freshness based on metrics payload and timestamp age.
 */
export function computeTelemetryFreshness(
  metrics: unknown,
  lastMetricsAt: number | null,
  now: number = Date.now()
): 'live' | 'stale' | 'unavailable' {
  if (!metrics || !lastMetricsAt) return 'unavailable';
  if (now - lastMetricsAt > TELEMETRY_STALE_THRESHOLD_MS) return 'stale';
  return 'live';
}

/**
 * Derives a truthful provenance label from an array of alert records.
 * - All detector origin -> 'Detector Live'
 * - All simulation origin -> 'Simulation Benchmark'
 * - Mixed detector + simulation -> 'Detector + Sim'
 * - Empty set -> emptyLabel || 'No records'
 */
export function getProvenanceLabel(alertsSubset: Alert[], emptyLabel = 'No records'): string {
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

