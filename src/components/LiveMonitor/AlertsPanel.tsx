import React, { useState } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';

export const AlertsPanel: React.FC = () => {
  const { alerts, openLightbox } = useApp();
  const [filter, setFilter] = useState<string>('all');

  const filteredAlerts = alerts
    .filter(a => filter === 'all' || a.type === filter)
    .sort((a, b) => b.ts.getTime() - a.ts.getTime())
    .slice(0, 30);

  const pendingCount = alerts.filter(a => !a.reviewed).length;
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
    <div className="w-[330px] min-w-[330px] bg-s1 border-l border-b1 flex flex-col overflow-hidden select-none">
      {/* Header */}
      <div className="p-[13px] px-[14px] pb-[10px] border-b border-b1 shrink-0">
        <div className="flex items-center gap-[8px] mb-[8px]">
          <span className="text-[12.5px] font-[700] text-tx flex-1">Live Alerts</span>
          <span className="text-[9.5px] font-[700] bg-red-d text-red border border-red/20 px-[9px] py-[2px] rounded-[20px]">
            {pendingCount} pending
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex gap-[4px] flex-wrap">
          {filterButtons.map(fb => (
            <button
              key={fb.id}
              onClick={() => setFilter(fb.id)}
              className={`text-[9.5px] px-[9px] py-[3px] rounded-[20px] border transition-all duration-150 cursor-pointer ${
                filter === fb.id
                  ? 'bg-cyan-d text-cyan border-cyan/30 font-semibold'
                  : 'border-b1 bg-transparent text-tx3 hover:text-tx2 hover:border-b2'
              }`}
            >
              {fb.label}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts List */}
      <div className="flex-1 overflow-y-auto">
        {filteredAlerts.length > 0 ? (
          filteredAlerts.map(a => {
            const meta = TYPE_META[a.type] || TYPE_META.intrusion;
            const isNew = Date.now() - a.ts.getTime() < 60000;
            return (
              <div
                key={a.id}
                onClick={() => openLightbox(a.id)}
                className={`flex gap-[10px] p-[10px] px-[12px] border-b border-b0 cursor-pointer transition-colors duration-100 hover:bg-s2 ${
                  isNew ? 'border-l-2 border-l-red' : ''
                }`}
              >
                {/* Icon or Real Thumbnail */}
                {a.snapshot ? (
                  <div className="w-[38px] h-[38px] rounded-[9px] shrink-0 overflow-hidden border border-red/40 relative">
                    <img src={a.snapshot} alt="Captured" className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-red-d/30 flex items-center justify-center">
                      <i className="ti ti-camera text-[12px] text-white drop-shadow"></i>
                    </div>
                  </div>
                ) : (
                  <div className={`w-[38px] h-[38px] rounded-[9px] shrink-0 flex items-center justify-center text-[16px] border ${meta.cls}`}>
                    <i className={`ti ${meta.icon}`}></i>
                  </div>
                )}

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-[5px] mb-[3px]">
                    <span className={`text-[8.5px] font-[700] tracking-[0.5px] uppercase px-[7px] py-[2px] rounded-[4px] border ${meta.cls}`}>
                      {a.type}
                    </span>
                    <span className={`text-[9px] font-[700] px-[7px] py-[2px] rounded-[4px] ml-auto ${
                      a.sev === 'high' ? 'bg-red-d text-red' : a.sev === 'med' ? 'bg-amber-d text-amber' : 'bg-blue-d text-blue'
                    }`}>
                      {a.sev === 'high' ? 'CRITICAL' : a.sev === 'med' ? 'WARNING' : 'INFO'}
                    </span>
                  </div>

                  <div className="text-[10.5px] text-tx2 truncate mb-[2px] font-medium" title={a.detail}>
                    {a.detail}
                  </div>

                  <div className="text-[10px] text-tx3 truncate mb-[2px] flex items-center gap-[4px]">
                    <span>{a.camName.split('·')[0].trim()}</span>
                    {a.snapshot && (
                      <span className="text-[9px] text-cyan font-mono font-bold flex items-center gap-[2px]">
                        <i className="ti ti-photo text-[10px]"></i> frame captured
                      </span>
                    )}
                    {a.reviewed && <span className="text-cyan text-[9px] ml-auto">✓ reviewed</span>}
                  </div>

                  <div className="text-[9px] text-tx4 font-mono">
                    {timeAgo(a.ts)}
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="p-[40px] text-center text-tx3 flex flex-col items-center justify-center gap-[8px]">
            <i className="ti ti-mood-empty text-[28px] opacity-40"></i>
            <span>No alerts for this filter</span>
          </div>
        )}
      </div>

      {/* Footer Summary */}
      <div className="p-[10px] px-[12px] border-t border-b1 shrink-0 grid grid-template grid-cols-3 gap-[6px]">
        <div className="text-center p-[7px] px-[4px] rounded-rad3 bg-s2 border border-b0">
          <div className="text-[20px] font-[800] leading-none font-mono text-red">{criticalCount}</div>
          <div className="text-[8px] text-tx3 tracking-[1px] uppercase mt-[2px]">Critical</div>
        </div>

        <div className="text-center p-[7px] px-[4px] rounded-rad3 bg-s2 border border-b0">
          <div className="text-[20px] font-[800] leading-none font-mono text-amber">{warningCount}</div>
          <div className="text-[8px] text-tx3 tracking-[1px] uppercase mt-[2px]">Warning</div>
        </div>

        <div className="text-center p-[7px] px-[4px] rounded-rad3 bg-s2 border border-b0">
          <div className="text-[20px] font-[800] leading-none font-mono text-cyan">{alerts.length}</div>
          <div className="text-[8px] text-tx3 tracking-[1px] uppercase mt-[2px]">Today</div>
        </div>
      </div>
    </div>
  );
};
