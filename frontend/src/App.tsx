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
import { About } from './components/About/About';
import { EvidenceModal } from './components/Modals/EvidenceModal';
import { FullscreenModal } from './components/Modals/FullscreenModal';

export const App: React.FC = () => {
  const { currentPage } = useApp();

  return (
    <div className="flex h-screen w-screen overflow-hidden relative bg-bg text-tx">
      {/* Background ambient lighting */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_800px_600px_at_15%_20%,rgba(0,229,184,0.04)_0%,transparent_70%),radial-gradient(ellipse_600px_500px_at_85%_80%,rgba(77,171,247,0.04)_0%,transparent_70%)]" />

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
            {currentPage === 'about' && <About />}
          </main>
        </div>
      </div>

      {/* Forensic Evidence Lightbox Modal */}
      <EvidenceModal />

      {/* Fullscreen Video Overlay */}
      <FullscreenModal />
    </div>
  );
};
