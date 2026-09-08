import React from 'react';
import { useApp } from '../context/AppContext';
import { PageId } from '../types';

export const Sidebar: React.FC = () => {
  const { currentPage, goToPage, alerts, armed } = useApp();

  const criticalCount = alerts.filter(a => a.sev === 'high' && !a.reviewed).length;

  const navItems: { id: PageId; label: string; icon: string; group?: string; badge?: number }[] = [
    { id: 'monitor', label: 'Live Monitor', icon: 'ti-layout-dashboard', group: 'Surveillance' },
    { id: 'camgrid', label: 'Camera Grid', icon: 'ti-grid-dots' },
    { id: 'alerts', label: 'Alerts Log', icon: 'ti-alert-triangle', group: 'Intelligence', badge: criticalCount },
    { id: 'analytics', label: 'Analytics', icon: 'ti-chart-donut' },
    { id: 'models', label: 'AI Pipeline', icon: 'ti-cpu', group: 'System' },
    { id: 'cam-config', label: 'Camera Config', icon: 'ti-settings-2' },
    { id: 'about', label: 'About', icon: 'ti-info-circle' },
  ];

  return (
    <aside className="w-[230px] min-w-[230px] bg-gradient-to-b from-s1 to-s0 border-r border-b1 flex flex-col overflow-hidden relative select-none">
      {/* Top ambient glow line */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-cyan to-transparent opacity-40" />

      {/* Logo */}
      <div className="flex items-center gap-[11px] px-[18px] py-[20px] pb-[16px] border-b border-b0">
        <div className="w-[36px] h-[36px] rounded-[10px] shrink-0 bg-gradient-to-br from-cyan to-[#008a6e] flex items-center justify-center shadow-[0_0_20px_rgba(0,229,184,0.25),0_4px_12px_rgba(0,0,0,0.4)]">
          <i className="ti ti-shield-check text-[18px] text-black font-bold"></i>
        </div>
        <div>
          <div className="text-[15px] font-[800] tracking-[-0.4px] text-tx">IBVAP</div>
          <div className="text-[9px] tracking-[2px] uppercase text-cyan font-[600] -mt-[1px]">Command Center</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="py-[8px] flex-1 overflow-y-auto">
        {navItems.map((item, idx) => (
          <React.Fragment key={item.id}>
            {item.group && (
              <div className={`px-[18px] pb-[4px] text-[8.5px] tracking-[2px] uppercase text-tx4 font-[700] ${idx > 0 ? 'pt-[14px]' : 'pt-[10px]'}`}>
                {item.group}
              </div>
            )}
            <div
              onClick={() => goToPage(item.id)}
              className={`flex items-center gap-[10px] px-[18px] py-[9px] cursor-pointer border-l-2 transition-all duration-150 ${
                currentPage === item.id
                  ? 'text-cyan border-cyan bg-gradient-to-r from-cyan-dd to-transparent'
                  : 'text-tx3 border-transparent hover:text-tx2 hover:bg-b0'
              }`}
            >
              <i className={`ti ${item.icon} text-[16px] shrink-0 ${currentPage === item.id ? 'opacity-100 text-cyan' : 'opacity-80'}`}></i>
              <span className="text-[12.5px] font-[500]">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="ml-auto text-[10px] font-[700] bg-red-d text-red px-[7px] py-[1px] rounded-[20px] border border-red/20 min-w-[20px] text-center">
                  {item.badge}
                </span>
              )}
            </div>
          </React.Fragment>
        ))}
      </nav>

      {/* Footer System Status */}
      <div className="p-[14px] px-[18px] border-t border-b0">
        <div className="flex items-center gap-[8px] p-[8px] px-[10px] bg-cyan-dd border border-cyan/15 rounded-rad2">
          <div className={`w-[7px] h-[7px] rounded-full shrink-0 ${armed ? 'bg-cyan shadow-[0_0_8px_#00e5b8] animate-pulse-glow' : 'bg-amber shadow-[0_0_8px_#ffa726]'}`}></div>
          <div className="text-[10.5px] text-tx2 flex-1 font-medium">{armed ? 'System Armed' : 'System Standby'}</div>
          <div className="text-[9.5px] text-tx3 font-mono">v0.1</div>
        </div>
      </div>
    </aside>
  );
};
