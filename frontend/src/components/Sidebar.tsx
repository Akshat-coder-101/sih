import React, { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { PageId } from '../types';

export const Sidebar: React.FC = () => {
  const { currentPage, goToPage, alerts, armed, currentUser, backendConnected, apiAvailable, websocketConnected, readiness, mobileMenuOpen, closeMobileMenu, showNotice } = useApp();

  const criticalCount = alerts.filter(a => a.sev === 'high' && !a.reviewed).length;
  const isAdmin = currentUser?.role === 'admin';

  // Handle Escape key to close mobile menu
  useEffect(() => {
    if (!mobileMenuOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeMobileMenu();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [mobileMenuOpen, closeMobileMenu]);

  const navItems: { id: PageId; label: string; icon: string; group?: string; badge?: number; adminOnly?: boolean }[] = [
    { id: 'monitor', label: 'Live Monitor', icon: 'ti-layout-dashboard', group: 'Surveillance' },
    { id: 'camgrid', label: 'Camera Grid', icon: 'ti-grid-dots' },
    { id: 'alerts', label: 'Alerts Log', icon: 'ti-alert-triangle', group: 'Intelligence', badge: criticalCount },
    { id: 'analytics', label: 'Analytics', icon: 'ti-chart-donut' },
    { id: 'models', label: 'AI Pipeline', icon: 'ti-cpu', group: 'System' },
    { id: 'cam-config', label: 'Camera Config', icon: 'ti-settings-2', adminOnly: true },
    { id: 'contact', label: 'Contact', icon: 'ti-mail' },
  ];

  return (
    <>
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-[90] bg-black/70 backdrop-blur-sm md:hidden transition-opacity"
          onClick={closeMobileMenu}
          aria-hidden="true"
        />
      )}
      <aside
        aria-label="Primary Navigation"
        className={`fixed inset-y-0 left-0 z-[100] w-[240px] min-w-[240px] max-w-[240px] bg-ink-900 border-r border-rind-500/15 flex flex-col overflow-hidden relative select-none transition-transform duration-200 md:static md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full'
        }`}
      >
        {/* Top ambient glow line */}
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-instrument-400/40 to-transparent" />

        {/* Logo / Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-rind-500/10">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-rad3 shrink-0 bg-gradient-to-br from-leaf-500 to-leaf-900 flex items-center justify-center shadow-[0_0_15px_rgba(101,214,139,0.25)]">
              <i className="ti ti-shield-check text-base text-ink-950 font-bold"></i>
            </div>
            <div>
              <div className="text-sm font-bold font-display tracking-tight text-rind-100">IBVAP</div>
              <div className="text-[8.5px] tracking-[1.8px] uppercase text-instrument-400 font-semibold -mt-0.5">Tactical Command</div>
            </div>
          </div>
          {/* Mobile close button */}
          <button
            onClick={closeMobileMenu}
            aria-label="Close navigation drawer"
            className="md:hidden w-7 h-7 rounded-rad3 text-rind-500 hover:text-rind-100 flex items-center justify-center transition-colors"
          >
            <i className="ti ti-x text-base"></i>
          </button>
        </div>

        {/* Navigation */}
        <nav className="py-2 flex-1 overflow-y-auto">
          {navItems.map((item, idx) => {
            const isRestricted = item.adminOnly && !isAdmin;
            const isActive = currentPage === item.id;
            return (
              <React.Fragment key={item.id}>
                {item.group && (
                  <div className={`px-4 pb-1 text-[8.5px] tracking-[1.5px] uppercase text-rind-500 font-bold ${idx > 0 ? 'pt-3.5' : 'pt-2'}`}>
                    {item.group}
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => {
                    if (isRestricted) {
                      showNotice('error', 'Administrator role required for Camera Configuration.');
                      return;
                    }
                    goToPage(item.id);
                  }}
                  className={`w-full flex items-center gap-2.5 px-4 py-2 border-l-2 text-left transition-all duration-150 ${
                    isRestricted
                      ? 'opacity-40 cursor-not-allowed text-rind-500 border-transparent'
                      : isActive
                      ? 'text-instrument-400 border-instrument-400 bg-gradient-to-r from-instrument-dd to-transparent font-semibold cursor-pointer'
                      : 'text-rind-300 border-transparent hover:text-rind-100 hover:bg-ink-800/60 cursor-pointer'
                  }`}
                  title={isRestricted ? 'Administrator role required' : undefined}
                >
                  <i className={`ti ${item.icon} text-base shrink-0 ${isActive ? 'text-instrument-400' : 'text-rind-500'}`}></i>
                  <span className="text-xs font-medium">{item.label}</span>
                  {isRestricted && (
                    <i className="ti ti-lock text-[11px] text-rind-500 ml-auto" title="Admin only"></i>
                  )}
                  {item.badge !== undefined && item.badge > 0 && !isRestricted && (
                    <span className="ml-auto text-[10px] font-bold bg-melon-d text-melon-500 px-1.5 py-0.5 rounded-full border border-melon-500/25 min-w-[18px] text-center">
                      {item.badge}
                    </span>
                  )}
                </button>
              </React.Fragment>
            );
          })}
        </nav>

        {/* Footer System & Backend Status */}
        <div className="p-3 px-4 border-t border-rind-500/10 space-y-2 bg-ink-950/40">
          {/* Arming Status */}
          <div className="flex items-center gap-2 p-2 px-2.5 bg-ink-800/80 border border-rind-500/15 rounded-rad3">
            <div className={`w-2 h-2 rounded-full shrink-0 ${armed ? 'bg-leaf-500 shadow-[0_0_8px_#65d68b] animate-pulse-glow' : 'bg-warning-400 shadow-[0_0_8px_#f4bd5b]'}`}></div>
            <div className="text-[10.5px] text-rind-200 flex-1 font-medium">{armed ? 'System Armed' : 'System Standby'}</div>
            <div className="text-[9.5px] text-rind-500 font-mono">v1.0</div>
          </div>

          {/* Backend Synced Indicator */}
          <div className="flex items-center gap-1.5 px-1 text-[9.5px] font-mono text-rind-500">
            <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${
              apiAvailable ? (readiness?.ready ? 'bg-leaf-500 shadow-[0_0_6px_#65d68b]' : 'bg-warning-400') : 'bg-warning-400'
            }`} />
            <span>{
              apiAvailable
                ? (readiness?.ready
                    ? (websocketConnected ? 'FastAPI + WS Online' : 'FastAPI Online (WS Off)')
                    : 'FastAPI Degraded')
                : 'Offline Demo / Simulation'
            }</span>
          </div>
        </div>
      </aside>
    </>
  );
};

