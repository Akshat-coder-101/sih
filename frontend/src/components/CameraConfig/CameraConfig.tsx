import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ConfirmModal } from '../Modals/ConfirmModal';
import { isWebcamCapable } from '../../utils/camera';

export const CameraConfig: React.FC = () => {
  const { cams, toggleCamOnline, currentUser, showNotice, isCamWebcamActive } = useApp();
  const [confirmTarget, setConfirmTarget] = useState<string | null>(null);

  const isAdmin = currentUser?.role === 'admin';

  const handleToggleClick = (camId: string, isOnline: boolean) => {
    if (!isAdmin) {
      showNotice('error', 'Administrator permission required to modify camera configuration.');
      return;
    }
    // If disabling a currently active camera, confirm first
    if (isOnline) {
      setConfirmTarget(camId);
    } else {
      toggleCamOnline(camId);
    }
  };

  const handleConfirmDisable = () => {
    if (confirmTarget) {
      toggleCamOnline(confirmTarget);
      setConfirmTarget(null);
    }
  };

  const targetCam = cams.find(c => c.id === confirmTarget);

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg md:text-xl font-bold font-display tracking-tight text-rind-100">Camera Configuration &amp; Topology</h1>
          <p className="text-xs text-rind-500 mt-0.5">Registered edge nodes, network RTSP endpoints, and sensor operational states</p>
        </div>
      </div>

      {cams.length === 0 ? (
        <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-12 text-center">
          <i className="ti ti-video-off text-4xl text-rind-500 opacity-50" />
          <div className="text-xs font-bold text-rind-100 mt-2">No cameras configured</div>
          <div className="text-[11px] text-rind-500 mt-0.5">Please add or discover edge camera endpoints.</div>
        </div>
      ) : (
        <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5 divide-y divide-rind-500/10 shadow-sm">
          {cams.map(c => (
            <div key={c.id} className="flex items-center gap-3.5 py-4 first:pt-0 last:pb-0 flex-wrap sm:flex-nowrap">
              <div className={`w-9 h-9 rounded-rad3 flex items-center justify-center text-base shrink-0 ${
                c.online ? 'bg-leaf-900 text-leaf-500 border border-leaf-500/30' : 'bg-melon-d text-melon-500 border border-melon-500/30'
              }`}>
                <i className={`ti ${c.online ? 'ti-video' : 'ti-video-off'}`}></i>
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                  <strong className="text-xs md:text-sm text-rind-100 font-bold">{c.name}</strong>
                  {isWebcamCapable(c) && (
                    <span className="text-[9px] font-mono text-instrument-400 bg-instrument-d border border-instrument-400/30 px-1.5 py-0.5 rounded">
                      Webcam Node
                    </span>
                  )}
                  {isCamWebcamActive(c.id) && (
                    <span className="text-[9px] font-mono text-leaf-400 bg-leaf-900 border border-leaf-500/30 px-1.5 py-0.5 rounded">
                      Webcam Active
                    </span>
                  )}
                  <span className="text-[8.5px] font-mono text-rind-400 bg-ink-800 border border-rind-500/20 px-1.5 py-0.5 rounded">
                    {c.activeModelVersion ? `v${c.activeModelVersion}` : 'Model: n/a'}
                  </span>
                </div>
                <div className="text-[11px] text-rind-500 font-mono truncate">
                  {c.rtspUrl ? c.rtspUrl.replace(/:554.*/, ':554/****') : 'rtsp://internal.stream'} &nbsp;·&nbsp; {c.location}
                </div>
              </div>

            <span className={`text-[9.5px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
              c.priority === 'High' ? 'bg-melon-d text-melon-500 border-melon-500/25' : 'bg-warning-d text-warning-400 border-warning-400/25'
            }`}>
              {c.priority} priority
            </span>

            <span className={`text-[9.5px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
              c.online ? 'bg-leaf-900 text-leaf-500 border-leaf-500/25' : 'bg-ink-800 text-rind-500 border-rind-500/15'
            }`}>
              {c.online ? 'Connected' : 'Disconnected'}
            </span>

            {/* Toggle Switch */}
            <button
              type="button"
              role="switch"
              aria-checked={c.online}
              aria-label={`Toggle power state for ${c.name}`}
              onClick={() => handleToggleClick(c.id, c.online)}
              className={`w-10 h-5 rounded-full border cursor-pointer relative transition-colors duration-200 shrink-0 outline-none focus-visible:ring-2 focus-visible:ring-instrument-400 ${
                c.online ? 'bg-leaf-500 border-leaf-500' : 'bg-ink-800 border-rind-500/25'
              }`}
            >
              <div className={`w-3.5 h-3.5 rounded-full bg-ink-950 absolute top-[2px] left-[2px] transition-transform duration-200 ${
                c.online ? 'translate-x-5 bg-ink-950' : 'translate-x-0 bg-rind-500'
              }`} />
            </button>
          </div>
        ))}
        </div>
      )}

      {/* Confirmation Modal for Disabling Camera */}
      <ConfirmModal
        isOpen={Boolean(confirmTarget)}
        title="Disable Sector Camera Feed?"
        message={`Are you sure you want to disconnect ${targetCam?.name || 'this camera'}? Live AI perimeter surveillance and automated tripwire triggers will be suspended for this sector.`}
        confirmLabel="Disconnect Camera"
        cancelLabel="Keep Online"
        isDestructive={true}
        onConfirm={handleConfirmDisable}
        onCancel={() => setConfirmTarget(null)}
      />
    </div>
  );
};

