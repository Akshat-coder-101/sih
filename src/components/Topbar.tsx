import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';

export const Topbar: React.FC = () => {
  const { currentPage, cams, alerts, armed, toggleArmed, triggerWeaponDemo } = useApp();
  const [timeStr, setTimeStr] = useState<string>('--:--:--');

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
    about: 'About IBVAP'
  };

  const onlineCamsCount = cams.filter(c => c.online).length;
  const watchlistCount = alerts.filter(a => a.type === 'watchlist').length;

  return (
    <header className="h-[52px] shrink-0 bg-s1 border-b border-b1 flex items-center px-[20px] gap-[8px] select-none z-10">
      <div className="font-[700] text-[13.5px] flex-1 tracking-[-0.2px] text-tx">
        {pageTitles[currentPage] || 'IBVAP'}
      </div>

      {/* Live Badge */}
      <div className="flex items-center gap-[6px] px-[11px] py-[4px] rounded-[20px] bg-cyan-d border border-cyan/20 text-[9.5px] font-[700] tracking-[1px] uppercase text-cyan">
        <div className="w-[5px] h-[5px] rounded-full bg-cyan animate-pulse-glow" />
        Live
      </div>

      {/* Clock */}
      <div className="font-mono text-[12px] text-tx2 bg-s2 border border-b1 px-[10px] py-[4px] rounded-rad3">
        {timeStr}
      </div>

      <div className="w-[1px] h-[22px] bg-b1 mx-[4px]" />

      {/* Topbar KPIs */}
      <div className="flex items-center gap-[6px] px-[10px] py-[4px] rounded-rad3 bg-s2 border border-b1">
        <i className="ti ti-video text-[13px] text-cyan"></i>
        <span className="text-[12px] font-[700] text-tx font-mono">{onlineCamsCount}/{cams.length}</span>
        <span className="text-[10px] text-tx3">cams online</span>
      </div>

      <div className="flex items-center gap-[6px] px-[10px] py-[4px] rounded-rad3 bg-s2 border border-b1">
        <i className="ti ti-alert-triangle text-[13px] text-red"></i>
        <span className="text-[12px] font-[700] text-tx font-mono">{alerts.length}</span>
        <span className="text-[10px] text-tx3">alerts today</span>
      </div>

      <div className="flex items-center gap-[6px] px-[10px] py-[4px] rounded-rad3 bg-s2 border border-b1">
        <i className="ti ti-fingerprint text-[13px] text-blue"></i>
        <span className="text-[12px] font-[700] text-tx font-mono">{watchlistCount}</span>
        <span className="text-[10px] text-tx3">watchlist hits</span>
      </div>

      <div className="w-[1px] h-[22px] bg-b1 mx-[4px]" />

      {/* Weapon Threat Demo Trigger Button */}
      <button
        onClick={triggerWeaponDemo}
        className="flex items-center gap-[6px] px-[10px] py-[4px] rounded-rad2 bg-red-d border border-red/30 hover:bg-red/20 text-red text-[11px] font-mono font-bold transition-all duration-150 active:scale-95"
        title="Keyboard Shortcut: Press 'K' anytime during presentation"
      >
        <i className="ti ti-crosshair text-[14px]"></i>
        <span>Demo Threat [K]</span>
      </button>

      {/* Armed Toggle */}
      <div
        onClick={toggleArmed}
        className={`flex items-center gap-[7px] px-[12px] py-[5px] rounded-rad2 border cursor-pointer transition-all duration-200 select-none ${
          armed ? 'bg-cyan-d border-cyan/30' : 'bg-amber-d border-amber/30'
        }`}
      >
        <div className={`w-[10px] h-[10px] rounded-full transition-all duration-200 ${
          armed ? 'bg-cyan shadow-[0_0_8px_#00e5b8] animate-pulse-glow' : 'bg-amber shadow-[0_0_8px_#ffa726]'
        }`} />
        <span className={`text-[10px] font-[700] tracking-[1px] uppercase ${armed ? 'text-cyan' : 'text-amber'}`}>
          {armed ? 'Armed' : 'Standby'}
        </span>
      </div>

      <div className="w-[1px] h-[22px] bg-b1 mx-[4px]" />

      {/* Fullscreen Button */}
      <button
        onClick={() => {
          if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
          } else {
            document.exitFullscreen();
          }
        }}
        className="w-[32px] h-[32px] rounded-rad2 border border-b1 bg-transparent hover:bg-s2 text-tx3 hover:text-tx flex items-center justify-center text-[15px] transition-colors duration-150"
        title="Fullscreen"
      >
        <i className="ti ti-maximize"></i>
      </button>
    </header>
  );
};
