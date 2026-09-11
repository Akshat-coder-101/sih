import React, { useState } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';

export const AlertsPanel: React.FC = () => {
  const { alerts, openLightbox, updateAlertState } = useApp();
  const [filter, setFilter] = useState<string>('all');

  const filteredAlerts = alerts
    .filter(a => filter === 'all' || a.type === filter)
    .sort((a, b) => b.ts.getTime() - a.ts.getTime())
    .slice(0, 30);

  const pendingCount = alerts.filter(a => !a.reviewed && (a.state || 'open') === 'open').length;
  const criticalCount = alerts.filter(a => a.sev === 'high').length;
  const warningCount = alerts.filter(a => a.sev === 'med').length;

  const timeAgo = (date: Date) => {
    const s = Math.floor((Date.now() - date.getTime()) / 1000);
    if (s < 60) return `${s}s ago`;
    const m = Math.floor(s / 60);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    return `${h}h ago`;
  };

  const filterButtons = [
    { id: 'all', label: 'All' },
    { id: 'intrusion', label: 'Intrusion' },
    { id: 'weapon', label: 'Threat' },
    { id: 'watchlist', label: 'Watchlist' },
    { id: 'anpr', label: 'ANPR' },
    { id: 'loiter', label: 'Loiter' },
    { id: 'night', label: 'Night' },
  ];

  return (
    <div className="w-full md:w-[320px] md:min-w-[320px] h-[40vh] md:h-auto bg-ink-900 border-t md:border-t-0 md:border-l border-rind-500/15 flex flex-col overflow-hidden select-none">
      {/* Header */}
      <div className="p-3 px-3.5 pb-2.5 border-b border-rind-500/15 shrink-0 bg-ink-850">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-bold font-display text-rind-100 flex-1">Live Alert Stream</span>
          <span className="text-[9.5px] font-bold bg-melon-d text-melon-500 border border-melon-500/25 px-2 py-0.5 rounded-full">
            {pendingCount} open
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex gap-1 flex-wrap">
          {filterButtons.map(fb => (
            <button
              key={fb.id}
              onClick={() => setFilter(fb.id)}
              className={`text-[9.5px] px-2 py-0.5 rounded-full border transition-all cursor-pointer ${
                filter === fb.id
                  ? 'bg-instrument-d text-instrument-400 border-instrument-400/30 font-semibold'
                  : 'border-rind-500/20 bg-transparent text-rind-500 hover:text-rind-200 hover:border-rind-500/40'
              }`}
            >
              {fb.label}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="flex-1 overflow-y-auto divide-y divide-rind-500/10">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map(a => {
            const meta = TYPE_META[a.type] || TYPE_META.intrusion;
            const isNew = Date.now() - a.ts.getTime() < 60000;
            const currentState = a.state || (a.reviewed ? 'resolved' : 'open');
            const isDetector = (a.provenance || 'detector') === 'detector';
            return (
              <div
                key={a.id}
                onClick={() => openLightbox(a.id)}
                className={`flex gap-2.5 p-2.5 px-3 cursor-pointer transition-colors duration-100 hover:bg-ink-800 ${
                  isNew ? 'border-l-2 border-l-melon-500 bg-melon-dd' : ''
                }`}
              >
                {/* Icon or Real Thumbnail */}
                {a.snapshot ? (
                  <div className="w-9 h-9 rounded-rad3 shrink-0 overflow-hidden border border-melon-500/40 relative">
                    <img src={a.snapshot} alt="Captured" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-melon-d flex items-center justify-center">
                      <i className="ti ti-camera text-xs text-rind-100 drop-shadow"></i>
                    </div>
                  </div>
                ) : (
                  <div className={`w-9 h-9 rounded-rad3 shrink-0 flex items-center justify-center text-sm border ${
                    a.sev === 'high' ? 'bg-melon-d text-melon-500 border-melon-500/30' : 'bg-instrument-d text-instrument-400 border-instrument-400/30'
                  }`}>
                    <i className={`ti ${meta.icon}`}></i>
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
                    <span className={`text-[8.5px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded border ${
                      a.sev === 'high' ? 'bg-melon-d text-melon-500 border-melon-500/30' : 'bg-instrument-d text-instrument-400 border-instrument-400/30'
                    }`}>
                      {a.type}
                    </span>
                    <span className={`text-[8px] font-bold px-1 py-0.5 rounded uppercase ${
                      isDetector ? 'bg-leaf-900 text-leaf-500 border border-leaf-500/30' : 'bg-ink-800 text-rind-500 border border-rind-500/20'
                    }`}>
                      {isDetector ? 'AI' : 'SIM'}
                    </span>
                    <span className={`text-[8.5px] font-bold px-1.5 py-0.5 rounded ml-auto ${
                      a.sev === 'high' ? 'bg-melon-d text-melon-500' : a.sev === 'med' ? 'bg-warning-d text-warning-400' : 'bg-instrument-d text-instrument-400'
                    }`}>
                      {a.sev === 'high' ? 'CRITICAL' : a.sev === 'med' ? 'WARN' : 'INFO'}
                    </span>
                  </div>

                  <div className="text-[10.5px] text-rind-200 truncate mb-0.5 font-medium" title={a.detail}>
                    {a.detail}
                  </div>

                  <div className="text-[10px] text-rind-500 truncate mb-0.5 flex items-center gap-1.5 flex-wrap">
                    <span>{a.camName.split('·')[0].trim()}</span>
                    {a.snapshot && (
                      <span className="text-[8.5px] text-instrument-400 font-mono font-bold flex items-center gap-0.5">
                        <i className="ti ti-photo text-[9px]"></i> snap
                      </span>
                    )}
                    {currentState === 'open' ? (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          updateAlertState(a.id, 'acknowledged');
                        }}
                        className="ml-auto text-[8.5px] font-bold text-warning-400 bg-warning-d hover:bg-warning-500/20 px-1.5 py-0.5 rounded border border-warning-400/30 transition-colors"
                      >
                        Ack
                      </button>
                    ) : (
                      <span className="text-leaf-500 text-[8.5px] font-semibold ml-auto">✓ {currentState}</span>
                    )}
                  </div>

                  <div className="text-[9px] text-rind-600 font-mono">
                    {timeAgo(a.ts)}
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-8 text-center text-rind-500 flex flex-col items-center justify-center gap-2">
            <i className="ti ti-inbox text-2xl opacity-40"></i>
            <span className="text-xs">No alerts matching filter</span>
          </div>
        )}
      </div>

      {/* Footer Summary */}
      <div className="p-2.5 px-3 border-t border-rind-500/15 shrink-0 grid grid-cols-3 gap-1.5 bg-ink-950/60">
        <div className="bg-ink-800 p-1.5 rounded-rad3 text-center border border-rind-500/10">
          <div className="text-[8.5px] text-rind-500 font-mono">CRITICAL</div>
          <div className="text-xs font-bold text-melon-500">{criticalCount}</div>
        </div>
        <div className="bg-ink-800 p-1.5 rounded-rad3 text-center border border-rind-500/10">
          <div className="text-[8.5px] text-rind-500 font-mono">WARNING</div>
          <div className="text-xs font-bold text-warning-400">{warningCount}</div>
        </div>
        <div className="bg-ink-800 p-1.5 rounded-rad3 text-center border border-rind-500/10">
          <div className="text-[8.5px] text-rind-500 font-mono">TOTAL</div>
          <div className="text-xs font-bold text-rind-100">{alerts.length}</div>
        </div>
      </div>
    </div>
  );
};

