import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const Topbar: React.FC = () => {
  const {
    currentPage,
    cams,
    alerts,
    armed,
    toggleArmed,
    triggerWeaponDemo,
    currentUser,
    switchRoleDemo,
    backendConnected,
    apiAvailable,
    websocketConnected,
    readiness,
    latencyPingMs,
    telemetryFreshness,
    lastMetricsAt,
    toggleMobileMenu,
    openPatrolModal
  } = useApp();
  const [timeStr, setTimeStr] = useState<string>('--:--:--');
  const [roleSwitching, setRoleSwitching] = useState<boolean>(false);

  useEffect(() => {
    const tick = () => {
      setTimeStr(new Date().toLocaleTimeString('en-IN', { hour12: false }));
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  const pageTitles: Record<string, string> = {
    monitor: 'Live Monitor',
    camgrid: 'Camera Grid',
    alerts: 'Alerts Log',
    analytics: 'Analytics',
    models: 'AI Inference Pipeline',
    'cam-config': 'Camera Configuration',
    about: 'About IBVAP',
    contact: 'Contact & Support',
    privacy: 'Privacy Policy',
    terms: 'Terms of Use',
    'not-found': 'Page Not Found'
  };

  const onlineCamsCount = cams.filter(c => c.online).length;
  const watchlistCount = alerts.filter(a => a.type === 'watchlist').length;

  let statusText = 'OFFLINE DEMO MODE';
  let statusBadgeCls = 'bg-warning-d text-warning-400 border-warning-400/30';
  let dotCls = 'bg-warning-400';

  if (apiAvailable) {
    if (readiness && !readiness.ready) {
      if (!readiness.database) {
        statusText = 'DATABASE DEGRADED';
        statusBadgeCls = 'bg-melon-d text-melon-500 border-melon-500/30';
        dotCls = 'bg-melon-500';
      } else if (!readiness.modelLoaded) {
        statusText = 'AI MODEL LOADING';
        statusBadgeCls = 'bg-warning-d text-warning-400 border-warning-400/30';
        dotCls = 'bg-warning-400 animate-pulse-glow';
      } else if (readiness.activeStreams.length === 0) {
        statusText = 'STREAMS IDLE';
        statusBadgeCls = 'bg-warning-d text-warning-400 border-warning-400/30';
        dotCls = 'bg-warning-400';
      } else {
        statusText = 'BACKEND DEGRADED';
        statusBadgeCls = 'bg-melon-d text-melon-500 border-melon-500/30';
        dotCls = 'bg-melon-500';
      }
    } else if (websocketConnected) {
      statusText = 'PILOT BACKEND ONLINE';
      statusBadgeCls = 'bg-leaf-900 text-leaf-500 border-leaf-500/30';
      dotCls = 'bg-leaf-500 animate-pulse-glow';
    } else {
      statusText = 'API ONLINE · WS DISCONNECTED';
      statusBadgeCls = 'bg-warning-d text-warning-400 border-warning-400/30';
      dotCls = 'bg-warning-400';
    }
  }

  const handleRoleChange = async (newRole: 'operator' | 'supervisor' | 'admin') => {
    setRoleSwitching(true);
    try {
      await switchRoleDemo(newRole);
    } catch (e) {
      console.error(e);
    } finally {
      setRoleSwitching(false);
    }
  };

  return (
    <header className="h-[52px] shrink-0 bg-ink-900 border-b border-rind-500/15 flex items-center px-3 md:px-5 gap-2 select-none z-10">
      {/* Mobile Drawer Trigger */}
      <button
        onClick={toggleMobileMenu}
        className="md:hidden w-8 h-8 shrink-0 rounded-rad3 border border-rind-500/20 text-rind-300 hover:text-rind-100 flex items-center justify-center transition-colors"
        aria-label="Open navigation menu"
      >
        <i className="ti ti-menu-2 text-base"></i>
      </button>

      {/* Page Title */}
      <div className="font-display font-bold text-sm flex-1 min-w-0 truncate tracking-tight text-rind-100">
        {pageTitles[currentPage] || 'Command Center'}
      </div>

      {/* Live / Readiness Indicator */}
      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[9px] font-bold tracking-wider uppercase border ${statusBadgeCls}`}>
        <div className={`w-1.5 h-1.5 rounded-full ${dotCls}`} />
        <span className="hidden sm:inline">{statusText}</span>
        <span className="sm:hidden">{apiAvailable ? (readiness?.ready ? (websocketConnected ? 'ONLINE' : 'WS OFF') : 'DEGRADED') : 'OFFLINE'}</span>
      </div>

      {/* Network Latency RTT Badge */}
      {apiAvailable && (
        <div
          className="hidden md:flex items-center gap-1 px-2 py-1 rounded-full text-[9px] font-mono font-bold bg-ink-800 border border-rind-500/15 text-rind-400"
          title="Edge API round-trip network latency"
        >
          <i className={`ti ti-activity text-[10.5px] ${
            latencyPingMs !== null && latencyPingMs < 60
              ? 'text-leaf-500'
              : latencyPingMs !== null && latencyPingMs < 200
              ? 'text-warning-400'
              : 'text-melon-500'
          }`}></i>
          <span>{latencyPingMs !== null ? `${latencyPingMs}ms RTT` : 'RTT --'}</span>
        </div>
      )}

      {/* Telemetry Freshness Badge */}
      {apiAvailable && (
        <div
          className={`hidden lg:flex items-center gap-1 px-2 py-1 rounded-full text-[9px] font-mono font-bold border ${
            telemetryFreshness === 'live'
              ? 'bg-leaf-950/40 text-leaf-400 border-leaf-500/25'
              : telemetryFreshness === 'stale'
              ? 'bg-warning-950/40 text-warning-400 border-warning-400/25'
              : 'bg-ink-800 text-rind-500 border-rind-500/15'
          }`}
          title={
            telemetryFreshness === 'live'
              ? `Telemetry live (${lastMetricsAt ? new Date(lastMetricsAt).toLocaleTimeString() : 'now'})`
              : telemetryFreshness === 'stale'
              ? `Telemetry stale (Last received ${lastMetricsAt ? Math.round((Date.now() - lastMetricsAt) / 1000) : '--'}s ago)`
              : 'Telemetry unavailable'
          }
        >
          <i className={`ti ${telemetryFreshness === 'live' ? 'ti-pulse' : 'ti-alert-circle'} text-[10.5px]`}></i>
          <span>
            {telemetryFreshness === 'live' ? 'TEL LIVE' : telemetryFreshness === 'stale' ? 'TEL STALE' : 'TEL N/A'}
          </span>
        </div>
      )}

      {/* Clock */}
      <div className="font-mono text-xs text-rind-300 bg-ink-800 border border-rind-500/15 px-2.5 py-1 rounded-rad3">
        {timeStr}
      </div>

      <div className="hidden lg:block w-[1px] h-5 bg-rind-500/15 mx-1" />

      {/* Topbar KPIs */}
      <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-rad3 bg-ink-800 border border-rind-500/15" title="Online Cameras">
        <i className="ti ti-video text-xs text-instrument-400"></i>
        <span className="text-xs font-bold text-rind-100 font-mono">{onlineCamsCount}/{cams.length}</span>
        <span className="text-[10px] text-rind-500">cams</span>
      </div>

      <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-rad3 bg-ink-800 border border-rind-500/15" title="Active Alerts">
        <i className="ti ti-alert-triangle text-xs text-melon-500"></i>
        <span className="text-xs font-bold text-rind-100 font-mono">{alerts.length}</span>
        <span className="text-[10px] text-rind-500">alerts</span>
      </div>

      <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-rad3 bg-ink-800 border border-rind-500/15" title="Watchlist Matches">
        <i className="ti ti-fingerprint text-xs text-instrument-400"></i>
        <span className="text-xs font-bold text-rind-100 font-mono">{watchlistCount}</span>
        <span className="text-[10px] text-rind-500">watchlist</span>
      </div>

      <div className="hidden md:block w-[1px] h-5 bg-rind-500/15 mx-1" />

      {/* Weapon Threat Demo Trigger Button */}
      <button
        onClick={triggerWeaponDemo}
        className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-rad3 bg-melon-d border border-melon-500/30 hover:bg-melon-500/20 text-melon-500 text-[11px] font-mono font-bold transition-all active:scale-95"
        title="Trigger simulated weapon threat (or press 'K')"
        aria-label="Trigger simulated weapon threat"
      >
        <i className="ti ti-crosshair text-xs"></i>
        <span>Demo Threat [K]</span>
      </button>

      {/* Armed Toggle */}
      <button
        type="button"
        onClick={toggleArmed}
        aria-label={armed ? 'Disarm surveillance system' : 'Arm surveillance system'}
        className={`hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-rad3 border transition-all select-none ${
          armed ? 'bg-instrument-d border-instrument-400/30' : 'bg-warning-d border-warning-400/30'
        }`}
      >
        <div className={`w-2 h-2 rounded-full transition-all ${
          armed ? 'bg-instrument-400 shadow-[0_0_8px_#56c7d9] animate-pulse-glow' : 'bg-warning-400 shadow-[0_0_8px_#f4bd5b]'
        }`} />
        <span className={`text-[10px] font-bold tracking-wider uppercase ${armed ? 'text-instrument-400' : 'text-warning-400'}`}>
          {armed ? 'Armed' : 'Standby'}
        </span>
      </button>

      {/* Patrol Mode Quick Trigger */}
      <button
        onClick={() => openPatrolModal()}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-rad3 border border-rind-500/20 bg-ink-800 text-rind-300 hover:text-rind-100 hover:border-rind-500/40 text-[10px] font-bold tracking-wider uppercase transition-colors"
        title="Open Field Patrol Tactical Dispatch Mode"
      >
        <i className="ti ti-compass text-instrument-400 text-xs"></i>
        <span className="hidden lg:inline">Patrol Mode</span>
      </button>

      <div className="hidden md:block w-[1px] h-5 bg-rind-500/15 mx-1" />

      {/* RBAC Role Switcher */}
      <div className="hidden xl:flex items-center gap-1 bg-ink-800 border border-rind-500/15 p-0.5 rounded-rad3">
        <span className="text-[9px] text-rind-500 uppercase font-mono px-1.5 font-bold">ROLE</span>
        {(['operator', 'supervisor', 'admin'] as const).map(role => (
          <button
            key={role}
            onClick={() => handleRoleChange(role)}
            disabled={roleSwitching}
            className={`px-2 py-0.5 rounded-rad3 text-[10px] font-bold capitalize transition-all ${
              currentUser?.role === role
                ? role === 'admin'
                  ? 'bg-melon-600 text-white shadow-[0_0_10px_rgba(232,77,82,0.4)]'
                  : role === 'supervisor'
                  ? 'bg-warning-400 text-ink-950 shadow-[0_0_10px_rgba(244,189,91,0.4)]'
                  : 'bg-leaf-500 text-ink-950 shadow-[0_0_10px_rgba(101,214,139,0.4)]'
                : 'text-rind-500 hover:text-rind-100'
            }`}
          >
            {role}
          </button>
        ))}
      </div>

      {/* Fullscreen Button */}
      <button
        onClick={() => {
          if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(() => {});
          } else {
            document.exitFullscreen().catch(() => {});
          }
        }}
        className="w-8 h-8 rounded-rad3 border border-rind-500/15 bg-transparent hover:bg-ink-800 text-rind-500 hover:text-rind-100 flex items-center justify-center text-sm transition-colors ml-0.5"
        title="Toggle Fullscreen"
        aria-label="Toggle Fullscreen"
      >
        <i className="ti ti-maximize"></i>
      </button>
    </header>
  );
};

