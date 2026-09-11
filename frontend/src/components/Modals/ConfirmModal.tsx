import React, { useEffect, useRef } from 'react';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  isDestructive = false,
  onConfirm,
  onCancel,
}) => {
  const confirmBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', handleKeyDown);
    confirmBtnRef.current?.focus();
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-modal-title"
      className="fixed inset-0 z-[250] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <div className="bg-ink-900 border border-rind-500/20 rounded-rad w-full max-w-[420px] overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
        {/* Header */}
        <div className="flex items-center gap-2.5 px-4 py-3 border-b border-rind-500/15 bg-ink-850">
          <div className={`w-7 h-7 rounded-rad3 flex items-center justify-center text-sm ${
            isDestructive ? 'bg-melon-d text-melon-500 border border-melon-500/30' : 'bg-instrument-d text-instrument-400 border border-instrument-400/30'
          }`}>
            <i className={`ti ${isDestructive ? 'ti-alert-triangle' : 'ti-help-circle'}`}></i>
          </div>
          <h3 id="confirm-modal-title" className="text-sm font-bold font-display text-rind-100 flex-1 truncate">
            {title}
          </h3>
          <button
            onClick={onCancel}
            aria-label="Close dialog"
            className="w-6 h-6 rounded-rad3 text-rind-500 hover:text-rind-100 flex items-center justify-center transition-colors"
          >
            <i className="ti ti-x text-sm"></i>
          </button>
        </div>

        {/* Body */}
        <div className="p-4">
          <p className="text-xs text-rind-300 leading-relaxed">
            {message}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-2 px-4 py-3 bg-ink-850 border-t border-rind-500/15">
          <button
            onClick={onCancel}
            className="px-3.5 py-1.5 rounded-rad3 text-xs font-medium text-rind-300 hover:text-rind-100 bg-ink-800 border border-rind-500/20 transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmBtnRef}
            onClick={onConfirm}
            className={`px-3.5 py-1.5 rounded-rad3 text-xs font-bold transition-all shadow-sm ${
              isDestructive
                ? 'bg-melon-600 hover:bg-melon-700 text-white shadow-melon-glow/30'
                : 'bg-instrument-400 hover:bg-instrument-500 text-ink-950 shadow-instrument-glow/30'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
};
