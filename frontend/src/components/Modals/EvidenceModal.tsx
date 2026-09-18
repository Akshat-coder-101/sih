import React, { useEffect, useState } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';
import { api } from '../../services/api';

export const EvidenceModal: React.FC = () => {
  const { activeLightboxAlert, closeLightbox, markReviewed, cams, currentUser } = useApp();
  const [terrain, setTerrain] = useState<any>(null);
  const [recommendation, setRecommendation] = useState<any>(null);

  useEffect(() => {
    if (!activeLightboxAlert) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeLightbox();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activeLightboxAlert, closeLightbox]);

  useEffect(() => {
    if (!activeLightboxAlert) return;
    api.getAlertTerrain(activeLightboxAlert.id, currentUser?.accessToken)
      .then(setTerrain)
      .catch(() => null);
    api.getAlertRecommendation(activeLightboxAlert.id, currentUser?.accessToken)
      .then(setRecommendation)
      .catch(() => null);
  }, [activeLightboxAlert, currentUser]);

  if (!activeLightboxAlert) return null;

  const a = activeLightboxAlert;
  const meta = TYPE_META[a.type] || TYPE_META.intrusion;
  const cam = cams.find(c => c.id === a.camId);
  const isThreat = a.type === 'watchlist' || a.type === 'weapon' || a.sev === 'high';

  const isDetector = (a.provenance || 'detector') === 'detector';

  const fields = [
    { key: 'Event Type', val: meta.label },
    { key: 'Severity', val: a.sev === 'high' ? 'CRITICAL' : a.sev === 'med' ? 'WARNING' : 'INFO' },
    { key: 'Provenance', val: isDetector ? 'Live Edge Detector' : 'Simulation' },
    { key: 'Camera Source', val: a.camName },
    { key: 'Sector Location', val: a.location },
    { key: 'AI Confidence', val: `${a.confidence}%` },
    { key: 'Track ID', val: a.trackId },
    { key: 'Event Detail', val: a.detail },
    { key: 'Timestamp', val: a.ts.toLocaleString('en-GB') },
    { key: 'Audit Status', val: a.reviewed ? 'Verified & Reviewed' : 'Action Pending' },
    { key: 'Event UID', val: a.id },
  ];

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="evidence-modal-title"
      onClick={e => {
        if (e.target === e.currentTarget) closeLightbox();
      }}
      className="fixed inset-0 z-[200] bg-black/85 backdrop-blur-md flex items-center justify-center p-4 overflow-y-auto animate-fade-in"
    >
      <div className="bg-ink-900 border border-rind-500/20 rounded-rad max-w-[560px] w-full overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
        {/* Header */}
        <div className="flex items-center gap-2.5 px-4 py-3.5 border-b border-rind-500/15 bg-ink-850">
          <span className={`text-[9px] font-bold uppercase px-2 py-0.5 rounded border ${
            a.sev === 'high' ? 'bg-melon-d text-melon-500 border-melon-500/30' : 'bg-instrument-d text-instrument-400 border-instrument-400/30'
          }`}>
            {a.type}
          </span>
          <div id="evidence-modal-title" className="text-sm font-bold font-display text-rind-100 flex-1 truncate">
            {meta.label} — {a.id}
          </div>
          <button
            onClick={closeLightbox}
            aria-label="Close evidence modal"
            className="w-7 h-7 rounded-rad3 border border-rind-500/15 hover:bg-melon-d hover:text-melon-500 flex items-center justify-center text-sm text-rind-500 transition-colors"
          >
            <i className="ti ti-x"></i>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-4 md:p-5">
          {/* Evidence Frame / Simulated Box */}
          <div className="w-full aspect-[16/10] rounded-rad3 overflow-hidden border border-rind-500/20 mb-4 bg-ink-950 relative">
            {a.snapshot ? (
              <img
                src={a.snapshot}
                alt="Forensic Frame Snapshot"
                className="w-full h-full object-cover block"
              />
            ) : (
              <>
                <div
                  className="absolute inset-0"
                  dangerouslySetInnerHTML={{ __html: getSceneSvg(cam?.scene || 'fence') }}
                />
                <div className="cv-vignette absolute inset-0" />
                <div className="scanlines absolute inset-0" />

                {/* Simulated Bounding Box */}
                <div
                  className={`dbox ${isThreat ? 'threat' : ''}`}
                  style={{
                    left: `${(cam?.anchor.left || 44) - 6}%`,
                    top: `${(cam?.anchor.top || 46) - 4}%`,
                    width: `${(cam?.anchor.w || 10) + 12}%`,
                    height: `${(cam?.anchor.h || 24) + 8}%`,
                    zIndex: 2
                  }}
                >
                  <div className="dbox-tag">{!isDetector ? '[SIM] ' : ''}{a.type.toUpperCase()} {a.confidence}%</div>
                </div>
              </>
            )}

            {/* Evidence Badges */}
            <div className="absolute top-2 right-2 z-[3] flex items-center gap-1.5 bg-black/80 px-2 py-1 rounded-rad3 text-[9.5px] font-bold text-rind-200 border border-rind-500/20">
              <i className="ti ti-camera text-instrument-400"></i>
              {a.snapshot ? 'Live Frame Burn-In' : isDetector ? 'Detector Evidence' : 'Simulation Evidence'}
            </div>

            <div className="absolute bottom-2 left-2 z-[3] font-mono text-[9px] text-rind-300 bg-black/80 px-2 py-1 rounded-rad3 border border-rind-500/20 max-w-[80%] truncate">
              {a.camName.split('·')[0]?.trim() || a.camName} · {cam?.geo || 'GPS UNAVAILABLE'}
            </div>
          </div>

          {/* Key-Value Fields Grid */}
          <div className="grid grid-cols-2 border border-rind-500/15 rounded-rad3 overflow-hidden mb-3.5">
            {fields.map((f, i) => (
              <div
                key={i}
                className={`p-2.5 px-3 border-b border-rind-500/10 bg-ink-850/60 ${
                  i % 2 === 0 ? 'border-r border-rind-500/10' : ''
                } ${i >= fields.length - 2 ? 'border-b-0' : ''}`}
              >
                <div className="text-[9px] text-rind-500 uppercase tracking-wider font-bold mb-0.5">{f.key}</div>
                <div className="text-xs text-rind-100 font-mono font-medium truncate">{f.val}</div>
              </div>
            ))}
          </div>

          {/* GIS Topographic Profile (FR-6) */}
          {terrain && (
            <div className="border border-rind-500/15 rounded-rad3 p-3 bg-ink-850/60 mb-3 text-xs space-y-1.5">
              <div className="flex items-center justify-between border-b border-rind-500/10 pb-1">
                <span className="font-bold text-rind-100 flex items-center gap-1.5 text-[11px]">
                  <i className="ti ti-mountain text-instrument-400"></i>
                  GIS Topographic Profile
                </span>
                <span className="text-[9.5px] font-mono text-rind-500">{terrain.datasetSource}</span>
              </div>
              <div className="grid grid-cols-4 gap-2 text-[10.5px]">
                <div className="bg-ink-900/60 p-1.5 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[9px] uppercase">Elev</div>
                  <div className="font-mono font-bold text-rind-100">{terrain.elevationM}m</div>
                </div>
                <div className="bg-ink-900/60 p-1.5 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[9px] uppercase">Slope</div>
                  <div className="font-mono font-bold text-rind-100">{terrain.slopeDeg}°</div>
                </div>
                <div className="bg-ink-900/60 p-1.5 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[9px] uppercase">Cover</div>
                  <div className="font-semibold text-leaf-400 capitalize truncate">{terrain.landCover.replace('_', ' ')}</div>
                </div>
                <div className="bg-ink-900/60 p-1.5 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[9px] uppercase">Route</div>
                  <div className="font-mono font-bold text-instrument-400">{terrain.nearestRoadDistanceM}m</div>
                </div>
              </div>
            </div>
          )}

          {/* Tactical Recommendation (FR-7) */}
          {recommendation && (
            <div className="border border-rind-500/15 rounded-rad3 p-3 bg-ink-850/60 text-xs space-y-1.5">
              <div className="flex items-center justify-between border-b border-rind-500/10 pb-1">
                <span className="font-bold text-rind-100 flex items-center gap-1.5 text-[11px]">
                  <i className="ti ti-compass text-melon-400"></i>
                  Tactical Guidance
                </span>
                <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                  recommendation.status === 'approved' ? 'bg-leaf-900 text-leaf-400 border border-leaf-500/30' : 'bg-warning-d text-warning border border-warning/30'
                }`}>
                  {recommendation.status}
                </span>
              </div>
              <p className="text-rind-200 text-[11px] leading-relaxed">
                {recommendation.actionSummary}
              </p>
              <div className="space-y-0.5">
                {recommendation.tacticalActions.slice(0, 2).map((act: string, idx: number) => (
                  <div key={idx} className="flex items-start gap-1 text-[10.5px] text-rind-300">
                    <i className="ti ti-chevron-right text-melon-400 text-[9px] mt-0.5 shrink-0"></i>
                    <span>{act}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 border-t border-rind-500/15 bg-ink-850">
          {!a.reviewed && (
            <div className="flex items-center gap-2">
              <select
                id="disposition-reason-select"
                defaultValue="verified_threat"
                className="bg-ink-900 border border-rind-500/30 text-rind-200 text-xs px-2.5 py-1.5 rounded-rad3 font-mono"
              >
                <option value="verified_threat">Verified Threat / Actioned</option>
                <option value="authorized_patrol">Authorized Friendly Patrol</option>
                <option value="false_alarm_animal">False Alarm — Animal Activity</option>
                <option value="false_alarm_weather">False Alarm — Environmental / Glare</option>
              </select>
              <button
                onClick={() => {
                  const sel = document.getElementById('disposition-reason-select') as HTMLSelectElement;
                  markReviewed(a.id, sel?.value || 'verified_threat');
                }}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-rad3 bg-leaf-500 hover:bg-leaf-600 text-ink-950 font-bold text-xs transition-colors shadow-sm"
              >
                <i className="ti ti-check text-sm"></i>
                Acknowledge Triage
              </button>
            </div>
          )}
          <button
            onClick={closeLightbox}
            className="px-4 py-2 rounded-rad3 border border-rind-500/20 text-rind-300 hover:bg-ink-800 hover:text-rind-100 text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

