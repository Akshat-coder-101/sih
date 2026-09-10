import React, { useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';

export const FullscreenModal: React.FC = () => {
  const { fullscreenCamId, closeFullscreen, cams, webcamActive, webcamStream } = useApp();
  const fsVideoRef = useRef<HTMLVideoElement>(null);

  const cam = cams.find(c => c.id === fullscreenCamId);

  useEffect(() => {
    if (fsVideoRef.current && webcamStream && cam?.id === 'cam-1') {
      fsVideoRef.current.srcObject = webcamStream;
    }
  }, [webcamStream, fullscreenCamId, cam]);

  if (!fullscreenCamId || !cam) return null;

  const isCam1Webcam = cam.id === 'cam-1' && webcamActive;

  return (
    <div className="fixed inset-0 z-[300] bg-black flex flex-col animate-fade-in">
      {/* Top Header */}
      <div className="absolute top-0 left-0 right-0 z-[301] flex items-center gap-[12px] p-[14px] px-[20px] bg-gradient-to-b from-black/85 to-transparent">
        <div className="flex-1 font-[700] text-[14.5px] text-tx">
          {cam.name} &mdash; {cam.location}
        </div>
        <div className="flex items-center gap-[6px] px-[10px] py-[3px] rounded-[15px] bg-cyan-d border border-cyan/30 text-cyan text-[10px] font-bold">
          <div className="w-[6px] h-[6px] rounded-full bg-cyan animate-pulse-glow" />
          FULL VIEW
        </div>
        <button
          onClick={closeFullscreen}
          className="w-[34px] h-[34px] rounded-rad2 border border-b2 bg-black/50 text-tx2 hover:bg-red-d hover:text-red flex items-center justify-center text-[16px] transition-colors"
        >
          <i className="ti ti-x"></i>
        </button>
      </div>

      {/* Main Stream Area */}
      <div className="flex-1 relative bg-[#04070b] overflow-hidden">
        {cam.online ? (
          <>
            {isCam1Webcam ? (
              <video
                ref={fsVideoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
            ) : (
              <div
                className="w-full h-full"
                dangerouslySetInnerHTML={{ __html: getSceneSvg(cam.scene) }}
              />
            )}
            <div className="cv-vignette absolute inset-0" />
            <div className="scanlines absolute inset-0" />

            {/* OSD */}
            <div className="absolute top-[70px] left-[20px] font-mono font-[700] text-[13px] text-white/90 drop-shadow">
              {cam.name.split('·')[1].trim().toUpperCase()}
            </div>
            <div className="absolute bottom-[20px] left-[20px] font-mono text-[12px] text-white/90 drop-shadow">
              {new Date().toLocaleString('en-GB')}
            </div>
            <div className="absolute bottom-[20px] right-[20px] font-mono text-[12px] text-white/90 drop-shadow text-right">
              {cam.geo} {isCam1Webcam ? '· TF.js COCO-SSD' : (cam.night ? '· IR MODE' : '')}
            </div>
          </>
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center gap-[10px] bg-s1">
            <i className="ti ti-video-off text-[48px] text-tx4"></i>
            <div className="text-[14px] text-red font-[700]">Camera Stream Offline</div>
          </div>
        )}
      </div>
    </div>
  );
};
