import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';
import { api } from '../../services/api';

export const CamViewport: React.FC = () => {
  const {
    cams,
    activeCamId,
    selectCam,
    webcamActive,
    webcamError,
    videoRef,
    liveDetections,
    cam1Fps,
    isFenceBreached,
    openFullscreen,
    triggerWeaponDemo,
    toggleCamNight,
    startWebcam
  } = useApp();

  const [simBoxes, setSimBoxes] = useState<any[]>([]);
  const [timeStamp, setTimeStamp] = useState<string>('');

  const cam = cams.find(c => c.id === activeCamId) || cams[0];

  useEffect(() => {
    const updateTime = () => {
      const d = new Date();
      setTimeStamp(d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) + ' ' + d.toLocaleTimeString('en-IN', { hour12: false }));
    };
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  // Jitter for simulated cams
  useEffect(() => {
    if (!cam.online || (cam.id === 'cam-1' && webcamActive)) {
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
        label: isWatch ? 'WATCHLIST 0.9' + Math.floor(Math.random() * 9) : (cam.scene === 'gate' ? 'VEHICLE 0.' + (80 + Math.floor(Math.random() * 18)) : 'PERSON 0.' + (80 + Math.floor(Math.random() * 18))),
        watch: isWatch
      }]);
    };

    updateSim();
    const interval = setInterval(updateSim, 3000);
    return () => clearInterval(interval);
  }, [activeCamId, cam.online, webcamActive]);

  const displayedBoxes = (cam.id === 'cam-1' && webcamActive) ? liveDetections : simBoxes;
  const isWebcamCam1 = cam.id === 'cam-1' && webcamActive;

  return (
    <div className="flex-1 flex flex-col overflow-hidden p-[12px] gap-[8px] min-w-0">
      {/* Cam Bar */}
      <div className="flex items-center gap-[8px] shrink-0">
        <span className="text-[11px] font-[600] text-tx2">Cameras</span>

        <div className="mr-auto flex items-center gap-[6px]">
          <span className="bg-cyan-dd border border-cyan/20 px-[8px] py-[2px] rounded-[12px] text-[9.5px] text-cyan font-mono font-[600] flex items-center gap-[4px]">
            <i className="ti ti-cpu text-[11px]"></i>
            CAM-01: {webcamActive ? 'Webcam AI Active' : 'AI Ready'}
          </span>
        </div>

        {/* Camera Selector Tabs */}
        <div className="flex items-center gap-[6px]">
          {cams.map(c => (
            <div
              key={c.id}
              onClick={() => selectCam(c.id)}
              className={`flex items-center rounded-[20px] border transition-all duration-150 cursor-pointer overflow-hidden ${
                c.id === activeCamId
                  ? 'border-cyan/40 bg-cyan-dd text-cyan'
                  : c.online
                  ? 'border-b1 bg-s2 text-tx3 hover:text-tx hover:border-b2'
                  : 'border-b1 bg-s2 text-tx4 opacity-60'
              }`}
            >
              <span className={`w-[6px] h-[6px] rounded-full ml-[10px] shrink-0 ${c.online ? 'bg-cyan shadow-[0_0_6px_#00e5b8]' : 'bg-red'}`} />
              <span className="text-[10.5px] font-[600] px-[10px] pr-[12px] py-[5px] whitespace-nowrap">
                {c.name.split('·')[0].trim()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Main Viewport Box */}
      <div className="flex-1 min-h-0 bg-s1 border border-b2 rounded-rad overflow-hidden flex flex-col shadow-[0_8px_40px_rgba(0,0,0,0.4)]">
        {/* Header */}
        <div className="flex items-center gap-[10px] px-[14px] py-[10px] shrink-0 bg-gradient-to-r from-cyan/5 to-transparent border-b border-b1">
          <div className={`w-[8px] h-[8px] rounded-full shrink-0 ${cam.online ? 'bg-cyan shadow-[0_0_8px_#00e5b8] animate-pulse-glow' : 'bg-red'}`} />
          <div className="text-[13px] font-[700] text-tx flex-1">
            {cam.name}
          </div>
          <div className="text-[11px] text-tx3">
            {cam.location}
          </div>

          {/* Night Mode Toggle Button */}
          {cam.online && (
            <button
              onClick={() => toggleCamNight(cam.id)}
              className={`text-[9.5px] font-[700] uppercase tracking-[0.4px] px-[8px] py-[2px] rounded-[5px] border flex items-center gap-[4px] transition-colors ${
                cam.night ? 'bg-violet-d text-violet border-violet/30' : 'bg-s2 text-tx3 border-b1 hover:text-tx'
              }`}
              title="Toggle IR Low-Light Night Vision Enhancement"
            >
              <i className={`ti ${cam.night ? 'ti-moon-stars' : 'ti-sun'} text-[11px]`}></i>
              {cam.night ? 'IR Night Active' : 'Optical Day'}
            </button>
          )}

          <span className={`text-[9.5px] font-[700] uppercase tracking-[0.4px] px-[8px] py-[2px] rounded-[5px] border ${
            cam.online ? 'bg-cyan-d text-cyan border-cyan/25' : 'bg-red-d text-red border-red/25'
          }`}>
            {cam.online ? (isWebcamCam1 ? 'AI Live' : 'Online · Live Stream') : 'Offline'}
          </span>
        </div>

        {/* Viewport Area */}
        <div className={`flex-1 relative bg-[#04070b] min-h-0 overflow-hidden ${cam.night ? 'radial-night' : ''}`}>
          {/* Real Webcam Video Stream for CAM-01 */}
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className={`absolute inset-0 w-full h-full object-cover z-0 ${isWebcamCam1 ? 'block' : 'hidden'}`}
          />

          {/* Live MJPEG Stream for CAM-02, 03, 04 from FastAPI Backend */}
          {!isWebcamCam1 && cam.online && (
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
          {!isWebcamCam1 && cam.online && (
            <div
              id={`svg-fb-${cam.id}`}
              className="absolute inset-0 z-0 hidden"
              dangerouslySetInnerHTML={{ __html: getSceneSvg(cam.scene) }}
            />
          )}

          {/* Webcam Activation Overlay for CAM-01 */}
          {cam.id === 'cam-1' && !webcamActive && cam.online && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/80 backdrop-blur-[3px] gap-[12px] p-[20px] text-center">
              <div className="w-[52px] h-[52px] rounded-full bg-cyan-d border border-cyan/30 text-cyan flex items-center justify-center text-[24px] shadow-[0_0_20px_rgba(0,229,184,0.25)]">
                <i className="ti ti-camera"></i>
              </div>
              <div>
                <div className="text-[14.5px] font-bold text-tx">Enable Webcam for Live AI Detection</div>
                <div className="text-[11px] text-tx3 max-w-[320px] mt-[4px]">
                  Click below to activate your laptop/USB camera to test real-time knife, blade, and threat detection.
                </div>
              </div>
              <button
                onClick={startWebcam}
                className="px-[16px] py-[8px] rounded-rad2 bg-gradient-to-r from-cyan to-cyan-2 text-black font-bold text-[12px] hover:opacity-95 transition-all flex items-center gap-[6px] shadow-[0_0_15px_rgba(0,229,184,0.35)] cursor-pointer active:scale-95"
              >
                <i className="ti ti-video text-[15px]"></i>
                Start Webcam
              </button>
            </div>
          )}

          {/* Offline Screen */}
          {!cam.online && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-[8px] bg-[repeating-linear-gradient(135deg,#080d14,#080d14_10px,#09111a_10px,#09111a_20px)]">
              <i className="ti ti-video-off text-[38px] text-tx4"></i>
              <div className="text-[12.5px] text-red font-[700]">Camera Offline</div>
              <div className="text-[10.5px] text-tx4">Stream disconnected</div>
            </div>
          )}

          {/* Vignette & Scanlines */}
          <div className="cv-vignette absolute inset-0 z-[1]" />
          <div className="scanlines absolute inset-0 z-[2]" />

          {/* Tactical Corner Reticles */}
          <div className="absolute top-[10px] left-[10px] w-[20px] h-[20px] border-t-2 border-l-2 border-cyan z-[4] pointer-events-none" />
          <div className="absolute top-[10px] right-[10px] w-[20px] h-[20px] border-t-2 border-r-2 border-cyan z-[4] pointer-events-none" />
          <div className="absolute bottom-[10px] left-[10px] w-[20px] h-[20px] border-b-2 border-l-2 border-cyan z-[4] pointer-events-none" />
          <div className="absolute bottom-[10px] right-[10px] w-[20px] h-[20px] border-b-2 border-r-2 border-cyan z-[4] pointer-events-none" />

          {/* Virtual Fence Line (CAM-01 / Perimeter) */}
          {cam.online && (
            <div className={`fence-line ${isFenceBreached ? 'breach' : 'clear'}`}>
              <span className={`absolute right-[8px] bottom-[4px] font-mono text-[8px] font-[700] tracking-[1px] px-[6px] py-[1px] rounded-[3px] ${
                isFenceBreached ? 'bg-red/20 text-red' : 'bg-green/15 text-green'
              }`}>
                {isFenceBreached ? 'FENCE BREACH' : 'FENCE CLEAR'}
              </span>
            </div>
          )}

          {/* OSD Text Overlays */}
          {cam.online && (
            <>
              <div className={`osd absolute top-[40px] left-[12px] font-mono font-[600] text-[11px] text-white/90 z-[5] pointer-events-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] ${cam.night ? 'text-[#b4ffd2]' : ''}`}>
                {cam.name.split('·')[1].trim().toUpperCase()} — {cam.location.split('—')[0].trim()}
              </div>
              <div className={`osd absolute bottom-[34px] left-[12px] font-mono font-[600] text-[10.5px] text-white/90 z-[5] pointer-events-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] ${cam.night ? 'text-[#b4ffd2]' : ''}`}>
                {timeStamp}
              </div>
              <div className={`osd absolute bottom-[34px] right-[12px] font-mono font-[600] text-[10.5px] text-white/90 z-[5] pointer-events-none drop-shadow-[0_1px_2px_rgba(0,0,0,0.9)] text-right ${cam.night ? 'text-[#b4ffd2]' : ''}`}>
                {cam.geo} {isWebcamCam1 ? '· AI ACTIVE' : (cam.night ? '· IR NIGHT' : '')}
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
          <div className="absolute top-[12px] left-[12px] z-[6] flex items-center gap-[5px] bg-black/70 backdrop-blur-[4px] px-[10px] py-[4px] rounded-[6px] text-[10px] font-[700] text-cyan border border-cyan/25">
            <div className="w-[6px] h-[6px] rounded-full bg-cyan animate-pulse-glow" />
            AI LIVE
          </div>

          {/* Fullscreen Trigger */}
          <button
            onClick={() => openFullscreen(cam.id)}
            className="absolute top-[12px] right-[12px] z-[6] w-[28px] h-[28px] rounded-rad3 bg-black/65 backdrop-blur-[4px] border border-b2 text-tx2 hover:text-cyan hover:bg-cyan-d flex items-center justify-center text-[14px] transition-all"
            title="Expand Camera"
          >
            <i className="ti ti-maximize"></i>
          </button>
        </div>

        {/* Viewport Footer Telemetry */}
        <div className="flex px-[14px] py-[8px] shrink-0 border-t border-b1 bg-s2">
          <div className="flex-1 flex items-center gap-[6px] text-[10.5px] text-tx3 border-r border-b1 px-[10px] first:pl-0">
            <i className="ti ti-users text-[13px] text-cyan"></i>
            <span className="font-mono text-[11.5px] font-[600] text-tx">
              {cam.id === 'cam-1' && webcamActive ? displayedBoxes.filter(b => b.class === 'person').length : (cam.online ? '1' : '0')}
            </span>
            <span>persons</span>
          </div>

          <div className="flex-1 flex items-center gap-[6px] text-[10.5px] text-tx3 border-r border-b1 px-[10px]">
            <i className="ti ti-car text-[13px] text-cyan"></i>
            <span className="font-mono text-[11.5px] font-[600] text-tx">
              {cam.id === 'cam-1' && webcamActive ? displayedBoxes.filter(b => ['car', 'truck', 'bus', 'motorcycle', 'bicycle'].includes(b.class || '')).length : (cam.scene === 'gate' ? '1' : '0')}
            </span>
            <span>vehicles</span>
          </div>

          <div className="flex-1 flex items-center gap-[6px] text-[10.5px] text-tx3 border-r border-b1 px-[10px]">
            <i className="ti ti-gauge text-[13px] text-cyan"></i>
            <span className="font-mono text-[11.5px] font-[600] text-tx">
              {cam.id === 'cam-1' && webcamActive ? (cam1Fps || 8) : cam.fps}
            </span>
            <span>fps</span>
          </div>

          <div className="flex-1 flex items-center gap-[6px] text-[10.5px] text-tx3 px-[10px] last:border-r-0">
            <i className="ti ti-map-pin text-[13px] text-cyan"></i>
            <span className="text-[10.5px] text-tx2 truncate">{cam.location}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
