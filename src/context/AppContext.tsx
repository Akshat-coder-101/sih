import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { Camera, Alert, PageId, DetectionBox, TypeMeta } from '../types';
import { loadCocoSsdModel, captureFrameWithBoxes } from '../services/aiDetection';

export const TYPE_META: Record<string, TypeMeta> = {
  intrusion: { label: 'Virtual Fence Intrusion', icon: 'ti-fence', cls: 'text-red bg-red-d border-red/30', sev: 'high' },
  watchlist: { label: 'Watchlist Face Match', icon: 'ti-fingerprint', cls: 'text-red bg-red-d border-red/30', sev: 'high' },
  anpr: { label: 'ANPR Plate Match', icon: 'ti-license', cls: 'text-blue bg-blue-d border-blue/30', sev: 'med' },
  loiter: { label: 'Loitering Detected', icon: 'ti-walk', cls: 'text-amber bg-amber-d border-amber/30', sev: 'med' },
  night: { label: 'Night Movement', icon: 'ti-moon', cls: 'text-violet bg-violet-d border-violet/30', sev: 'low' },
  weapon: { label: 'Weapon / Threat Detected', icon: 'ti-crosshair', cls: 'text-red bg-red-d border-red/30', sev: 'high' }
};

const INITIAL_CAMS: Camera[] = [
  { id: 'cam-1', name: 'CAM-01 · North Perimeter', location: 'BOP Alpha — North Fence Line', online: true, priority: 'High', fps: 9, night: false, scene: 'fence', geo: '29.5481°N 74.8763°E', anchor: { left: 44, top: 46, w: 9, h: 26 }, rtspUrl: 'rtsp://cam-1.bop.local:554/stream1' },
  { id: 'cam-2', name: 'CAM-02 · Check Post Gate', location: 'BOP Alpha — Gate Road', online: true, priority: 'Medium', fps: 8, night: false, scene: 'gate', geo: '29.5502°N 74.8791°E', anchor: { left: 41, top: 52, w: 20, h: 24 }, rtspUrl: 'rtsp://cam-2.bop.local:554/stream2' },
  { id: 'cam-3', name: 'CAM-03 · Border Road', location: 'BOP Bravo — Approach Road', online: true, priority: 'High', fps: 9, night: true, scene: 'night', geo: '29.6104°N 74.9038°E', anchor: { left: 47, top: 50, w: 18, h: 22 }, rtspUrl: 'rtsp://cam-3.bop.local:554/stream1' },
  { id: 'cam-4', name: 'CAM-04 · East Watchtower', location: 'BOP Bravo — East Ridge', online: false, priority: 'Medium', fps: 0, night: false, scene: 'fence', geo: '29.6140°N 74.9102°E', anchor: { left: 44, top: 46, w: 9, h: 26 }, rtspUrl: 'rtsp://cam-4.bop.local:554/stream2' },
];

let alertSeq = 1;
export function mkAlert(type: string, camId: string, minsAgo: number, detail: string, reviewed = false, snapshot?: string | null, customConf?: number): Alert {
  const cam = INITIAL_CAMS.find(c => c.id === camId) || INITIAL_CAMS[0];
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
  cam1Fps: number;
  isFenceBreached: boolean;
  activeLightboxAlert: Alert | null;
  fullscreenCamId: string | null;
  videoRef: React.RefObject<HTMLVideoElement>;
  toggleArmed: () => void;
  selectCam: (id: string) => void;
  goToPage: (page: PageId) => void;
  markReviewed: (id: string) => void;
  openLightbox: (id: string) => void;
  closeLightbox: () => void;
  openFullscreen: (camId: string) => void;
  closeFullscreen: () => void;
  triggerWeaponDemo: () => void;
  addAlert: (alert: Alert) => void;
  toggleCamOnline: (id: string) => void;
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
  const [cam1Fps, setCam1Fps] = useState<number>(0);
  const [isFenceBreached, setIsFenceBreached] = useState<boolean>(false);
  const [activeLightboxAlert, setActiveLightboxAlert] = useState<Alert | null>(null);
  const [fullscreenCamId, setFullscreenCamId] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement>(null);
  const lastIntrusionRef = useRef<number>(0);
  const lastWeaponRef = useRef<number>(0);
  const lastLoiterRef = useRef<number>(0);
  const loiterTrackerRef = useRef<{ firstSeen: number | null; lastSeen: number | null; center: { cx: number; cy: number } | null; alerted: boolean }>({
    firstSeen: null,
    lastSeen: null,
    center: null,
    alerted: false
  });
  const fpsCountRef = useRef<number>(0);
  const lastFpsTimeRef = useRef<number>(performance.now());

  // Initialize Webcam
  useEffect(() => {
    let mounted = true;
    async function initCam() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
          audio: false
        });
        if (!mounted) return;
        setWebcamStream(stream);
        setWebcamActive(true);
        setWebcamError(null);
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (err: any) {
        console.warn('Webcam permission not granted or device offline:', err);
        if (mounted) {
          setWebcamActive(false);
          setWebcamError(err.message || 'Permission denied');
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
  }, []);

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

      intervalId = setInterval(async () => {
        if (!webcamActive || isProcessing || !videoRef.current) return;
        const video = videoRef.current;
        if (video.readyState < 2 || video.paused || video.ended) return;

        isProcessing = true;
        try {
          const predictions = await model.detect(video);
          const vw = video.videoWidth || 1280;
          const vh = video.videoHeight || 720;

          const boxes: DetectionBox[] = [];
          interface TrackedPerson { left: number; top: number; w: number; h: number; score: number; }
          interface TrackedWeapon { class: string; score: number; left: number; top: number; w: number; h: number; }

          let detectedPerson: TrackedPerson | null = null;
          let detectedWeaponProxy: TrackedWeapon | null = null;

          for (const p of predictions) {
            if (p.score < 0.40) continue;
            const [bx, by, bw, bh] = p.bbox;
            const leftPct = (bx / vw) * 100;
            const topPct = (by / vh) * 100;
            const wPct = (bw / vw) * 100;
            const hPct = (bh / vh) * 100;

            const isPerson = p.class === 'person';
            const isWeapon = ['knife', 'scissors', 'cell phone'].includes(p.class);

            if (isPerson) {
              detectedPerson = { left: leftPct, top: topPct, w: wPct, h: hPct, score: p.score };
            }
            if (isWeapon) {
              detectedWeaponProxy = { class: p.class, score: p.score, left: leftPct, top: topPct, w: wPct, h: hPct };
            }

            const label = isWeapon
              ? (p.class === 'knife' ? `WEAPON (KNIFE) ${(p.score).toFixed(2)}` : `OBJECT PROXY (${p.class.toUpperCase()}) ${(p.score).toFixed(2)}`)
              : `${p.class.toUpperCase()} ${(p.score).toFixed(2)}`;

            boxes.push({
              left: Math.max(0, leftPct),
              top: Math.max(0, topPct),
              w: Math.min(100 - leftPct, wPct),
              h: Math.min(100 - topPct, hPct),
              label,
              watch: isWeapon,
              score: p.score,
              class: p.class
            });
          }

          setLiveDetections(boxes);

          // FPS calculation
          fpsCountRef.current++;
          const now = performance.now();
          if (now - lastFpsTimeRef.current >= 1000) {
            setCam1Fps(fpsCountRef.current);
            fpsCountRef.current = 0;
            lastFpsTimeRef.current = now;
          }

          const osdMeta = {
            camName: 'CAM-01 · North Perimeter',
            location: 'BOP Alpha — North Fence Line',
            geo: '29.5481°N 74.8763°E',
            timestamp: new Date().toLocaleString('en-GB')
          };

          const pPerson = detectedPerson;
          const pWeapon = detectedWeaponProxy;

          // 1. Virtual Fence Crossing Check (Y >= 72%)
          if (pPerson) {
            const bottomY = pPerson.top + pPerson.h;
            if (bottomY >= 72) {
              setIsFenceBreached(true);
              const nowTime = Date.now();
              if (nowTime - lastIntrusionRef.current > 8000 && armed) {
                lastIntrusionRef.current = nowTime;
                const snap = captureFrameWithBoxes(video, boxes, osdMeta);
                const newAlert = mkAlert(
                  'intrusion',
                  'cam-1',
                  0,
                  'Virtual fence boundary crossed by individual (Live AI Detection)',
                  false,
                  snap,
                  Math.round(pPerson.score * 100)
                );
                setAlerts(prev => [newAlert, ...prev]);
              }
            } else {
              if (Date.now() - lastIntrusionRef.current > 2000) {
                setIsFenceBreached(false);
              }
            }

            // 2. Stationary Loitering Check (> 4 seconds)
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
                    'cam-1',
                    0,
                    'Individual stationary 4s+ in CAM-01 perimeter (Live AI Loiter)',
                    false,
                    snap,
                    Math.round(pPerson.score * 100)
                  );
                  setAlerts(prev => [newAlert, ...prev]);
                }
              } else {
                lt.firstSeen = curTime;
                lt.center = { cx, cy };
                lt.alerted = false;
              }
            }
          } else {
            // Reset loiter if person left
            if (loiterTrackerRef.current.firstSeen && Date.now() - (loiterTrackerRef.current.lastSeen || 0) > 2000) {
              loiterTrackerRef.current.firstSeen = null;
              loiterTrackerRef.current.alerted = false;
            }
          }

          // 3. Threat Proxy Detection
          if (pWeapon) {
            const nowTime = Date.now();
            if (nowTime - lastWeaponRef.current > 8000 && armed) {
              lastWeaponRef.current = nowTime;
              const snap = captureFrameWithBoxes(video, boxes, osdMeta);
              const isKnife = pWeapon.class === 'knife';
              const detail = isKnife
                ? 'CRITICAL: Weapon Detected (Blade / Edged Weapon)'
                : `CRITICAL: Threat Proxy Object (${pWeapon.class.toUpperCase()}) flagged by AI`;
              const newAlert = mkAlert(
                'weapon',
                'cam-1',
                0,
                detail,
                false,
                snap,
                Math.round(pWeapon.score * 100)
              );
              newAlert.sev = 'high';
              setAlerts(prev => [newAlert, ...prev]);
            }
          }

        } catch (err) {
          console.error('Inference error:', err);
        } finally {
          isProcessing = false;
        }
      }, 350);
    }

    startLoop();

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [webcamActive, armed]);

  // Demo Trigger "K" Key Shortcut
  const triggerWeaponDemo = () => {
    let boxes: DetectionBox[] = [];
    if (liveDetections.length > 0) {
      boxes = liveDetections.map(b => ({ ...b }));
      boxes.push({
        left: 44,
        top: 38,
        w: 22,
        h: 28,
        label: 'WEAPON DETECTED 0.96',
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
        label: 'WEAPON DETECTED 0.96',
        watch: true,
        score: 0.96,
        class: 'weapon'
      }];
    }

    let snap: string | null = null;
    if (videoRef.current && videoRef.current.readyState >= 2) {
      snap = captureFrameWithBoxes(videoRef.current, boxes, {
        camName: 'CAM-01 · North Perimeter',
        location: 'BOP Alpha — North Fence Line',
        geo: '29.5481°N 74.8763°E',
        timestamp: new Date().toLocaleString('en-GB')
      });
    }

    const newAlert = mkAlert(
      'weapon',
      'cam-1',
      0,
      'CRITICAL: Weapon Detected — Concealed Blade (Live Demo Trigger [K])',
      false,
      snap,
      96
    );
    newAlert.sev = 'high';
    setAlerts(prev => [newAlert, ...prev]);

    // Switch view to monitor CAM-01 so audience instantly observes
    setCurrentPage('monitor');
    setActiveCamId('cam-1');

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

  // Periodic simulation for simulated cameras
  useEffect(() => {
    const simInterval = setInterval(() => {
      if (!armed) return;
      if (Math.random() > 0.35) return;
      const simTypes = ['intrusion', 'watchlist', 'anpr', 'loiter', 'night'];
      const type = simTypes[Math.floor(Math.random() * simTypes.length)];
      const onlineCams = cams.filter(c => c.online && c.id !== 'cam-1');
      if (onlineCams.length === 0) return;
      const cam = onlineCams[Math.floor(Math.random() * onlineCams.length)];

      const details: Record<string, string> = {
        intrusion: 'Person crossed virtual boundary',
        watchlist: 'Match: Watchlist ID WL-0' + (10 + Math.floor(Math.random() * 90)) + ' (Person of Interest)',
        anpr: 'Plate ' + ['PB', 'RJ', 'HR', 'UP'][Math.floor(Math.random() * 4)] + '-' + (10 + Math.floor(Math.random() * 80)) + '-XX-' + (1000 + Math.floor(Math.random() * 8999)) + ' — flagged vehicle list',
        loiter: 'Individual stationary 4m+ near perimeter',
        night: 'Movement detected in low-light conditions',
      };

      const alert = mkAlert(type, cam.id, 0, details[type] || 'Security event detected', false);
      setAlerts(prev => [alert, ...prev]);
    }, 12000);

    return () => clearInterval(simInterval);
  }, [armed, cams]);

  const toggleArmed = () => setArmed(prev => !prev);
  const selectCam = (id: string) => setActiveCamId(id);
  const goToPage = (page: PageId) => setCurrentPage(page);
  const markReviewed = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, reviewed: true } : a));
    if (activeLightboxAlert && activeLightboxAlert.id === id) {
      setActiveLightboxAlert(prev => prev ? { ...prev, reviewed: true } : null);
    }
  };
  const openLightbox = (id: string) => {
    const a = alerts.find(x => x.id === id);
    if (a) setActiveLightboxAlert(a);
  };
  const closeLightbox = () => setActiveLightboxAlert(null);
  const openFullscreen = (camId: string) => setFullscreenCamId(camId);
  const closeFullscreen = () => setFullscreenCamId(null);
  const addAlert = (alert: Alert) => setAlerts(prev => [alert, ...prev]);
  const toggleCamOnline = (id: string) => {
    setCams(prev => prev.map(c => c.id === id ? { ...c, online: !c.online } : c));
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
        cam1Fps,
        isFenceBreached,
        activeLightboxAlert,
        fullscreenCamId,
        videoRef,
        toggleArmed,
        selectCam,
        goToPage,
        markReviewed,
        openLightbox,
        closeLightbox,
        openFullscreen,
        closeFullscreen,
        triggerWeaponDemo,
        addAlert,
        toggleCamOnline
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
