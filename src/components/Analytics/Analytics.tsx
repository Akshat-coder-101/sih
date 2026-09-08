import React, { useRef, useEffect } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';

export const Analytics: React.FC = () => {
  const { alerts, cams, openLightbox } = useApp();
  const donutCanvasRef = useRef<HTMLCanvasElement>(null);

  const criticalCount = alerts.filter(a => a.sev === 'high').length;
  const watchlistCount = alerts.filter(a => a.type === 'watchlist').length;
  const onlineCamsCount = cams.filter(c => c.online).length;

  const kpis = [
    { cls: 'border-t-cyan', valCls: 'text-cyan', label: 'Cameras Online', val: `${onlineCamsCount}/${cams.length}`, sub: '1 offline — coverage gap flagged', icon: 'ti-video' },
    { cls: 'border-t-red', valCls: 'text-red', label: 'Alerts Today', val: `${alerts.length}`, sub: `${criticalCount} critical events`, icon: 'ti-alert-triangle' },
    { cls: 'border-t-blue', valCls: 'text-blue', label: 'Watchlist Hits', val: `${watchlistCount}`, sub: 'Authorized watchlist matching', icon: 'ti-fingerprint' },
    { cls: 'border-t-amber', valCls: 'text-amber', label: 'Avg AI Latency', val: '~14ms', sub: 'Client-side inference', icon: 'ti-bolt' },
  ];

  const types = Object.keys(TYPE_META);
  const typeColors: Record<string, string> = {
    intrusion: '#ff4757',
    weapon: '#e03445',
    watchlist: '#ff4757',
    anpr: '#4dabf7',
    loiter: '#ffa726',
    night: '#b197fc'
  };

  const typeCounts = types.map(t => ({
    type: t,
    label: TYPE_META[t].label,
    color: typeColors[t] || '#00e5b8',
    count: alerts.filter(a => a.type === t).length
  }));

  // Draw interactive donut canvas
  useEffect(() => {
    const canvas = donutCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const total = alerts.length || 1;
    ctx.clearRect(0, 0, 130, 130);
    let ang = -Math.PI / 2;

    typeCounts.forEach(it => {
      if (it.count === 0) return;
      const slice = (it.count / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(65, 65);
      ctx.arc(65, 65, 56, ang, ang + slice);
      ctx.closePath();
      ctx.fillStyle = it.color;
      ctx.fill();
      ang += slice;
    });

    // Inner cutout
    ctx.beginPath();
    ctx.arc(65, 65, 32, 0, Math.PI * 2);
    ctx.fillStyle = '#0f1822';
    ctx.fill();

    // Center total label
    ctx.fillStyle = '#e8eef8';
    ctx.font = 'bold 15px "JetBrains Mono", monospace';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(String(alerts.length), 65, 65);
  }, [alerts]);

  const barData = cams.map(c => ({
    label: c.name.split('·')[0].trim(),
    count: alerts.filter(a => a.camId === c.id).length
  }));
  const maxBar = Math.max(...barData.map(b => b.count), 1);

  const recentAlerts = alerts.slice().sort((a, b) => b.ts.getTime() - a.ts.getTime()).slice(0, 6);

  return (
    <div className="flex-1 overflow-y-auto p-[24px]">
      <div className="flex items-center justify-between mb-[22px]">
        <div>
          <div className="text-[18px] font-[800] tracking-[-0.4px] text-tx">Analytics & Intelligence</div>
          <div className="text-[11.5px] text-tx3 mt-[1px]">Real-time pattern analysis across all border sectors</div>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-4 gap-[14px] mb-[20px]">
        {kpis.map((k, i) => (
          <div
            key={i}
            className={`bg-s2 border border-b1 rounded-rad p-[18px] px-[20px] relative overflow-hidden transition-transform duration-150 hover:-translate-y-[2px] border-t-2 ${k.cls}`}
          >
            <div className="text-[9.5px] tracking-[1.4px] uppercase text-tx3 font-[700] mb-[10px]">{k.label}</div>
            <div className={`text-[30px] font-[900] leading-none tracking-[-1px] font-mono ${k.valCls}`}>{k.val}</div>
            <div className="text-[11px] text-tx3 mt-[6px]">{k.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-2 gap-[14px] mb-[20px]">
        {/* Donut Chart: Alerts by Type */}
        <div className="bg-s2 border border-b1 rounded-rad p-[20px]">
          <div className="flex items-center gap-[10px] pb-[14px] mb-[16px] border-b border-b1">
            <div className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center bg-cyan-d text-cyan text-[14px]">
              <i className="ti ti-chart-donut"></i>
            </div>
            <h3 className="text-[13px] font-[700] text-tx flex-1">Alerts by Threat Type</h3>
          </div>

          <div className="flex items-center gap-[20px]">
            <canvas ref={donutCanvasRef} width={130} height={130} className="shrink-0" />
            <div className="flex-1 flex flex-col gap-[8px]">
              {typeCounts.map(it => (
                <div key={it.type} className="flex items-center gap-[9px]">
                  <div className="w-[10px] h-[10px] rounded-[3px] shrink-0" style={{ backgroundColor: it.color }} />
                  <div className="flex-1 text-[11.5px] text-tx2">{it.label}</div>
                  <div className="font-mono text-[12px] font-[600] text-tx">{it.count}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bar Chart: Alerts by Camera */}
        <div className="bg-s2 border border-b1 rounded-rad p-[20px]">
          <div className="flex items-center gap-[10px] pb-[14px] mb-[16px] border-b border-b1">
            <div className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center bg-blue-d text-blue text-[14px]">
              <i className="ti ti-chart-bar"></i>
            </div>
            <h3 className="text-[13px] font-[700] text-tx flex-1">Incidents per Camera Stream</h3>
          </div>

          <div className="flex items-end gap-[12px] h-[130px] pt-[16px]">
            {barData.map(b => (
              <div key={b.label} className="flex flex-col items-center gap-[4px] flex-1">
                <div className="text-[10px] text-tx2 font-mono font-[600]">{b.count}</div>
                <div
                  className="w-full rounded-t-[4px] bg-cyan transition-all duration-300 min-h-[4px]"
                  style={{ height: `${Math.max(6, (b.count / maxBar) * 92)}px` }}
                />
                <div className="text-[9px] text-tx3 text-center">{b.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity List */}
      <div className="bg-s2 border border-b1 rounded-rad p-[20px]">
        <div className="flex items-center gap-[10px] pb-[14px] mb-[16px] border-b border-b1">
          <div className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center bg-amber-d text-amber text-[14px]">
            <i className="ti ti-clock-alert"></i>
          </div>
          <h3 className="text-[13px] font-[700] text-tx flex-1">Recent Intelligence Triggers</h3>
        </div>

        <div className="space-y-[10px]">
          {recentAlerts.map(a => {
            const meta = TYPE_META[a.type] || TYPE_META.intrusion;
            return (
              <div
                key={a.id}
                onClick={() => openLightbox(a.id)}
                className="flex items-center gap-[12px] p-[10px] px-[14px] bg-s1 border border-b0 rounded-rad2 hover:bg-s3 cursor-pointer transition-colors"
              >
                <div className={`w-[32px] h-[32px] rounded-[8px] flex items-center justify-center text-[15px] border ${meta.cls}`}>
                  <i className={`ti ${meta.icon}`}></i>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-bold text-tx truncate">{a.detail}</div>
                  <div className="text-[10.5px] text-tx3">{a.camName} · {a.location}</div>
                </div>
                {a.snapshot && (
                  <span className="text-[9.5px] font-mono font-bold text-cyan bg-cyan-dd border border-cyan/25 px-[7px] py-[2px] rounded">
                    Evidence Captured
                  </span>
                )}
                <div className="text-[10px] text-tx4 font-mono">
                  {a.ts.toLocaleTimeString('en-IN', { hour12: false })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
