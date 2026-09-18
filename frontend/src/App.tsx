import React from 'react';
import { useApp } from './context/AppContext';
import { Sidebar } from './components/Sidebar';
import { Topbar } from './components/Topbar';
import { LiveMonitor } from './components/LiveMonitor/LiveMonitor';
import { CameraGrid } from './components/CameraGrid/CameraGrid';
import { AlertsLog } from './components/AlertsLog/AlertsLog';
import { Analytics } from './components/Analytics/Analytics';
import { AiPipeline } from './components/AiPipeline/AiPipeline';
import { CameraConfig } from './components/CameraConfig/CameraConfig';
import { EvidenceModal } from './components/Modals/EvidenceModal';
import { FullscreenModal } from './components/Modals/FullscreenModal';
import { Contact } from './components/Contact/Contact';
import { LegalPage } from './components/LegalPage/LegalPage';
import { NotFound } from './components/NotFound/NotFound';
import { Toast } from './components/Toast/Toast';
import { PatrolModal } from './components/Modals/PatrolModal';

export const App: React.FC = () => {
  const { currentPage, notice, dismissNotice, activePatrolAlert, closePatrolModal, updateAlertState } = useApp();

  React.useEffect(() => {
    const titles: Record<string, string> = {
      monitor: 'Live Monitor', camgrid: 'Camera Grid', alerts: 'Alerts Log',
      analytics: 'Analytics', models: 'AI Pipeline', 'cam-config': 'Camera Configuration',
      contact: 'Contact IBVAP', privacy: 'Privacy Policy', terms: 'Terms of Use',
      'not-found': 'Page Not Found'
    };
    document.title = `${titles[currentPage] || 'IBVAP'} | Command Center`;
  }, [currentPage]);

  return (
    <div className="flex h-screen w-screen overflow-hidden relative bg-ink-950 text-rind-100 font-sans">
      {/* Background ambient lighting */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_800px_600px_at_15%_20%,rgba(86,199,217,0.03)_0%,transparent_70%),radial-gradient(ellipse_600px_500px_at_85%_80%,rgba(101,214,139,0.03)_0%,transparent_70%)]" />

      {/* Main Container */}
      <div className="flex w-full h-full relative z-1">
        <Sidebar />

        <div className="flex-1 flex flex-col overflow-hidden min-w-0">
          <Topbar />

          {/* Page Routing */}
          <main className="flex-1 flex overflow-hidden min-h-0 min-w-0">
            {currentPage === 'monitor' && <LiveMonitor />}
            {currentPage === 'camgrid' && <CameraGrid />}
            {currentPage === 'alerts' && <AlertsLog />}
            {currentPage === 'analytics' && <Analytics />}
            {currentPage === 'models' && <AiPipeline />}
            {currentPage === 'cam-config' && <CameraConfig />}
            {currentPage === 'contact' && <Contact />}
            {(currentPage === 'privacy' || currentPage === 'terms') && <LegalPage type={currentPage} />}
            {currentPage === 'not-found' && <NotFound />}
          </main>
        </div>
      </div>

      {/* Mobile Patrol Tactical Dispatch Modal */}
      {activePatrolAlert && (
        <PatrolModal
          alert={activePatrolAlert}
          onClose={closePatrolModal}
          onAcknowledge={(alertId) => updateAlertState(alertId, 'acknowledged')}
        />
      )}

      {/* Forensic Evidence Lightbox Modal */}
      <EvidenceModal />

      {/* Fullscreen Video Overlay */}
      <FullscreenModal />
      {notice && <Toast notice={notice} onDismiss={dismissNotice} />}
    </div>
  );
};
