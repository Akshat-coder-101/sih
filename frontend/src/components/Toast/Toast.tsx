import React, { useEffect } from 'react';

interface ToastProps {
  notice: { type: 'error' | 'success'; message: string };
  onDismiss: () => void;
}

export const Toast: React.FC<ToastProps> = ({ notice, onDismiss }) => {
  useEffect(() => {
    const timer = window.setTimeout(onDismiss, 5000);
    return () => window.clearTimeout(timer);
  }, [notice.message, onDismiss]);

  const isError = notice.type === 'error';

  return (
    <div
      role="status"
      aria-live="polite"
      className={`fixed bottom-4 right-4 z-[500] max-w-[calc(100vw-2rem)] flex items-center gap-3 px-4 py-3 rounded-rad border shadow-2xl bg-ink-900 ${
        isError ? 'border-melon-500/40 text-melon-500' : 'border-leaf-500/40 text-leaf-500'
      }`}
    >
      <i className={`ti ${isError ? 'ti-alert-circle' : 'ti-circle-check'} text-lg shrink-0`} />
      <span className="text-xs text-rind-100 font-medium">{notice.message}</span>
      <button
        onClick={onDismiss}
        className="text-rind-500 hover:text-rind-100 transition-colors p-0.5 ml-1"
        aria-label="Dismiss notification"
      >
        <i className="ti ti-x text-sm" />
      </button>
    </div>
  );
};

