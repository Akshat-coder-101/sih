import React, { useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';
import { api } from '../../services/api';

export const CameraGrid: React.FC = () => {
  const { cams, alerts, webcamActive, webcamStream, cam1Fps, openFullscreen } = useApp();
  const gridVideoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (gridVideoRef.current && webcamStream) {
      gridVideoRef.current.srcObject = webcamStream;
    }
  }, [webcamStream]);

  return (
    <div className="flex-1 overflow-y-auto p-[24px]">
      <div className="flex items-center justify-between mb-[22px] flex-wrap gap-[10px]">
        <div>
          <div className="text-[18px] font-[800] tracking-[-0.4px] text-tx">Camera Grid</div>
          <div className="text-[11.5px] text-tx3 mt-[1px]">All configured tactical cameras at a glance</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-[16px] mb-[20px]">
        {cams.map(c => {
          const camAlerts = alerts.filter(a => a.camId === c.id);
          const isCam1Webcam = c.id === 'cam-1' && webcamActive;

          return (
            <div
              key={c.id}
              className={`bg-s2 border rounded-rad overflow-hidden transition-all duration-150 hover:-translate-y-[2px] ${
                c.online ? 'border-cyan/20' : 'border-red/15'
              }`}
            >
              {/* Header */}
              <div className="flex items-center gap-[9px] px-[14px] py-[10px] border-b border-b1 bg-s1">
                <div className={`w-[8px] h-[8px] rounded-full shrink-0 ${c.online ? 'bg-cyan shadow-[0_0_8px_#00e5b8]' : 'bg-red'}`} />
                <div className="flex-1 min-w-0">
                  <div className="font-[700] text-[12.5px] text-tx truncate">{c.name}</div>
                  <div className="text-[10px] text-tx3 truncate">{c.location}</div>
                </div>
                <span className={`text-[9.5px] font-[700] uppercase tracking-[0.4px] px-[8px] py-[2px] rounded-[5px] border ${
                  c.online ? 'bg-cyan-d text-cyan border-cyan/25' : 'bg-red-d text-red border-red/25'
                }`}>
                  {c.online ? (isCam1Webcam ? 'AI Live' : 'Online') : 'Offline'}
                </span>
              </div>

              {/* Feed Display */}
              <div
                onClick={() => openFullscreen(c.id)}
                className="w-full aspect-video bg-[#04070b] relative overflow-hidden cursor-pointer group"
              >
                {c.online ? (
                  <>
                    {isCam1Webcam ? (
                      <video
                        ref={gridVideoRef}
                        autoPlay
                        playsInline
                        muted
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <>
                        <img
                          src={api.getStreamUrl(c.id)}
                          alt={c.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.currentTarget as HTMLElement).style.display = 'none';
                            const fb = document.getElementById(`grid-svg-${c.id}`);
                            if (fb) fb.style.display = 'block';
                          }}
                        />
                        <div
                          id={`grid-svg-${c.id}`}
                          className="w-full h-full hidden"
                          dangerouslySetInnerHTML={{ __html: getSceneSvg(c.scene) }}
                        />
                      </>
                    )}
                    <div className="cv-vignette absolute inset-0 pointer-events-none" />
                    <div className="scanlines absolute inset-0 pointer-events-none" />
                    <div className="absolute bottom-[8px] left-[10px] font-mono text-[9px] text-white/90 drop-shadow">
                      {new Date().toLocaleTimeString('en-IN', { hour12: false })} · {c.geo}
                    </div>
                    <div className="absolute top-[8px] right-[8px] opacity-0 group-hover:opacity-100 transition-opacity bg-black/70 text-cyan p-[5px] rounded-rad3 border border-cyan/30 text-[12px]">
                      <i className="ti ti-maximize"></i>
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full flex flex-col items-center justify-center gap-[6px] bg-[repeating-linear-gradient(135deg,#080d14,#080d14_10px,#09111a_10px,#09111a_20px)]">
                    <i className="ti ti-video-off text-[32px] text-tx4"></i>
                    <div className="text-[11px] text-red font-[700]">Camera Offline</div>
                  </div>
                )}
              </div>

              {/* Footer Stats */}
              <div className="flex px-[14px] py-[8px] border-t border-b1 bg-s1">
                <div className="flex-1 flex items-center gap-[6px] text-[10px] text-tx3 border-r border-b1 px-[8px] first:pl-0">
                  <i className="ti ti-gauge text-cyan text-[12px]"></i>
                  <span className="font-mono text-[11px] font-[600] text-tx">
                    {c.id === 'cam-1' && webcamActive ? (cam1Fps || 8) : c.fps}
                  </span>
                  <span>fps</span>
                </div>

                <div className="flex-1 flex items-center gap-[6px] text-[10px] text-tx3 border-r border-b1 px-[8px]">
                  <i className="ti ti-alert-triangle text-red text-[12px]"></i>
                  <span className="font-mono text-[11px] font-[600] text-tx">{camAlerts.length}</span>
                  <span>alerts</span>
                </div>

                <div className="flex-1 flex items-center gap-[6px] text-[10px] text-tx3 px-[8px] last:border-r-0">
                  <i className="ti ti-flag text-cyan text-[12px]"></i>
                  <span className="font-mono text-[11px] font-[600] text-tx">{c.priority}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
