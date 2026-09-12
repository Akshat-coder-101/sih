import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';
import { api, SingleFrameAnalysis } from '../../services/api';
import { isWebcamCapable } from '../../utils/camera';

export const CamViewport: React.FC = () => {
  const {
    cams,
    activeCamId,
    selectCam,
    webcamActive,
    webcamError,
    videoRef,
    liveDetections,
    webcamFps,
    isCamWebcamActive,
    telemetryFreshness,
    isFenceBreached,
    fenceStatus,
    openFullscreen,
    triggerWeaponDemo,
    toggleCamNight,
    startWebcam,
    currentUser,
    metrics,
    backendConnected,
    apiAvailable
  } = useApp();

  const [simBoxes, setSimBoxes] = useState<any[]>([]);
  const [timeStamp, setTimeStamp] = useState<string>('');
  
  // Single-frame inspection & stepping states
  const [frozenFrameUrl, setFrozenFrameUrl] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [analysisResult, setAnalysisResult] = useState<SingleFrameAnalysis | null>(null);
  const [stepInfo, setStepInfo] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const cam = cams.find(c => c.id === activeCamId) || cams[0];

  // Capture single frame
  const handleCaptureSingleFrame = async () => {
    if (frozenFrameUrl) {
      // Resume live
      setFrozenFrameUrl(null);
      setAnalysisResult(null);
      setStepInfo(null);
      return;
    }
    try {
      setIsProcessing(true);
      const url = `${api.getSingleFrameUrl(cam.id, currentUser?.accessToken)}&t=${Date.now()}`;
      setFrozenFrameUrl(url);
      setStepInfo(`Captured instantaneous snapshot at ${new Date().toLocaleTimeString()}`);
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  // Step 1 frame forward
  const handleStepFrame = async () => {
    try {
      setIsProcessing(true);
      const result = await api.stepFrame(cam.id, currentUser?.accessToken);
      const url = `${api.getSingleFrameUrl(cam.id, currentUser?.accessToken)}&t=${Date.now()}`;
      setFrozenFrameUrl(url);
      setStepInfo(`Stepped to Frame #${result.frameIndex} (${result.detectionsCount} detections)`);
    } catch (e) {
      console.error(e);
    } finally {
      setIsProcessing(false);
    }
  };

  // Upload frame for synchronous YOLO analysis
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setIsProcessing(true);
      const objectUrl = URL.createObjectURL(file);
      setFrozenFrameUrl(objectUrl);
      const res = await api.processSingleFrame(cam.id, file, currentUser?.accessToken);
      setAnalysisResult(res);
      setStepInfo(`Processed in ${res.processingTimeMs}ms (${res.numDetections} objects detected)`);
    } catch (err: any) {
      alert(`Frame analysis error: ${err.message}`);
    } finally {
      setIsProcessing(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStamp(d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + ' ' + d.toLocaleTimeString('en-IN', { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Jitter for simulated cams (only when backend is offline and not using webcam)
  useEffect(() => {
    if (!cam || !cam.online || isCamWebcamActive(cam.id) || apiAvailable) {
      setSimBoxes([]);
      return;
    }

    const updateSim = () => {
      const a = cam.anchor;
      const isWatch = Math.random() < 0.15;
      const jitter = () => (Math.random() - 0.5) * 2;
      setSimBoxes([{
        left: a.left + jitter(),
        top: a.top + jitter(),
        w: a.w,
        h: a.h,
        label: isWatch ? '[SIM] WATCHLIST 0.9' + Math.floor(Math.random() * 9) : (cam.scene === 'gate' ? '[SIM] VEHICLE 0.' + (80 + Math.floor(Math.random() * 18)) : '[SIM] PERSON 0.' + (80 + Math.floor(Math.random() * 18))),
        watch: isWatch
      }]);
    };

    updateSim();
    const interval = setInterval(updateSim, 3000);
    return () => clearInterval(interval);
  }, [activeCamId, cam?.online, isCamWebcamActive, apiAvailable]);

  if (!cam) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6 text-center text-rind-500">
        <i className="ti ti-video-off text-4xl mb-2"></i>
        <div className="text-sm font-bold text-rind-200">No Cameras Configured</div>
        <div className="text-xs text-rind-500 mt-1">Register edge cameras or connect to backend.</div>
      </div>
    );
  }

  const isCurrentCamWebcam = isCamWebcamActive(cam.id);
  const displayedBoxes = isCurrentCamWebcam ? liveDetections : simBoxes;

  const personCount = isCurrentCamWebcam
    ? displayedBoxes.filter(b => b.class === 'person').length
    : (analysisResult && analysisResult.camId === cam.id)
    ? analysisResult.detections.filter(d => d.className.toLowerCase() === 'person').length
    : null;

  const vehicleCount = isCurrentCamWebcam
    ? displayedBoxes.filter(b => ['car', 'truck', 'bus', 'motorcycle', 'bicycle'].includes(b.class || '')).length
    : (analysisResult && analysisResult.camId === cam.id)
    ? analysisResult.detections.filter(d => ['car', 'truck', 'bus', 'motorcycle', 'bicycle'].includes(d.className.toLowerCase())).length
    : null;

  const currentFps = isCurrentCamWebcam
    ? (webcamFps || 0)
    : !cam.online
    ? 0
    : (metrics?.cameraTelemetry?.[cam.id]?.fps ?? cam.fps);

  return (
    <div className="flex-1 flex flex-col overflow-hidden p-3 gap-2 min-w-0">
      {/* Cam Bar */}
      <div className="flex items-center gap-2 shrink-0 flex-wrap">
        <span className="text-xs font-bold text-rind-300 font-display">Surveillance Feeds</span>

        <div className="mr-auto flex items-center gap-1.5">
          <span className="bg-instrument-d border border-instrument-400/25 px-2 py-0.5 rounded-full text-[9.5px] text-instrument-400 font-mono font-semibold flex items-center gap-1">
            <i className="ti ti-cpu text-xs"></i>
            {cam.name.split('·')[0].trim()}: {isCamWebcamActive(cam.id) ? 'Webcam AI Active' : (cam.online ? 'Detector Ready' : 'Feed Offline')}
          </span>
        </div>

        {/* Camera Selector Tabs */}
        <div className="flex items-center gap-1.5 overflow-x-auto max-w-full pb-0.5">
          {cams.map(c => (
            <button
              key={c.id}
              type="button"
              onClick={() => selectCam(c.id)}
              className={`flex items-center rounded-full border transition-all cursor-pointer overflow-hidden ${
                c.id === activeCamId
                  ? 'border-instrument-400/50 bg-instrument-d text-instrument-400 font-semibold'
                  : c.online
                  ? 'border-rind-500/20 bg-ink-800 text-rind-300 hover:text-rind-100 hover:border-rind-500/40'
                  : 'border-rind-500/10 bg-ink-800 text-rind-500 opacity-60'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ml-2.5 shrink-0 ${c.online ? 'bg-leaf-500 shadow-[0_0_6px_#65d68b]' : 'bg-melon-500'}`} />
              <span className="text-[10.5px] px-2.5 pr-3 py-1 whitespace-nowrap">
                {c.name.split('·')[0].trim()}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Main Viewport Box */}
      <div className="flex-1 min-h-0 bg-ink-900 border border-rind-500/20 rounded-rad overflow-hidden flex flex-col shadow-[0_8px_40px_rgba(0,0,0,0.5)]">
        {/* Header */}
        <div className="flex items-center gap-2.5 px-3.5 py-2.5 shrink-0 bg-ink-850 border-b border-rind-500/15">
          <div className={`w-2 h-2 rounded-full shrink-0 ${cam.online ? 'bg-leaf-500 shadow-[0_0_8px_#65d68b] animate-pulse-glow' : 'bg-melon-500'}`} />
          <div className="text-xs font-bold font-display text-rind-100 flex-1 truncate">
            {cam.name}
          </div>
          <div className="text-[11px] text-rind-500 hidden sm:block truncate">
            {cam.location}
          </div>

          {/* Single Frame Capture & Stepping Controls */}
          {cam.online && (
            <div className="flex items-center gap-1.5">
              {/* Freeze Snapshot button */}
              <button
                onClick={handleCaptureSingleFrame}
                className={`text-[9.5px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-rad3 border flex items-center gap-1 transition-colors ${
                  frozenFrameUrl ? 'bg-melon-900 text-melon-300 border-melon-500/40' : 'bg-ink-800 text-rind-400 border-rind-500/20 hover:text-rind-100'
                }`}
                title={frozenFrameUrl ? "Resume Live Video Stream" : "Capture Instantaneous Single Frame"}
              >
                <i className={`ti ${frozenFrameUrl ? 'ti-player-play' : 'ti-camera'} text-[11px]`}></i>
                <span>{frozenFrameUrl ? 'Resume Live' : 'Freeze Frame'}</span>
              </button>

              {/* Step frame button */}
              <button
                onClick={handleStepFrame}
                disabled={isProcessing}
                className="text-[9.5px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-rad3 border bg-ink-800 text-rind-400 border-rind-500/20 hover:text-rind-100 flex items-center gap-1 transition-colors"
                title="Advance exactly 1 frame forward"
              >
                <i className="ti ti-player-skip-forward text-[11px]"></i>
                <span className="hidden md:inline">Step 1F</span>
              </button>

              {/* Upload single frame for YOLO analysis */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isProcessing}
                className="text-[9.5px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-rad3 border bg-ink-800 text-rind-400 border-rind-500/20 hover:text-rind-100 flex items-center gap-1 transition-colors"
                title="Upload Image for Single-Frame YOLO Inference"
              >
                <i className="ti ti-upload text-[11px]"></i>
                <span className="hidden md:inline">Analyze Image</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
          )}

          {/* Night Mode Toggle Button */}
          {cam.online && (
            <button
              onClick={() => toggleCamNight(cam.id)}
              className={`text-[9.5px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-rad3 border flex items-center gap-1 transition-colors ${
                cam.night ? 'bg-violet-d text-violet border-violet/30' : 'bg-ink-800 text-rind-500 border-rind-500/20 hover:text-rind-100'
              }`}
              title="Toggle Low-Light Night Vision Filter"
            >
              <i className={`ti ${cam.night ? 'ti-moon-stars' : 'ti-sun'} text-[11px]`}></i>
              <span className="hidden sm:inline">{cam.night ? 'IR Night Active' : 'Optical Day'}</span>
            </button>
          )}

          <span className={`text-[9.5px] font-bold uppercase tracking-wide px-2 py-0.5 rounded-rad3 border ${
            cam.online
              ? isCurrentCamWebcam
                ? 'bg-leaf-900 text-leaf-500 border-leaf-500/30'
                : 'bg-instrument-d text-instrument-400 border-instrument-400/30'
              : 'bg-melon-d text-melon-500 border-melon-500/30'
          }`}>
            {cam.online ? (isCurrentCamWebcam ? 'AI DETECTOR LIVE' : 'LIVE STREAM') : 'OFFLINE'}
          </span>
        </div>

        {/* Viewport Area */}
        <div className={`flex-1 relative bg-ink-950 min-h-0 overflow-hidden ${cam.night ? 'radial-night' : ''}`}>
          {/* Frozen Frame / Uploaded Image View */}
          {frozenFrameUrl && (
            <div className="absolute inset-0 z-10 bg-black flex items-center justify-center">
              <img
                src={frozenFrameUrl}
                alt="Frozen Single Frame"
                className="w-full h-full object-contain"
              />
              
              {/* Single Frame Analysis Bounding Boxes */}
              {analysisResult?.detections?.map((d, i) => (
                <div
                  key={i}
                  className="dbox threat"
                  style={{
                    left: `${d.normalizedBox[0] * 100}%`,
                    top: `${d.normalizedBox[1] * 100}%`,
                    width: `${(d.normalizedBox[2] - d.normalizedBox[0]) * 100}%`,
                    height: `${(d.normalizedBox[3] - d.normalizedBox[1]) * 100}%`,
                    zIndex: 15
                  }}
                >
                  <div className="dbox-tag">{d.className.toUpperCase()} {Math.round(d.confidence * 100)}%</div>
                </div>
              ))}

              {/* Frozen Banner */}
              <div className="absolute top-3 left-1/2 -translate-x-1/2 z-20 flex items-center gap-2 bg-melon-900/90 border border-melon-500/40 px-3 py-1 rounded-rad text-xs text-melon-100 font-mono shadow-lg">
                <span className="w-2 h-2 rounded-full bg-melon-500 animate-pulse"></span>
                <span>SINGLE FRAME INSPECTION</span>
                {stepInfo && <span className="text-rind-300 text-[11px]">· {stepInfo}</span>}
                <button
                  onClick={handleCaptureSingleFrame}
                  className="ml-2 bg-ink-900/80 hover:bg-ink-800 text-rind-100 px-2 py-0.5 rounded text-[10px] border border-rind-500/30"
                >
                  Resume Live
                </button>
              </div>
            </div>
          )}
          {/* Real Webcam Video Stream for the selected camera */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`absolute inset-0 w-full h-full object-cover z-0 ${isCurrentCamWebcam ? 'block' : 'hidden'}`}
          />

          {/* Live MJPEG Stream for RTSP feeds from FastAPI Backend */}
          {!isCurrentCamWebcam && cam.online && (
            <img
              src={api.getStreamUrl(cam.id)}
              alt={cam.name}
              className="absolute inset-0 w-full h-full object-cover z-0"
              onError={(e) => {
                // Fallback to SVG if backend stream is not reached
                (e.currentTarget as HTMLElement).style.display = 'none';
                const fb = document.getElementById(`svg-fb-${cam.id}`);
                if (fb) fb.style.display = 'block';
              }}
            />
          )}

          {/* SVG Illustrated Fallback Scene */}
          {!isCurrentCamWebcam && cam.online && (
            <div
              id={`svg-fb-${cam.id}`}
              className="absolute inset-0 z-0 hidden"
              dangerouslySetInnerHTML={{ __html: getSceneSvg(cam.scene) }}
            />
          )}

          {/* Webcam Activation Overlay for webcam-capable cameras */}
          {isWebcamCapable(cam) && !webcamActive && cam.online && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/80 backdrop-blur-sm gap-3 p-5 text-center">
              <div className="w-12 h-12 rounded-full bg-instrument-d border border-instrument-400/30 text-instrument-400 flex items-center justify-center text-xl shadow-[0_0_20px_rgba(86,199,217,0.25)]">
                <i className="ti ti-camera"></i>
              </div>
              <div>
                <div className="text-sm font-bold font-display text-rind-100">Enable Webcam for Live Detector Inference</div>
                <div className="text-[11px] text-rind-300 max-w-[320px] mt-1">
                  Activate camera feed to test real-time knife, blade, perimeter intrusion, and loitering analytics.
                </div>
              </div>
              <button
                onClick={startWebcam}
                className="px-4 py-2 rounded-rad3 bg-instrument-400 hover:bg-instrument-500 text-ink-950 font-bold text-xs transition-all flex items-center gap-1.5 shadow-[0_0_15px_rgba(86,199,217,0.35)] cursor-pointer active:scale-95"
              >
                <i className="ti ti-video text-sm"></i>
                Start Webcam
              </button>
            </div>
          )}

          {/* Offline Screen */}
          {!cam.online && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-2 bg-[repeating-linear-gradient(135deg,#101313,#101313_10px,#171b1a_10px,#171b1a_20px)]">
              <i className="ti ti-video-off text-4xl text-rind-500"></i>
              <div className="text-xs text-melon-500 font-bold">Camera Offline</div>
              <div className="text-[10.5px] text-rind-500">Stream disconnected (BOP Network Failure)</div>
            </div>
          )}

          {/* Vignette & Scanlines */}
          <div className="cv-vignette absolute inset-0 z-[1]" />
          <div className="scanlines absolute inset-0 z-[2]" />

          {/* Tactical Corner Reticles */}
          <div className="absolute top-2.5 left-2.5 w-5 h-5 border-t-2 border-l-2 border-instrument-400 z-[4] pointer-events-none opacity-80" />
          <div className="absolute top-2.5 right-2.5 w-5 h-5 border-t-2 border-r-2 border-instrument-400 z-[4] pointer-events-none opacity-80" />
          <div className="absolute bottom-2.5 left-2.5 w-5 h-5 border-b-2 border-l-2 border-instrument-400 z-[4] pointer-events-none opacity-80" />
          <div className="absolute bottom-2.5 right-2.5 w-5 h-5 border-b-2 border-r-2 border-instrument-400 z-[4] pointer-events-none opacity-80" />

          {/* Virtual Fence Buffer Zone & Tripwire for the selected camera */}
          {cam.online && (
            <>
              {/* Proximity Warning Buffer Zone (54% to 74% height) */}
              <div className={`fence-buffer-zone ${fenceStatus === 'near_warning' ? 'active' : ''}`}>
                <span className={`absolute left-3 top-1 font-mono text-[8px] font-bold tracking-wider px-1.5 py-0.5 rounded ${
                  fenceStatus === 'near_warning'
                    ? 'bg-amber-950/80 text-amber-300 border border-amber-400/50 animate-pulse'
                    : 'text-amber-300/40 font-semibold'
                }`}>
                  {fenceStatus === 'near_warning' ? '⚠️ SUSPICIOUS ACTIVITY NEAR FENCE (BUFFER ZONE)' : 'BUFFER ZONE (PROXIMITY)'}
                </span>
              </div>

              {/* Main Virtual Fence Line */}
              <div className={`fence-line ${fenceStatus === 'breach' ? 'breach' : (fenceStatus === 'near_warning' ? 'warning' : 'clear')}`}>
                <span className={`absolute right-2 bottom-1 font-mono text-[8.5px] font-bold tracking-wider px-2 py-0.5 rounded ${
                  fenceStatus === 'breach'
                    ? 'bg-melon-d text-melon-500 border border-melon-500/40 animate-pulse'
                    : (fenceStatus === 'near_warning'
                        ? 'bg-amber-950/80 text-amber-300 border border-amber-400/50'
                        : 'bg-leaf-900/80 text-leaf-500 border border-leaf-500/40')
                }`}>
                  {fenceStatus === 'breach' ? '🚨 FENCE BREACH (INSIDE)' : (fenceStatus === 'near_warning' ? '⚠️ NEAR FENCE WARNING' : '🛡️ FENCE CLEAR')}
                </span>
              </div>
            </>
          )}

          {/* OSD Text Overlays */}
          {cam.online && (
            <>
              <div className={`osd absolute top-10 left-3 font-mono font-semibold text-[11px] text-white/90 z-[5] pointer-events-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] ${cam.night ? 'text-[#b4ffd2]' : ''}`}>
                {cam.name.split('·')[1]?.trim()?.toUpperCase() || cam.name.toUpperCase()} — {cam.location.split('—')[0]?.trim() || cam.location}
              </div>
              <div className={`osd absolute bottom-8 left-3 font-mono font-semibold text-[10.5px] text-white/90 z-[5] pointer-events-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] ${cam.night ? 'text-[#b4ffd2]' : ''}`}>
                {timeStamp}
              </div>
              <div className={`osd absolute bottom-8 right-3 font-mono font-semibold text-[10.5px] text-white/90 z-[5] pointer-events-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] text-right ${cam.night ? 'text-[#b4ffd2]' : ''}`}>
                {cam.geo || 'GPS UNAVAILABLE'} {isCurrentCamWebcam ? '· LIVE DETECTOR' : (cam.night ? '· IR NIGHT' : '')}
              </div>
            </>
          )}

          {/* Real-time Bounding Boxes Layer */}
          {cam.online && displayedBoxes.map((b, i) => (
            <div
              key={i}
              className={`dbox ${b.watch ? 'threat' : ''}`}
              style={{
                left: `${b.left}%`,
                top: `${b.top}%`,
                width: `${b.w}%`,
                height: `${b.h}%`,
                zIndex: 3
              }}
            >
              <div className="dbox-tag">{b.label}</div>
            </div>
          ))}

          {/* AI LIVE pill badge */}
          <div className={`absolute top-3 left-3 z-[6] flex items-center gap-1.5 bg-black/75 backdrop-blur-sm px-2.5 py-1 rounded-rad3 text-[9.5px] font-bold border ${
            !cam.online
              ? 'text-melon-500 border-melon-500/30'
              : isCurrentCamWebcam
              ? 'text-leaf-400 border-leaf-500/30'
              : backendConnected
              ? 'text-instrument-400 border-instrument-400/25'
              : 'text-warning-400 border-warning-400/25'
          }`}>
            <div className={`w-1.5 h-1.5 rounded-full ${
              !cam.online ? 'bg-melon-500' : isCurrentCamWebcam ? 'bg-leaf-400 animate-pulse-glow' : backendConnected ? 'bg-instrument-400' : 'bg-warning-400'
            }`} />
            {!cam.online
              ? 'STREAM OFFLINE'
              : isCurrentCamWebcam
              ? 'WEBCAM DETECTOR LIVE'
              : backendConnected
              ? 'BACKEND RTSP FEED'
              : 'BENCHMARK SIMULATION'}
          </div>

          {/* Fullscreen Trigger */}
          <button
            onClick={() => openFullscreen(cam.id)}
            className="absolute top-3 right-3 z-[6] w-7 h-7 rounded-rad3 bg-black/70 backdrop-blur-sm border border-rind-500/20 text-rind-300 hover:text-instrument-400 hover:bg-instrument-d flex items-center justify-center text-xs transition-all"
            title="Expand Camera"
            aria-label="Expand Camera to Fullscreen"
          >
            <i className="ti ti-maximize"></i>
          </button>
        </div>

        {/* Viewport Footer Telemetry */}
        <div className="flex px-3.5 py-2 shrink-0 border-t border-rind-500/15 bg-ink-850">
          <div className="flex-1 flex items-center gap-1.5 text-[10.5px] text-rind-500 border-r border-rind-500/15 px-2.5 first:pl-0" title={personCount === null ? 'Real-time count awaiting worker stream' : undefined}>
            <i className="ti ti-users text-xs text-instrument-400"></i>
            <span className="font-mono text-xs font-semibold text-rind-100">
              {personCount !== null ? personCount : '--'}
            </span>
            <span className="hidden sm:inline">persons</span>
          </div>

          <div className="flex-1 flex items-center gap-1.5 text-[10.5px] text-rind-500 border-r border-rind-500/15 px-2.5" title={vehicleCount === null ? 'Real-time count awaiting worker stream' : undefined}>
            <i className="ti ti-car text-xs text-instrument-400"></i>
            <span className="font-mono text-xs font-semibold text-rind-100">
              {vehicleCount !== null ? vehicleCount : '--'}
            </span>
            <span className="hidden sm:inline">vehicles</span>
          </div>

          <div
            className="flex-1 flex items-center gap-1.5 text-[10.5px] text-rind-500 border-r border-rind-500/15 px-2.5"
            title={
              !cam.online
                ? 'Camera is offline'
                : isCurrentCamWebcam
                ? 'Webcam frame rate'
                : metrics?.cameraTelemetry?.[cam.id]
                ? telemetryFreshness === 'stale'
                  ? 'Worker telemetry (stale)'
                  : telemetryFreshness === 'unavailable'
                  ? 'Telemetry unavailable'
                  : 'Measured worker telemetry'
                : 'Camera metadata'
            }
          >
            <i className="ti ti-gauge text-xs text-instrument-400"></i>
            <span className="font-mono text-xs font-semibold text-rind-100">
              {currentFps}
            </span>
            <span>fps</span>
          </div>

          <div className="flex-1 flex items-center gap-1.5 text-[10.5px] text-rind-500 px-2.5 last:border-r-0">
            <i className="ti ti-map-pin text-xs text-instrument-400"></i>
            <span className="text-[10.5px] text-rind-300 truncate">{cam.location}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

