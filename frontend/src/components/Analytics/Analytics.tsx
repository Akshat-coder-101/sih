import React, { useRef, useEffect } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';
import { getProvenanceLabel } from '../../utils/camera';

export const Analytics: React.FC = () => {
  const { alerts, cams, openLightbox, metrics, telemetryFreshness } = useApp();
  const donutCanvasRef = useRef<HTMLCanvasElement>(null);

  const criticalCount = alerts.filter(a => a.sev === 'high').length;
  const watchlistAlerts = alerts.filter(a => a.type === 'watchlist');
  const watchlistCount = watchlistAlerts.length;
  const onlineCamsCount = cams.filter(c => c.online).length;

  const activeLatencies = metrics
    ? Object.values(metrics.cameraTelemetry)
        .map(t => t.inferenceLatencyMs)
        .filter((lat): lat is number => typeof lat === 'number' && lat > 0)
    : [];

  const avgLatencyVal = activeLatencies.length > 0
    ? `${Math.round(activeLatencies.reduce((a, b) => a + b, 0) / activeLatencies.length)}ms`
    : 'n/a';
  const avgLatencySub = telemetryFreshness === 'stale'
    ? `Telemetry stale (${activeLatencies.length} worker(s) cached)`
    : activeLatencies.length > 0
    ? `Measured across ${activeLatencies.length} active camera worker(s)`
    : metrics
    ? 'Workers idle / awaiting frame triggers'
    : 'Telemetry unavailable';

  const avgLatencyProv = telemetryFreshness === 'stale'
    ? 'Telemetry stale'
    : telemetryFreshness === 'unavailable'
    ? 'Telemetry unavailable'
    : activeLatencies.length > 0
    ? 'Live backend telemetry'
    : metrics
    ? 'Worker idle'
    : 'Awaiting telemetry';

  const threatProv = getProvenanceLabel(alerts, 'No alerts');
  const watchlistProv = getProvenanceLabel(watchlistAlerts, 'No hits');

  const kpis = [
    { cls: 'border-t-leaf-500', valCls: 'text-leaf-500', label: 'Cameras Online', val: `${onlineCamsCount}/${cams.length}`, sub: cams.length - onlineCamsCount > 0 ? `${cams.length - onlineCamsCount} offline` : 'All sector cameras operational', icon: 'ti-video', prov: 'Live Hardware' },
    { cls: 'border-t-melon-500', valCls: 'text-melon-500', label: 'Threats Logged', val: `${alerts.length}`, sub: `${criticalCount} high-priority breaches`, icon: 'ti-alert-triangle', prov: threatProv },
    { cls: 'border-t-instrument-400', valCls: 'text-instrument-400', label: 'Watchlist Hits', val: `${watchlistCount}`, sub: 'Biometric profile match', icon: 'ti-fingerprint', prov: watchlistProv },
    { cls: 'border-t-warning-400', valCls: 'text-warning-400', label: 'Avg AI Latency', val: avgLatencyVal, sub: avgLatencySub, icon: 'ti-bolt', prov: avgLatencyProv },
  ];

  const types = Object.keys(TYPE_META);
  const typeColors: Record<string, string> = {
    intrusion: '#ff6b5f',
    weapon: '#e84d52',
    watchlist: '#ff6b5f',
    anpr: '#56c7d9',
    loiter: '#f4bd5b',
    night: '#b197fc'
  };

  const typeCounts = types.map(t => ({
    type: t,
    label: TYPE_META[t].label,
    color: typeColors[t] || '#56c7d9',
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
    ctx.fillStyle = '#171b1a';
    ctx.fill();

    // Center total label
    ctx.fillStyle = '#f2f5ee';
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
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg md:text-xl font-bold font-display tracking-tight text-rind-100">Analytics & Intelligence</h1>
          <p className="text-xs text-rind-500 mt-0.5">Real-time pattern analysis and telemetry across border sectors</p>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3.5 mb-5">
        {kpis.map((k, i) => (
          <div
            key={i}
            className={`bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:px-5 relative overflow-hidden transition-transform duration-150 hover:-translate-y-0.5 border-t-2 shadow-sm ${k.cls}`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[9.5px] tracking-wider uppercase text-rind-500 font-bold">{k.label}</span>
              <span className="text-[8.5px] font-mono font-semibold px-1.5 py-0.5 rounded bg-ink-800 text-rind-500 border border-rind-500/15">
                {k.prov}
              </span>
            </div>
            <div className={`text-2xl md:text-3xl font-black leading-none tracking-tight font-mono ${k.valCls}`}>{k.val}</div>
            <div className="text-[11px] text-rind-500 mt-1.5">{k.sub}</div>
          </div>
        ))}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-3.5 mb-5">
        {/* Donut Chart: Alerts by Type */}
        <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5">
          <div className="flex items-center gap-2.5 pb-3.5 mb-4 border-b border-rind-500/15">
            <div className="w-7 h-7 rounded-rad3 flex items-center justify-center bg-instrument-d text-instrument-400 text-sm">
              <i className="ti ti-chart-donut"></i>
            </div>
            <h3 className="text-xs font-bold font-display text-rind-100 flex-1">Alerts by Threat Type</h3>
            <span className="text-[9px] font-mono text-rind-500">{threatProv}</span>
          </div>

          <div className="flex items-center gap-5">
            <canvas ref={donutCanvasRef} width={130} height={130} className="shrink-0" />
            <div className="flex-1 flex flex-col gap-2">
              {typeCounts.map(it => (
                <div key={it.type} className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: it.color }} />
                  <div className="flex-1 text-xs text-rind-300">{it.label}</div>
                  <div className="font-mono text-xs font-semibold text-rind-100">{it.count}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Bar Chart: Alerts by Camera */}
        <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5">
          <div className="flex items-center gap-2.5 pb-3.5 mb-4 border-b border-rind-500/15">
            <div className="w-7 h-7 rounded-rad3 flex items-center justify-center bg-instrument-d text-instrument-400 text-sm">
              <i className="ti ti-chart-bar"></i>
            </div>
            <h3 className="text-xs font-bold font-display text-rind-100 flex-1">Incidents per Camera Stream</h3>
            <span className="text-[9px] font-mono text-rind-500">Sector Aggregation</span>
          </div>

          <div className="flex items-end gap-3 h-[130px] pt-4">
            {barData.map(b => (
              <div key={b.label} className="flex flex-col items-center gap-1 flex-1">
                <div className="text-[10px] text-rind-300 font-mono font-semibold">{b.count}</div>
                <div
                  className="w-full rounded-t bg-instrument-400/80 transition-all duration-300 min-h-[4px]"
                  style={{ height: `${Math.max(6, (b.count / maxBar) * 92)}px` }}
                />
                <div className="text-[9px] text-rind-500 text-center truncate w-full">{b.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity List */}
      <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5">
        <div className="flex items-center gap-2.5 pb-3.5 mb-4 border-b border-rind-500/15">
          <div className="w-7 h-7 rounded-rad3 flex items-center justify-center bg-warning-d text-warning-400 text-sm">
            <i className="ti ti-clock-alert"></i>
          </div>
          <h3 className="text-xs font-bold font-display text-rind-100 flex-1">Recent Intelligence Triggers</h3>
          <span className="text-[9px] font-mono text-rind-500">Triage Queue</span>
        </div>

        <div className="space-y-2">
          {recentAlerts.map(a => {
            const meta = TYPE_META[a.type] || TYPE_META.intrusion;
            return (
              <div
                key={a.id}
                onClick={() => openLightbox(a.id)}
                className="flex items-center gap-3 p-2.5 px-3.5 bg-ink-850 border border-rind-500/10 rounded-rad3 hover:bg-ink-800 cursor-pointer transition-colors"
              >
                <div className={`w-8 h-8 rounded-rad3 flex items-center justify-center text-sm border ${
                  a.sev === 'high' ? 'bg-melon-d text-melon-500 border-melon-500/30' : 'bg-instrument-d text-instrument-400 border-instrument-400/30'
                }`}>
                  <i className={`ti ${meta.icon}`}></i>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-bold text-rind-100 truncate">{a.detail}</div>
                  <div className="text-[10.5px] text-rind-500">{a.camName} · {a.location}</div>
                </div>
                {a.snapshot && (
                  <span className="text-[9px] font-mono font-bold text-instrument-400 bg-instrument-d border border-instrument-400/25 px-1.5 py-0.5 rounded hidden sm:inline">
                    Evidence Captured
                  </span>
                )}
                <div className="text-[10px] text-rind-500 font-mono">
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

