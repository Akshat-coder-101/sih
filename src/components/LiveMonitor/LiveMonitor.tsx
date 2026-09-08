import React from 'react';
import { CamViewport } from './CamViewport';
import { AlertsPanel } from './AlertsPanel';

export const LiveMonitor: React.FC = () => {
  return (
    <div className="flex-1 flex overflow-hidden min-h-0 min-w-0">
      <CamViewport />
      <AlertsPanel />
    </div>
  );
};
