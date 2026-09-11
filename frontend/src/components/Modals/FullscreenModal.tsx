import React, { useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';
import { api } from '../../services/api';

export const FullscreenModal: React.FC = () => {
  const { fullscreenCamId, closeFullscreen, cams, webcamStream, isCamWebcamActive } = useApp();
  const fsVideoRef = useRef<HTMLVideoElement>(null);

  const cam = cams.find(c => c.id === fullscreenCamId);

  useEffect(() => {
    if (!fullscreenCamId) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeFullscreen();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [fullscreenCamId, closeFullscreen]);

  useEffect(() => {
    if (fsVideoRef.current && webcamStream && isCamWebcamActive(cam?.id)) {
      fsVideoRef.current.srcObject = webcamStream;
    }
  }, [webcamStream, fullscreenCamId, cam, isCamWebcamActive]);

  if (!fullscreenCamId || !cam) return null;

  const isCurrentCamWebcam = isCamWebcamActive(cam.id);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Fullscreen View: ${cam.name}`}
      className="fixed inset-0 z-[300] bg-black flex flex-col animate-fade-in"
    >
      {/* Top Header */}
      <div className="absolute top-0 left-0 right-0 z-[301] flex items-center gap-3 p-3.5 px-5 bg-gradient-to-b from-black/90 to-transparent">
        <div className="flex-1 font-bold font-display text-sm md:text-base text-rind-100 truncate">
          {cam.name} &mdash; {cam.location}
        </div>
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-instrument-d border border-instrument-400/30 text-instrument-400 text-[10px] font-bold">
          <div className="w-1.5 h-1.5 rounded-full bg-instrument-400 animate-pulse-glow" />
          FULL VIEW
        </div>
        <button
          onClick={closeFullscreen}
          aria-label="Exit fullscreen view"
          className="w-8 h-8 rounded-rad3 border border-rind-500/20 bg-black/50 text-rind-300 hover:bg-melon-d hover:text-melon-500 flex items-center justify-center text-base transition-colors"
        >
          <i className="ti ti-x"></i>
        </button>
      </div>

      {/* Main Stream Area */}
      <div className="flex-1 relative bg-ink-950 overflow-hidden">
        {cam.online ? (
          <>
            {isCurrentCamWebcam ? (
              <video
                ref={fsVideoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
            ) : (
              <>
                <img
                  src={api.getStreamUrl(cam.id)}
                  alt={cam.name}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.currentTarget as HTMLElement).style.display = 'none';
                    const fb = document.getElementById(`fs-svg-${cam.id}`);
                    if (fb) fb.style.display = 'block';
                  }}
                />
                <div
                  id={`fs-svg-${cam.id}`}
                  className="w-full h-full hidden"
                  dangerouslySetInnerHTML={{ __html: getSceneSvg(cam.scene) }}
                />
              </>
            )}
            <div className="cv-vignette absolute inset-0 pointer-events-none" />
            <div className="scanlines absolute inset-0 pointer-events-none" />

            {/* OSD */}
            <div className="absolute top-16 left-5 font-mono font-bold text-sm text-white/90 drop-shadow">
              {cam.name.split('·')[1]?.trim()?.toUpperCase() || cam.name.toUpperCase()}
            </div>
            <div className="absolute bottom-5 left-5 font-mono text-xs text-white/90 drop-shadow">
              {new Date().toLocaleString('en-GB')}
            </div>
            <div className="absolute bottom-5 right-5 font-mono text-xs text-white/90 drop-shadow text-right">
              {cam.geo || 'GPS UNAVAILABLE'} {isCurrentCamWebcam ? '· TF.js DETECTOR' : (cam.night ? '· IR NIGHT MODE' : '')}
            </div>
          </>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-2 bg-ink-900">
            <i className="ti ti-video-off text-5xl text-rind-500"></i>
            <div className="text-sm text-melon-500 font-bold">Camera Stream Offline</div>
          </div>
        )}
      </div>
    </div>
  );
};

