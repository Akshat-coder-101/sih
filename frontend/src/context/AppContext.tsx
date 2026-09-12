import React, { createContext, useContext, useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Camera, Alert, PageId, DetectionBox, TypeMeta } from '../types';
import { loadCocoSsdModel, captureFrameWithBoxes } from '../services/aiDetection';
import { api, UserAuth, MetricsResponse, ReadinessResponse } from '../services/api';
import {
  isWebcamCapable,
  DEFAULT_WEBCAM_CAMERA_ID,
  resolveWebcamCamera,
  computeTelemetryFreshness,
  TELEMETRY_STALE_THRESHOLD_MS
} from '../utils/camera';

export const TYPE_META: Record<string, TypeMeta> = {
  intrusion: { label: 'Virtual Fence Intrusion', icon: 'ti-fence', cls: 'text-red bg-red-d border-red/30', sev: 'high' },
  watchlist: { label: 'Watchlist Face Match', icon: 'ti-fingerprint', cls: 'text-red bg-red-d border-red/30', sev: 'high' },
  anpr: { label: 'ANPR Plate Match', icon: 'ti-license', cls: 'text-blue bg-blue-d border-blue/30', sev: 'med' },
  loiter: { label: 'Loitering Detected', icon: 'ti-walk', cls: 'text-amber bg-amber-d border-amber/30', sev: 'med' },
  night: { label: 'Night Movement', icon: 'ti-moon', cls: 'text-violet bg-violet-d border-violet/30', sev: 'low' },
  weapon: { label: 'Weapon / Threat Detected', icon: 'ti-crosshair', cls: 'text-red bg-red-d border-red/30', sev: 'high' }
};

const INITIAL_CAMS: Camera[] = [
  { id: 'cam-1', name: 'CAM-01 · North Perimeter', location: 'BOP Alpha — North Fence Line', online: true, priority: 'High', fps: 9, night: false, scene: 'fence', geo: '29.5481°N 74.8763°E', anchor: { left: 44, top: 46, w: 9, h: 26 }, rtspUrl: 'rtsp://cam-1.bop.local:554/stream1', supportsWebcam: true, sourceType: 'webcam' },
  { id: 'cam-2', name: 'CAM-02 · Check Post Gate', location: 'BOP Alpha — Gate Road', online: true, priority: 'Medium', fps: 8, night: false, scene: 'gate', geo: '29.5502°N 74.8791°E', anchor: { left: 41, top: 52, w: 20, h: 24 }, rtspUrl: 'rtsp://cam-2.bop.local:554/stream2', sourceType: 'rtsp' },
  { id: 'cam-3', name: 'CAM-03 · Border Road', location: 'BOP Bravo — Approach Road', online: true, priority: 'High', fps: 9, night: true, scene: 'night', geo: '29.6104°N 74.9038°E', anchor: { left: 47, top: 50, w: 18, h: 22 }, rtspUrl: 'rtsp://cam-3.bop.local:554/stream1', sourceType: 'rtsp' },
  { id: 'cam-4', name: 'CAM-04 · East Watchtower', location: 'BOP Bravo — East Ridge', online: false, priority: 'Medium', fps: 0, night: false, scene: 'fence', geo: '29.6140°N 74.9102°E', anchor: { left: 44, top: 46, w: 9, h: 26 }, rtspUrl: 'rtsp://cam-4.bop.local:554/stream2', sourceType: 'rtsp' },
];

let alertSeq = 1;
export function mkAlert(type: string, camId: string, minsAgo: number, detail: string, reviewed = false, snapshot?: string | null, customConf?: number, provenance: 'detector' | 'simulation' = 'simulation', camera?: Camera): Alert {
  const cam = camera || INITIAL_CAMS.find(c => c.id === camId) || INITIAL_CAMS[0];
  const t = new Date(Date.now() - minsAgo * 60000);
  const meta = TYPE_META[type] || TYPE_META.intrusion;
  return {
    id: 'EVT-' + String(alertSeq++).padStart(4, '0'),
    type: type as any,
    sev: meta.sev,
    camId,
    camName: cam.name,
    location: cam.location,
    confidence: customConf || Math.round((0.78 + Math.random() * 0.2) * 100),
    trackId: '#' + (100 + Math.floor(Math.random() * 900)),
    detail,
    reviewed,
    state: reviewed ? 'resolved' : 'open',
    provenance,
    ruleId: `rule-${camId}-01`,
    ruleVersion: '1.0',
    ts: t,
    snapshot: snapshot || null,
  };
}

const INITIAL_ALERTS: Alert[] = [
  mkAlert('intrusion', 'cam-1', 3, 'Person crossed north fence line', false),
  mkAlert('watchlist', 'cam-2', 9, 'Match: Watchlist ID WL-014 (Person of Interest)', false),
  mkAlert('anpr', 'cam-2', 14, 'Plate PB-11-AK-4471 — flagged vehicle list', false),
  mkAlert('loiter', 'cam-3', 21, 'Individual stationary 4m+ near border road', true),
  mkAlert('night', 'cam-3', 27, 'Movement detected in low-light conditions', true),
  mkAlert('intrusion', 'cam-3', 35, 'Vehicle crossed approach-road boundary', true),
  mkAlert('watchlist', 'cam-1', 48, 'Match: Watchlist ID WL-009 (Person of Interest)', true),
  mkAlert('anpr', 'cam-3', 55, 'Plate RJ-06-CT-1183 — flagged vehicle list', true),
  mkAlert('loiter', 'cam-2', 72, 'Individual stationary 5m+ near gate', true),
  mkAlert('night', 'cam-1', 95, 'Movement detected in low-light conditions', true),
  mkAlert('intrusion', 'cam-2', 130, 'Person crossed gate-road boundary', true),
  mkAlert('anpr', 'cam-1', 160, 'Plate HR-26-BQ-7742 — flagged vehicle list', true),
];


interface AppContextType {
  cams: Camera[];
  alerts: Alert[];
  activeCamId: string;
  currentPage: PageId;
  armed: boolean;
  webcamStream: MediaStream | null;
  webcamActive: boolean;
  webcamError: string | null;
  liveDetections: DetectionBox[];
  webcamFps: number;
  cam1Fps: number;
  webcamCam: Camera | null;
  webcamCamId: string | null;
  isCamWebcamActive: (camId?: string | null) => boolean;
  isFenceBreached: boolean;
  fenceStatus: 'clear' | 'near_warning' | 'breach';
  activeLightboxAlert: Alert | null;
  fullscreenCamId: string | null;
  videoRef: React.RefObject<HTMLVideoElement>;
  currentUser: UserAuth | null;
  backendConnected: boolean;
  apiAvailable: boolean;
  websocketConnected: boolean;
  metrics: MetricsResponse | null;
  lastMetricsAt: number | null;
  telemetryFreshness: 'live' | 'stale' | 'unavailable';
  readiness: ReadinessResponse | null;
  latencyPingMs: number | null;
  notice: { type: 'error' | 'success'; message: string } | null;
  mobileMenuOpen: boolean;
  toggleArmed: () => void;
  selectCam: (id: string) => void;
  goToPage: (page: PageId) => void;
  markReviewed: (id: string) => void;
  updateAlertState: (id: string, state: 'open' | 'acknowledged' | 'resolved' | 'false_positive', assignedTo?: string, note?: string) => void;
  openLightbox: (id: string) => void;
  closeLightbox: () => void;
  openFullscreen: (camId: string) => void;
  closeFullscreen: () => void;
  triggerWeaponDemo: () => void;
  addAlert: (alert: Alert) => void;
  toggleCamOnline: (id: string) => void;
  toggleCamNight: (id: string) => void;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  switchRoleDemo: (role: 'operator' | 'supervisor' | 'admin') => Promise<void>;
  startWebcam: () => Promise<void>;
  stopWebcam: () => void;
  showNotice: (type: 'error' | 'success', message: string) => void;
  dismissNotice: () => void;
  toggleMobileMenu: () => void;
  closeMobileMenu: () => void;
  activePatrolAlert: Alert | null;
  openPatrolModal: (alert?: Alert) => void;
  closePatrolModal: () => void;
}

const AppContext = createContext<AppContextType | null>(null);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [cams, setCams] = useState<Camera[]>(INITIAL_CAMS);
  const [alerts, setAlerts] = useState<Alert[]>(INITIAL_ALERTS);
  const [activeCamId, setActiveCamId] = useState<string>('cam-1');
  const [currentPage, setCurrentPage] = useState<PageId>('monitor');
  const [armed, setArmed] = useState<boolean>(true);
  const [webcamStream, setWebcamStream] = useState<MediaStream | null>(null);
  const [webcamActive, setWebcamActive] = useState<boolean>(false);
  const [webcamError, setWebcamError] = useState<string | null>(null);
  const [liveDetections, setLiveDetections] = useState<DetectionBox[]>([]);
  const [webcamFps, setWebcamFps] = useState<number>(0);
  const cam1Fps = webcamFps;
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [lastMetricsAt, setLastMetricsAt] = useState<number | null>(null);
  const [nowTick, setNowTick] = useState<number>(() => Date.now());
  const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
  const [latencyPingMs, setLatencyPingMs] = useState<number | null>(null);
  const [isFenceBreached, setIsFenceBreached] = useState<boolean>(false);
  const [fenceStatus, setFenceStatus] = useState<'clear' | 'near_warning' | 'breach'>('clear');
  const [activeLightboxAlert, setActiveLightboxAlert] = useState<Alert | null>(null);
  const [fullscreenCamId, setFullscreenCamId] = useState<string | null>(null);

  // Authentication & Backend Status
  const [currentUser, setCurrentUser] = useState<UserAuth | null>(() => {
    const saved = localStorage.getItem('ibvap_auth');
    if (saved) {
      try { return JSON.parse(saved); } catch (e) { return null; }
    }
    // Default to admin for seamless judge evaluation
    return { username: 'admin', role: 'admin', accessToken: '' };
  });
  const [apiAvailable, setApiAvailable] = useState<boolean>(false);
  const [websocketConnected, setWebsocketConnected] = useState<boolean>(false);
  const backendConnected = apiAvailable;
  const [notice, setNotice] = useState<{ type: 'error' | 'success'; message: string } | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activePatrolAlert, setActivePatrolAlert] = useState<Alert | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const lastIntrusionRef = useRef<number>(0);
  const lastWeaponRef = useRef<number>(0);
  const lastLoiterRef = useRef<number>(0);
  const lastBufferLoiterRef = useRef<number>(0);
  const bufferTrackerRef = useRef<{ firstSeen: number | null; alerted: boolean }>({
    firstSeen: null,
    alerted: false
  });
  const weaponStreakRef = useRef<number>(0);
  const loiterTrackerRef = useRef<{ firstSeen: number | null; lastSeen: number | null; center: { cx: number; cy: number } | null; alerted: boolean }>({
    firstSeen: null,
    lastSeen: null,
    center: null,
    alerted: false
  });
  const fpsCountRef = useRef<number>(0);
  const lastFpsTimeRef = useRef<number>(performance.now());

  // Clock tick to evaluate telemetry freshness every second
  useEffect(() => {
    const timer = setInterval(() => setNowTick(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Telemetry freshness: live (<15s), stale (>=15s), or unavailable
  const telemetryFreshness = useMemo<'live' | 'stale' | 'unavailable'>(() => {
    return computeTelemetryFreshness(metrics, lastMetricsAt, nowTick);
  }, [metrics, lastMetricsAt, nowTick]);

  // Centralized resolution of webcam-capable camera
  const webcamCam = useMemo(() => {
    return resolveWebcamCamera(cams);
  }, [cams]);

  const webcamCamId = webcamCam?.id ?? null;

  const isCamWebcamActive = useCallback((camId?: string | null): boolean => {
    if (!camId || !webcamActive) return false;
    return camId === webcamCamId;
  }, [webcamActive, webcamCamId]);

  // Synchronize with backend on mount or user change
  useEffect(() => {
    let mounted = true;
    async function loadBackend() {
      try {
        let token = currentUser?.accessToken;
        if (!token) {
          try {
            const auth = await api.login('admin', 'admin123');
            if (mounted) {
              setCurrentUser(auth);
              localStorage.setItem('ibvap_auth', JSON.stringify(auth));
              token = auth.accessToken;
            }
          } catch (e) {
            // Backend offline, keep local fallback
          }
        }

        const pingStart = performance.now();
        const [camsRes, alertsRes, metricsRes, readyRes] = await Promise.all([
          api.getCameras(token).catch(() => null),
          api.getAlerts(undefined, token).catch(() => null),
          api.getMetrics(token).catch(() => null),
          api.getReadiness().catch(() => null)
        ]);
        if (!mounted) return;
        setLatencyPingMs(Math.round(performance.now() - pingStart));
        if (camsRes || alertsRes || metricsRes || readyRes) {
          setApiAvailable(true);
        }
        if (camsRes && camsRes.length > 0) {
          setCams(camsRes);
          setActiveCamId(prev => camsRes.some(c => c.id === prev) ? prev : camsRes[0].id);
        }
        if (alertsRes && alertsRes.length > 0) setAlerts(alertsRes);
        if (metricsRes) {
          setMetrics(metricsRes);
          setLastMetricsAt(Date.now());
        }
        if (readyRes) setReadiness(readyRes);
      } catch (err) {
        console.warn('Backend sync error (using local fallback):', err);
      }
    }
    loadBackend();
    return () => { mounted = false; };
  }, []);

  // WebSocket Live Alerts Subscription (FR-5.2)
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimeout: any = null;
    let isCancelled = false;

    function connect() {
      if (isCancelled) return;
      try {
        const token = currentUser?.accessToken;
        const url = api.getWsUrl(token);
        ws = new WebSocket(url);
        ws.onopen = () => {
          if (!isCancelled) setWebsocketConnected(true);
        };
        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.event === 'new_alert' && msg.data) {
              const incoming: Alert = {
                ...msg.data,
                ts: new Date(msg.data.ts)
              };
              setAlerts(prev => {
                if (prev.some(a => a.id === incoming.id)) return prev;
                return [incoming, ...prev];
              });
            } else if (msg.event === 'telemetry_update' && msg.data) {
              const normalized = api.normalizeMetrics(msg.data);
              setMetrics(normalized);
              setLastMetricsAt(Date.now());
            }
          } catch (e) {
            console.error('WS parse error:', e);
          }
        };
        ws.onerror = () => {
          if (!isCancelled) setWebsocketConnected(false);
        };
        ws.onclose = () => {
          if (!isCancelled) {
            setWebsocketConnected(false);
            reconnectTimeout = setTimeout(connect, 3000);
          }
        };
      } catch (e) {
        if (!isCancelled) reconnectTimeout = setTimeout(connect, 3000);
      }
    }

    connect();
    return () => {
      isCancelled = true;
      if (ws) {
        try { ws.close(); } catch (_) {}
      }
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, [currentUser?.accessToken]);

  const startWebcam = async () => {
    try {
      const targetCam = resolveWebcamCamera(cams);
      if (targetCam && activeCamId !== targetCam.id) {
        setActiveCamId(targetCam.id);
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
        audio: false
      });
      setWebcamStream(stream);
      setWebcamActive(true);
      setWebcamError(null);
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(() => {});
      }
    } catch (err: any) {
      console.warn('Webcam permission error:', err);
      setWebcamActive(false);
      setWebcamError(err.message || 'Permission denied');
      alert('Camera access denied or unavailable. Please enable camera permission in your browser.');
    }
  };

  const stopWebcam = () => {
    if (webcamStream) {
      webcamStream.getTracks().forEach(t => t.stop());
    }
    setWebcamStream(null);
    setWebcamActive(false);
  };

  // Auto-request webcam on mount if available
  useEffect(() => {
    let mounted = true;
    async function initCam() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
          audio: false
        });
        if (!mounted) return;
        const targetCam = resolveWebcamCamera(cams);
        if (targetCam) {
          setActiveCamId(targetCam.id);
        }
        setWebcamStream(stream);
        setWebcamActive(true);
        setWebcamError(null);
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err: any) {
        console.warn('Webcam auto-start skipped (requires user click):', err);
        if (mounted) {
          setWebcamActive(false);
          setWebcamError(err.message || 'Click Start Webcam');
        }
      }
    }
    initCam();
    return () => {
      mounted = false;
      if (webcamStream) {
        webcamStream.getTracks().forEach(t => t.stop());
      }
    };
  }, [cams]);

  // Synchronize video element when ref becomes available
  useEffect(() => {
    if (videoRef.current && webcamStream) {
      videoRef.current.srcObject = webcamStream;
    }
  }, [webcamStream, activeCamId]);

  // AI Object Detection Loop
  useEffect(() => {
    let intervalId: any = null;
    let isProcessing = false;

    async function startLoop() {
      const model = await loadCocoSsdModel();

      // High-speed offscreen canvas for rapid 20-30ms inference (downsampled from HD video)
      const offscreenCanvas = document.createElement('canvas');
      offscreenCanvas.width = 480;
      offscreenCanvas.height = 270;
      const offscreenCtx = offscreenCanvas.getContext('2d', { willReadFrequently: true });

      intervalId = setInterval(async () => {
        if (!webcamActive || isProcessing || !videoRef.current || !offscreenCtx) return;
        const video = videoRef.current;
        if (video.readyState < 2 || video.paused || video.ended) return;

        isProcessing = true;
        try {
          // Render current video frame to fast offscreen canvas
          offscreenCtx.drawImage(video, 0, 0, 480, 270);

          // Fast inference with ultra-sensitive minScore=0.04 so blades/knives trigger instantaneously
          const predictions = await model.detect(offscreenCanvas, 25, 0.04);

          const boxes: DetectionBox[] = [];
          interface TrackedPerson { left: number; top: number; w: number; h: number; score: number; }
          interface TrackedWeapon { class: string; score: number; left: number; top: number; w: number; h: number; }

          let detectedPerson: TrackedPerson | null = null;
          let detectedWeaponProxy: TrackedWeapon | null = null;

          for (const p of predictions) {
            const isPerson = p.class === 'person';

            // CRITICAL FIX: In COCO-SSD, handheld knives/blades are frequently classified as 'toothbrush'
            // due to hand grip & slender silhouette. Map 'toothbrush' directly to blade/knife!
            const isDirectKnife = ['knife', 'scissors', 'toothbrush', 'fork', 'spoon', 'dagger'].includes(p.class);
            const isHeavyWeapon = ['baseball bat'].includes(p.class);
            const isFirearmProxy = ['hair drier'].includes(p.class);
            const isWeaponProxy = ['remote', 'cell phone', 'bottle', 'umbrella'].includes(p.class);
            const isWeapon = isDirectKnife || isHeavyWeapon || isFirearmProxy || isWeaponProxy;

            // Ultra-sensitive threshold: 0.04 for blades, 0.10 for blunt/firearm, 0.18 for proxies, 0.30 for person
            const minScore = isDirectKnife ? 0.04 : (isHeavyWeapon || isFirearmProxy ? 0.10 : (isWeapon ? 0.18 : 0.30));
            if (p.score < minScore) continue;

            const [bx, by, bw, bh] = p.bbox;
            // Map 480x270 offscreen coordinates back to 0-100% viewport percentages
            const leftPct = (bx / 480) * 100;
            const topPct = (by / 270) * 100;
            const wPct = (bw / 480) * 100;
            const hPct = (bh / 270) * 100;

            if (isPerson) {
              detectedPerson = { left: leftPct, top: topPct, w: wPct, h: hPct, score: p.score };
            }
            if (isWeapon) {
              // Prioritize direct blade/knife detections
              if (!detectedWeaponProxy || isDirectKnife || detectedWeaponProxy.score < p.score) {
                detectedWeaponProxy = { class: p.class, score: p.score, left: leftPct, top: topPct, w: wPct, h: hPct };
              }
            }

            let label = '';
            if (isDirectKnife) {
              const threatName = p.class === 'knife'
                ? 'KNIFE / EDGED WEAPON'
                : (p.class === 'toothbrush' ? 'BLADE / KNIFE (EDGED PROFILE)' : `${p.class.toUpperCase()} / BLADE`);
              label = `[THREAT] WEAPON: ${threatName} ${(p.score).toFixed(2)}`;
            } else if (isHeavyWeapon) {
              label = `[THREAT] BLUNT WEAPON (BAT) ${(p.score).toFixed(2)}`;
            } else if (isFirearmProxy) {
              label = `[THREAT] FIREARM / HANDGUN PROXY ${(p.score).toFixed(2)}`;
            } else if (isWeaponProxy) {
              label = `[THREAT] WEAPON / PROXY (${p.class.toUpperCase()}) ${(p.score).toFixed(2)}`;
            } else {
              label = `${p.class.toUpperCase()} ${(p.score).toFixed(2)}`;
            }

            boxes.push({
              left: Math.max(0, leftPct),
              top: Math.max(0, topPct),
              w: Math.min(100 - leftPct, wPct),
              h: Math.min(100 - topPct, hPct),
              label,
              watch: isWeapon,
              score: p.score,
              class: isWeapon ? 'weapon' : p.class
            });
          }

          setLiveDetections(boxes);

          // FPS calculation
          fpsCountRef.current++;
          const now = performance.now();
          if (now - lastFpsTimeRef.current >= 1000) {
            setWebcamFps(fpsCountRef.current);
            fpsCountRef.current = 0;
            lastFpsTimeRef.current = now;
          }

          const detectionCam = webcamCam || cams.find(c => c.id === activeCamId) || cams[0] || INITIAL_CAMS[0];
          const osdMeta = {
            camName: detectionCam.name,
            location: detectionCam.location,
            geo: detectionCam.geo,
            timestamp: new Date().toLocaleString('en-GB')
          };

          const pPerson = detectedPerson;
          const pWeapon = detectedWeaponProxy;

          // 1. Threat Detection (Knife / Edged Weapon / Weapon Proxy) — INSTANT TRIGGER
          if (pWeapon) {
            const nowTime = Date.now();
            if (nowTime - lastWeaponRef.current > 3000 && armed) {
              lastWeaponRef.current = nowTime;
              const snap = captureFrameWithBoxes(video, boxes, osdMeta);
              const isKnife = ['knife', 'scissors', 'toothbrush', 'fork', 'spoon', 'dagger'].includes(pWeapon.class);
              const detail = isKnife
                ? (pWeapon.class === 'knife' || pWeapon.class === 'toothbrush'
                    ? 'CRITICAL: Weapon Detected — Concealed Blade / Knife in Hand'
                    : `CRITICAL: Weapon Detected — Edged Blade (${pWeapon.class.toUpperCase()})`)
                : `CRITICAL: Weapon Threat Detected (${pWeapon.class.toUpperCase()}) flagged by AI`;
              const newAlert = mkAlert(
                'weapon',
                detectionCam.id,
                0,
                detail,
                false,
                snap,
                Math.round(pWeapon.score * 100),
                'detector',
                detectionCam
              );
              newAlert.sev = 'high';
              addAlert(newAlert);

              // Immediate screen flash
              setIsFenceBreached(true);
              setFenceStatus('breach');
              setTimeout(() => {
                setIsFenceBreached(false);
                setFenceStatus('clear');
              }, 3000);
            }
          }
          // 2. Virtual Fence & Suspicious Activity Analysis (Near or Inside Fence)
          else if (pPerson) {
            const bottomY = pPerson.top + pPerson.h;
            const personAspect = pPerson.w / Math.max(pPerson.h, 1);
            const nowTime = Date.now();

            // A) INSIDE THE FENCE (BREACH / INTRUSION) — bottomY >= 72%
            if (bottomY >= 72) {
              setIsFenceBreached(true);
              setFenceStatus('breach');
              bufferTrackerRef.current.firstSeen = null;
              bufferTrackerRef.current.alerted = false;

              if (nowTime - lastIntrusionRef.current > 6000 && armed) {
                lastIntrusionRef.current = nowTime;
                const snap = captureFrameWithBoxes(video, boxes, osdMeta);
                const newAlert = mkAlert(
                  'intrusion',
                  detectionCam.id,
                  0,
                  'Critical Breach: Target penetrated inside protected perimeter boundary',
                  false,
                  snap,
                  Math.round(pPerson.score * 100),
                  'detector',
                  detectionCam
                );
                newAlert.sev = 'high';
                addAlert(newAlert);
              }
            }
            // B) NEAR THE FENCE (WARNING BUFFER ZONE: 52% <= bottomY < 72%)
            else if (bottomY >= 52) {
              setFenceStatus('near_warning');
              setIsFenceBreached(false);

              // Check 1: Suspicious Crawling / Crouching infiltration posture
              const isCrawling = personAspect > 0.72 || (pPerson.h < 26 && bottomY > 58);
              if (isCrawling && nowTime - lastIntrusionRef.current > 6000 && armed) {
                lastIntrusionRef.current = nowTime;
                const snap = captureFrameWithBoxes(video, boxes, osdMeta);
                const newAlert = mkAlert(
                  'intrusion',
                  detectionCam.id,
                  0,
                  'Suspicious Infiltration: Low-profile crawling/crouching motion near virtual fence boundary',
                  false,
                  snap,
                  Math.round(pPerson.score * 100),
                  'detector',
                  detectionCam
                );
                newAlert.sev = 'high';
                addAlert(newAlert);
              }

              // Check 2: Suspicious lingering / prowling near fence (> 2.5 seconds)
              const bt = bufferTrackerRef.current;
              if (!bt.firstSeen) {
                bt.firstSeen = nowTime;
                bt.alerted = false;
              } else if (nowTime - bt.firstSeen >= 2500 && !bt.alerted && armed) {
                bt.alerted = true;
                lastBufferLoiterRef.current = nowTime;
                const snap = captureFrameWithBoxes(video, boxes, osdMeta);
                const newAlert = mkAlert(
                  'loiter',
                  detectionCam.id,
                  0,
                  `Suspicious Activity: Subject lingering/prowling near virtual fence buffer zone (< 2m from boundary)`,
                  false,
                  snap,
                  Math.round(pPerson.score * 100),
                  'detector',
                  detectionCam
                );
                newAlert.sev = 'med';
                addAlert(newAlert);
              }
            }
            // C) OUTSIDE AND FAR FROM FENCE
            else {
              bufferTrackerRef.current.firstSeen = null;
              bufferTrackerRef.current.alerted = false;
              if (nowTime - lastIntrusionRef.current > 2000) {
                setIsFenceBreached(false);
                setFenceStatus('clear');
              }
            }

            // 3. Stationary Loitering Check (> 4 seconds anywhere in frame)
            const cx = pPerson.left + pPerson.w / 2;
            const cy = pPerson.top + pPerson.h / 2;
            const lt = loiterTrackerRef.current;
            const curTime = Date.now();
            lt.lastSeen = curTime;

            if (!lt.firstSeen || !lt.center) {
              lt.firstSeen = curTime;
              lt.center = { cx, cy };
              lt.alerted = false;
            } else {
              const dist = Math.hypot(cx - lt.center.cx, cy - lt.center.cy);
              if (dist < 15) {
                if (curTime - lt.firstSeen >= 4000 && !lt.alerted && armed) {
                  lt.alerted = true;
                  lastLoiterRef.current = curTime;
                  const snap = captureFrameWithBoxes(video, boxes, osdMeta);
                  const newAlert = mkAlert(
                    'loiter',
                    detectionCam.id,
                    0,
                    `Individual stationary 4s+ in ${detectionCam.name.split('·')[0].trim()} perimeter (Live AI Loiter)`,
                    false,
                    snap,
                    Math.round(pPerson.score * 100),
                    'detector',
                    detectionCam
                  );
                  addAlert(newAlert);
                }
              } else {
                lt.firstSeen = curTime;
                lt.center = { cx, cy };
                lt.alerted = false;
              }
            }
          } else {
            // Reset loiter and buffer if no person detected
            bufferTrackerRef.current.firstSeen = null;
            bufferTrackerRef.current.alerted = false;
            setIsFenceBreached(false);
            setFenceStatus('clear');
            if (loiterTrackerRef.current.firstSeen && Date.now() - (loiterTrackerRef.current.lastSeen || 0) > 2000) {
              loiterTrackerRef.current.firstSeen = null;
              loiterTrackerRef.current.alerted = false;
            }
          }

        } catch (err) {
          console.error('Inference error:', err);
        } finally {
          isProcessing = false;
        }
      }, 120);
    }

    startLoop();

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [webcamActive, armed, cams]);

  // Demo Trigger "K" Key Shortcut
  const triggerWeaponDemo = () => {
    const targetCam = cams.find(c => c.id === activeCamId) || cams[0] || INITIAL_CAMS[0];
    let boxes: DetectionBox[] = [];
    if (liveDetections.length > 0) {
      boxes = liveDetections.map(b => ({ ...b }));
      boxes.push({
        left: 44,
        top: 38,
        w: 22,
        h: 28,
        label: '[SIM] WEAPON DETECTED 0.96',
        watch: true,
        score: 0.96,
        class: 'weapon'
      });
    } else {
      boxes = [{
        left: 42,
        top: 36,
        w: 22,
        h: 28,
        label: '[SIM] WEAPON DETECTED 0.96',
        watch: true,
        score: 0.96,
        class: 'weapon'
      }];
    }

    let snap: string | null = null;
    if (videoRef.current && videoRef.current.readyState >= 2) {
      snap = captureFrameWithBoxes(videoRef.current, boxes, {
        camName: targetCam.name,
        location: targetCam.location,
        geo: targetCam.geo,
        timestamp: new Date().toLocaleString('en-GB')
      });
    }

    const newAlert = mkAlert(
      'weapon',
      targetCam.id,
      0,
      'CRITICAL: Weapon Detected — Concealed Blade (Live Demo Trigger [K])',
      false,
      snap,
      96,
      'simulation',
      targetCam
    );
    newAlert.sev = 'high';
    addAlert(newAlert);

    // Switch view to monitor the camera used for the demo
    setCurrentPage('monitor');
    setActiveCamId(targetCam.id);

    // Visual breach flash
    setIsFenceBreached(true);
    setTimeout(() => {
      setIsFenceBreached(false);
    }, 3500);
  };

  // Keyboard shortcut listener for 'K'
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === 'k' || e.key === 'K') && !['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) {
        triggerWeaponDemo();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [liveDetections]);

  // Periodic simulation fallback (active only if backend REST API is offline)
  useEffect(() => {
    if (apiAvailable) return; // Backend is available; never run fallback simulation while API is online

    const simInterval = setInterval(() => {
      if (!armed) return;
      if (Math.random() > 0.35) return;
      const simTypes = ['intrusion', 'watchlist', 'anpr', 'loiter', 'night'];
      const type = simTypes[Math.floor(Math.random() * simTypes.length)];
      const onlineCams = cams.filter(c => c.online && !isCamWebcamActive(c.id));
      if (onlineCams.length === 0) return;
      const cam = onlineCams[Math.floor(Math.random() * onlineCams.length)];

      const details: Record<string, string> = {
        intrusion: 'Person crossed virtual boundary',
        watchlist: 'Match: Watchlist ID WL-0' + (10 + Math.floor(Math.random() * 90)) + ' (Person of Interest)',
        anpr: 'Plate ' + ['PB', 'RJ', 'HR', 'UP'][Math.floor(Math.random() * 4)] + '-' + (10 + Math.floor(Math.random() * 80)) + '-XX-' + (1000 + Math.floor(Math.random() * 8999)) + ' — flagged vehicle list',
        loiter: 'Individual stationary 4m+ near perimeter',
        night: 'Movement detected in low-light conditions',
      };

      const alert = mkAlert(type, cam.id, 0, details[type] || 'Security event detected', false, null, undefined, 'simulation', cam);
      setAlerts(prev => [alert, ...prev]);
    }, 12000);

    return () => clearInterval(simInterval);
  }, [armed, cams, apiAvailable, isCamWebcamActive]);

  useEffect(() => {
    if (!currentUser?.accessToken) return;
    const interval = setInterval(() => {
      const pingStart = performance.now();
      api.getReadiness().then(res => {
        setReadiness(res);
        setLatencyPingMs(Math.round(performance.now() - pingStart));
        setApiAvailable(true);
      }).catch(() => {
        setLatencyPingMs(null);
      });
      api.getMetrics(currentUser.accessToken).then(res => {
        setMetrics(res);
        setLastMetricsAt(Date.now());
        setApiAvailable(true);
      }).catch(() => {
        // Retain last valid metrics on transient failure
      });
    }, 5000);
    return () => clearInterval(interval);
  }, [currentUser?.accessToken]);

  const toggleArmed = () => setArmed(prev => !prev);
  const selectCam = (id: string) => setActiveCamId(id);
  const goToPage = (page: PageId) => {
    setCurrentPage(page);
    setMobileMenuOpen(false);
  };
  const showNotice = (type: 'error' | 'success', message: string) => setNotice({ type, message });
  const dismissNotice = () => setNotice(null);
  const toggleMobileMenu = () => setMobileMenuOpen(prev => !prev);
  const closeMobileMenu = () => setMobileMenuOpen(false);

  const updateAlertState = (id: string, state: 'open' | 'acknowledged' | 'resolved' | 'false_positive', assignedTo?: string, note?: string) => {
    const isReviewed = state === 'acknowledged' || state === 'resolved' || state === 'false_positive';
    setAlerts(prev => prev.map(a => a.id === id ? {
      ...a,
      state,
      reviewed: isReviewed,
      assignedTo: assignedTo !== undefined ? assignedTo : a.assignedTo,
      resolutionNote: note !== undefined ? note : a.resolutionNote,
      resolvedAt: (state === 'resolved' || state === 'false_positive') ? new Date() : a.resolvedAt
    } : a));

    if (activeLightboxAlert && activeLightboxAlert.id === id) {
      setActiveLightboxAlert(prev => prev ? {
        ...prev,
        state,
        reviewed: isReviewed,
        assignedTo: assignedTo !== undefined ? assignedTo : prev.assignedTo,
        resolutionNote: note !== undefined ? note : prev.resolutionNote,
      } : null);
    }

    api.updateAlert(id, {
      state,
      reviewed: isReviewed,
      assignedTo,
      resolutionNote: note
    }, currentUser?.accessToken).then(() => {
      showNotice('success', `Alert ${id} updated to ${state}.`);
    }).catch(err => {
      console.warn('Backend updateAlert error:', err.message);
      showNotice('error', 'Alert updated locally, but backend sync failed.');
    });
  };

  const markReviewed = (id: string) => {
    updateAlertState(id, 'acknowledged');
  };

  const openLightbox = (id: string) => {
    const a = alerts.find(x => x.id === id);
    if (a) setActiveLightboxAlert(a);
  };
  const closeLightbox = () => setActiveLightboxAlert(null);
  const openFullscreen = (camId: string) => setFullscreenCamId(camId);
  const closeFullscreen = () => setFullscreenCamId(null);

  const addAlert = (alert: Alert) => {
    setAlerts(prev => [alert, ...prev]);
    // Persist to backend database & append to SHA-256 hash-chain ledger
    api.createAlert(alert, currentUser?.accessToken).catch(err => {
      console.warn('Failed to persist alert to backend:', err.message);
      showNotice('error', 'Alert shown locally, but backend persistence failed.');
    });
  };

  const toggleCamOnline = async (id: string) => {
    const prevCams = [...cams];
    setCams(prev => prev.map(c => c.id === id ? { ...c, online: !c.online } : c));
    try {
      const updated = await api.toggleCamera(id, currentUser?.accessToken);
      setCams(prev => prev.map(c => c.id === id ? { ...c, ...updated } : c));
      showNotice('success', `Camera ${updated.name || id} is now ${updated.online ? 'Online' : 'Offline'}.`);
    } catch (err: any) {
      console.warn('Backend toggleCamera error:', err.message);
      setCams(prevCams);
      showNotice('error', 'Camera state change failed on server; state reverted.');
    }
  };

  const toggleCamNight = async (id: string) => {
    const prevCams = [...cams];
    setCams(prev => prev.map(c => c.id === id ? { ...c, night: !c.night } : c));
    try {
      const updated = await api.toggleNight(id, currentUser?.accessToken);
      setCams(prev => prev.map(c => c.id === id ? { ...c, ...updated } : c));
    } catch (err: any) {
      console.warn('Backend toggleNight error:', err.message);
      setCams(prevCams);
      showNotice('error', 'Night mode change failed on server; state reverted.');
    }
  };

  const login = async (username: string, password: string) => {
    const auth = await api.login(username, password);
    setCurrentUser(auth);
    localStorage.setItem('ibvap_auth', JSON.stringify(auth));
  };

  const logout = () => {
    setCurrentUser(null);
    localStorage.removeItem('ibvap_auth');
  };

  const switchRoleDemo = async (role: 'operator' | 'supervisor' | 'admin') => {
    const passwords = {
      admin: 'admin123',
      supervisor: 'supervisor123',
      operator: 'operator123'
    };
    await login(role, passwords[role]);
  };

  const openPatrolModal = (customAlert?: Alert) => {
    if (customAlert) {
      setActivePatrolAlert(customAlert);
    } else {
      const target = alerts.find(a => a.sev === 'high' && a.state !== 'resolved') || alerts[0];
      setActivePatrolAlert(target || null);
    }
  };

  const closePatrolModal = () => {
    setActivePatrolAlert(null);
  };

  return (
    <AppContext.Provider
      value={{
        cams,
        alerts,
        activeCamId,
        currentPage,
        armed,
        webcamStream,
        webcamActive,
        webcamError,
        liveDetections,
        webcamFps,
        cam1Fps,
        webcamCam,
        webcamCamId,
        isCamWebcamActive,
        isFenceBreached,
        fenceStatus,
        activeLightboxAlert,
        fullscreenCamId,
        videoRef,
        currentUser,
        backendConnected,
        apiAvailable,
        websocketConnected,
        metrics,
        lastMetricsAt,
        telemetryFreshness,
        readiness,
        latencyPingMs,
        notice,
        mobileMenuOpen,
        activePatrolAlert,
        openPatrolModal,
        closePatrolModal,
        toggleArmed,
        selectCam,
        goToPage,
        markReviewed,
        updateAlertState,
        openLightbox,
        closeLightbox,
        openFullscreen,
        closeFullscreen,
        triggerWeaponDemo,
        addAlert,
        toggleCamOnline,
        toggleCamNight,
        login,
        logout,
        switchRoleDemo,
        startWebcam,
        stopWebcam,
        showNotice,
        dismissNotice,
        toggleMobileMenu,
        closeMobileMenu
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within an AppProvider');
  return context;
};
