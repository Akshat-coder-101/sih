import React, { useRef, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';
import { api } from '../../services/api';

export const CameraGrid: React.FC = () => {
  const { cams, alerts, webcamStream, webcamFps, isCamWebcamActive, openFullscreen, metrics } = useApp();
  const gridVideoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (gridVideoRef.current && webcamStream) {
      gridVideoRef.current.srcObject = webcamStream;
    }
  }, [webcamStream]);

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <h1 className="text-lg md:text-xl font-bold font-display tracking-tight text-rind-100">Camera Grid Surveillance</h1>
          <p className="text-xs text-rind-500 mt-0.5">Multi-sector tactical feed overview and live frame inspection</p>
        </div>
      </div>

      {cams.length === 0 ? (
        <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-12 text-center">
          <i className="ti ti-video-off text-4xl text-rind-500 opacity-50" />
          <div className="text-xs font-bold text-rind-100 mt-2">No cameras available</div>
          <div className="text-[11px] text-rind-500 mt-0.5">Please check camera configurations or backend connectivity.</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
          {cams.map(c => {
            const camAlerts = alerts.filter(a => a.camId === c.id);
            const isThisCamWebcam = isCamWebcamActive(c.id);
            const cardFps = isThisCamWebcam
              ? (webcamFps || 0)
              : !c.online
              ? 0
              : (metrics?.cameraTelemetry?.[c.id]?.fps ?? c.fps);

            return (
              <div
                key={c.id}
                className={`bg-ink-900 border rounded-rad overflow-hidden transition-all duration-150 hover:-translate-y-0.5 shadow-sm ${
                  c.online ? 'border-rind-500/20 hover:border-instrument-400/40' : 'border-melon-500/20'
                }`}
              >
                {/* Header */}
                <div className="flex items-center gap-2.5 px-3.5 py-2.5 border-b border-rind-500/15 bg-ink-850">
                  <div className={`w-2 h-2 rounded-full shrink-0 ${c.online ? 'bg-leaf-500 shadow-[0_0_8px_#65d68b]' : 'bg-melon-500'}`} />
                  <div className="flex-1 min-w-0">
                    <div className="font-bold text-xs text-rind-100 truncate">{c.name}</div>
                    <div className="text-[10px] text-rind-500 truncate">{c.location}</div>
                  </div>
                  <span className={`text-[9.5px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                    c.online ? (isThisCamWebcam ? 'bg-leaf-900 text-leaf-500 border-leaf-500/30' : 'bg-instrument-d text-instrument-400 border-instrument-400/30') : 'bg-melon-d text-melon-500 border-melon-500/30'
                  }`}>
                    {c.online ? (isThisCamWebcam ? 'AI Live' : 'Online') : 'Offline'}
                  </span>
                </div>

                {/* Feed Display */}
                <div
                  onClick={() => openFullscreen(c.id)}
                  className="w-full aspect-video bg-ink-950 relative overflow-hidden cursor-pointer group"
                  title={`Click to open full inspect view for ${c.name}`}
                >
                  {c.online ? (
                    <>
                      {isThisCamWebcam ? (
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
                      <div className="absolute bottom-2 left-2.5 font-mono text-[9px] text-white/90 drop-shadow">
                        {new Date().toLocaleTimeString('en-IN', { hour12: false })} · {c.geo || 'GPS UNAVAILABLE'}
                      </div>
                      <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-black/80 text-instrument-400 p-1.5 rounded-rad3 border border-instrument-400/30 text-xs">
                        <i className="ti ti-maximize"></i>
                      </div>
                    </>
                  ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center gap-1.5 bg-[repeating-linear-gradient(135deg,#101313,#101313_10px,#171b1a_10px,#171b1a_20px)]">
                      <i className="ti ti-video-off text-3xl text-rind-500"></i>
                      <div className="text-xs text-melon-500 font-bold">Camera Offline</div>
                    </div>
                  )}
                </div>

                {/* Footer Stats */}
                <div className="flex px-3.5 py-2 border-t border-rind-500/15 bg-ink-850">
                  <div className="flex-1 flex items-center gap-1.5 text-[10px] text-rind-500 border-r border-rind-500/15 px-2 first:pl-0" title={!c.online ? 'Stream offline' : metrics?.cameraTelemetry?.[c.id] ? 'Worker measured telemetry' : 'Camera nominal profile'}>
                    <i className="ti ti-gauge text-instrument-400 text-xs"></i>
                    <span className={`font-mono text-[11px] font-semibold ${c.online ? 'text-rind-100' : 'text-rind-500'}`}>
                      {cardFps}
                    </span>
                    <span>fps</span>
                  </div>

                  <div className="flex-1 flex items-center gap-1.5 text-[10px] text-rind-500 border-r border-rind-500/15 px-2">
                    <i className="ti ti-alert-triangle text-melon-500 text-xs"></i>
                    <span className="font-mono text-[11px] font-semibold text-rind-100">{camAlerts.length}</span>
                    <span>alerts</span>
                  </div>

                  <div className="flex-1 flex items-center gap-1.5 text-[10px] text-rind-500 px-2 last:border-r-0">
                    <i className="ti ti-flag text-instrument-400 text-xs"></i>
                    <span className="font-mono text-[11px] font-semibold text-rind-100">{c.priority}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

