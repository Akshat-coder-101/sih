import React from 'react';
import { useApp } from '../../context/AppContext';

export const NotFound: React.FC = () => {
  const { goToPage } = useApp();
  return (
    <div className="flex-1 flex items-center justify-center p-6 text-center bg-ink-950">
      <div className="max-w-[420px] bg-ink-900 border border-rind-500/15 rounded-rad p-8 shadow-lg">
        <div className="font-mono text-5xl leading-none font-bold text-melon-500 mb-3">404</div>
        <h1 className="text-base font-bold font-display text-rind-100 mb-1.5">Command View Not Found</h1>
        <p className="text-xs text-rind-500 mb-5">The surveillance sector or operational dashboard view you requested does not exist.</p>
        <button
          onClick={() => goToPage('monitor')}
          className="px-4 py-2 rounded-rad3 bg-instrument-400 hover:bg-instrument-500 text-ink-950 text-xs font-bold transition-all shadow-sm"
        >
          Return to Live Monitor
        </button>
      </div>
    </div>
  );
};

