import React, { useState, useEffect } from 'react';
import { Alert } from '../../types';
import { api, TerrainEnrichment, TacticalRecommendation } from '../../services/api';
import { useApp } from '../../context/AppContext';

interface PatrolModalProps {
  alert: Alert | null;
  onClose: () => void;
  onAcknowledge?: (alertId: string) => void;
}

export const PatrolModal: React.FC<PatrolModalProps> = ({ alert, onClose, onAcknowledge }) => {
  const { currentUser } = useApp();
  const [terrain, setTerrain] = useState<TerrainEnrichment | null>(null);
  const [recommendation, setRecommendation] = useState<TacticalRecommendation | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [reviewing, setReviewing] = useState<boolean>(false);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  useEffect(() => {
    if (!alert) return;
    let isMounted = true;
    setLoading(true);

    Promise.all([
      api.getAlertTerrain(alert.id, currentUser?.accessToken).catch(() => null),
      api.getAlertRecommendation(alert.id, currentUser?.accessToken).catch(() => null)
    ]).then(([t, r]) => {
      if (isMounted) {
        setTerrain(t);
        setRecommendation(r);
        setLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [alert, currentUser]);

  const handleReview = async (newStatus: 'approved' | 'rejected') => {
    if (!recommendation) return;
    try {
      setReviewing(true);
      const updated = await api.reviewRecommendation(
        recommendation.id,
        newStatus,
        `Field action confirmed by ${currentUser?.username || 'operator'}`,
        currentUser?.accessToken
      );
      setRecommendation(updated);
      setActionNotice(`Tactical recommendation ${newStatus.toUpperCase()}`);
    } catch (err: any) {
      setActionNotice(`Review failed: ${err.message}`);
    } finally {
      setReviewing(false);
    }
  };

  const handleDispatchAck = () => {
    if (alert && onAcknowledge) {
      onAcknowledge(alert.id);
      setActionNotice('Dispatch acknowledged by patrol unit');
    }
  };

  if (!alert) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-ink-950/80 backdrop-blur-md animate-fade-in">
      <div
        className="w-full max-w-lg bg-ink-900 border border-rind-500/20 rounded-rad shadow-2xl overflow-hidden flex flex-col max-h-[92vh]"
        role="dialog"
        aria-modal="true"
        aria-labelledby="patrol-modal-title"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-ink-850 border-b border-rind-500/15">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-melon-500 animate-pulse-glow" />
            <h2 id="patrol-modal-title" className="text-sm font-bold font-display text-rind-100 uppercase tracking-wide">
              Patrol Tactical Dispatch Mode
            </h2>
          </div>
          <button
            onClick={onClose}
            className="w-7 h-7 rounded-rad3 bg-ink-800 hover:bg-ink-700 text-rind-400 hover:text-rind-100 flex items-center justify-center transition-colors border border-rind-500/15"
            aria-label="Close dialog"
          >
            <i className="ti ti-x text-sm"></i>
          </button>
        </div>

        {/* Action Notice */}
        {actionNotice && (
          <div className="bg-leaf-900/60 border-b border-leaf-500/30 px-4 py-1.5 text-xs text-leaf-400 flex items-center gap-2">
            <i className="ti ti-circle-check"></i>
            <span>{actionNotice}</span>
          </div>
        )}

        {/* Content Body */}
        <div className="p-4 overflow-y-auto space-y-4 text-rind-300 text-xs">
          {/* Top Target Card */}
          <div className="bg-ink-800/80 border border-rind-500/15 rounded-rad p-3.5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] text-rind-500">{alert.id} · {alert.camId}</span>
              <span className="px-2 py-0.5 rounded-rad3 text-[10px] font-bold uppercase bg-melon-900 text-melon-400 border border-melon-500/30">
                {alert.type.toUpperCase()} ({alert.confidence}%)
              </span>
            </div>
            <div className="text-sm font-semibold text-rind-100">{alert.location}</div>
            <div className="flex items-center gap-4 text-[11px] font-mono text-rind-400">
              <span className="flex items-center gap-1">
                <i className="ti ti-clock text-instrument-400"></i>
                {new Date(alert.ts).toLocaleTimeString()}
              </span>
              <span className="flex items-center gap-1">
                <i className="ti ti-shield-check text-leaf-400"></i>
                Provenance: {alert.provenance || 'detector'}
              </span>
            </div>
          </div>

          {/* GIS Topographical Context */}
          <div className="bg-ink-800/80 border border-rind-500/15 rounded-rad p-3.5 space-y-2.5">
            <div className="flex items-center justify-between border-b border-rind-500/10 pb-1.5">
              <span className="font-bold text-xs text-rind-100 flex items-center gap-1.5">
                <i className="ti ti-mountain text-instrument-400"></i>
                GIS Topographic Profile
              </span>
              <span className="text-[10px] text-rind-500 font-mono">
                {terrain?.datasetSource || 'SRTM-v3 / CartoDEM-v1'}
              </span>
            </div>

            {loading ? (
              <div className="text-center py-3 text-rind-500 font-mono text-[11px]">Loading spatial elevation data...</div>
            ) : terrain ? (
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="bg-ink-900/60 p-2 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[10px] uppercase">Elevation</div>
                  <div className="font-mono font-bold text-rind-100 text-sm">{terrain.elevationM} m MSL</div>
                </div>
                <div className="bg-ink-900/60 p-2 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[10px] uppercase">Slope Gradient</div>
                  <div className="font-mono font-bold text-rind-100 text-sm">{terrain.slopeDeg}° ({terrain.slopeDeg > 25 ? 'Steep' : 'Moderate'})</div>
                </div>
                <div className="bg-ink-900/60 p-2 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[10px] uppercase">Sector Land Cover</div>
                  <div className="font-semibold text-leaf-400 capitalize">{terrain.landCover.replace('_', ' ')}</div>
                </div>
                <div className="bg-ink-900/60 p-2 rounded border border-rind-500/10">
                  <div className="text-rind-500 text-[10px] uppercase">Nearest Road / Route</div>
                  <div className="font-mono font-bold text-instrument-400">{terrain.nearestRoadDistanceM} m</div>
                </div>
              </div>
            ) : (
              <div className="text-rind-500 text-[11px]">Topographic elevation data unavailable for sector.</div>
            )}
          </div>

          {/* Tactical Recommendation Card */}
          <div className="bg-ink-800/80 border border-rind-500/15 rounded-rad p-3.5 space-y-2.5">
            <div className="flex items-center justify-between border-b border-rind-500/10 pb-1.5">
              <span className="font-bold text-xs text-rind-100 flex items-center gap-1.5">
                <i className="ti ti-compass text-melon-400"></i>
                Tactical Guidance (Decision Support)
              </span>
              {recommendation && (
                <span className={`px-2 py-0.5 rounded-rad3 text-[9.5px] font-bold uppercase ${
                  recommendation.status === 'approved'
                    ? 'bg-leaf-900 text-leaf-400 border border-leaf-500/30'
                    : 'bg-warning-d text-warning border border-warning/30'
                }`}>
                  {recommendation.status}
                </span>
              )}
            </div>

            {loading ? (
              <div className="text-center py-3 text-rind-500 font-mono text-[11px]">Evaluating tactical decision support...</div>
            ) : recommendation ? (
              <div className="space-y-2 text-[11px]">
                <p className="text-rind-200 font-medium leading-relaxed bg-ink-900/60 p-2.5 rounded border border-rind-500/10">
                  {recommendation.actionSummary}
                </p>
                <div className="space-y-1 pl-1">
                  <div className="text-[10.5px] font-bold uppercase text-rind-400">Recommended Steps:</div>
                  {recommendation.tacticalActions.map((step, idx) => (
                    <div key={idx} className="flex items-start gap-1.5 text-rind-300">
                      <i className="ti ti-chevron-right text-melon-400 text-[10px] mt-0.5 shrink-0"></i>
                      <span>{step}</span>
                    </div>
                  ))}
                </div>

                {/* Supervisor Approval Controls */}
                {currentUser?.role === 'supervisor' || currentUser?.role === 'admin' ? (
                  recommendation.status !== 'approved' && (
                    <div className="flex items-center gap-2 pt-2 border-t border-rind-500/10">
                      <button
                        onClick={() => handleReview('approved')}
                        disabled={reviewing}
                        className="flex-1 bg-leaf-600 hover:bg-leaf-500 text-ink-950 font-bold py-1.5 px-3 rounded text-[11px] transition-colors flex items-center justify-center gap-1"
                      >
                        <i className="ti ti-check"></i>
                        <span>Authorize Tactical Action</span>
                      </button>
                      <button
                        onClick={() => handleReview('rejected')}
                        disabled={reviewing}
                        className="bg-ink-800 hover:bg-ink-700 text-rind-300 py-1.5 px-3 rounded text-[11px] border border-rind-500/20"
                      >
                        Reject
                      </button>
                    </div>
                  )
                ) : null}
              </div>
            ) : (
              <div className="text-rind-500 text-[11px]">No tactical guidance generated for alert.</div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-3 bg-ink-850 border-t border-rind-500/15 flex items-center gap-2">
          <button
            onClick={handleDispatchAck}
            className="flex-1 bg-instrument-500 hover:bg-instrument-400 text-ink-950 font-bold py-2 px-3 rounded text-xs transition-colors flex items-center justify-center gap-1.5 shadow-sm"
          >
            <i className="ti ti-radio"></i>
            <span>Acknowledge Dispatch</span>
          </button>
          <button
            onClick={onClose}
            className="bg-ink-800 hover:bg-ink-700 text-rind-300 py-2 px-4 rounded text-xs border border-rind-500/20 font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
