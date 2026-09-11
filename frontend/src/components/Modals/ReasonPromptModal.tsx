import React, { useState, useEffect, useRef } from 'react';

interface ReasonPromptModalProps {
  isOpen: boolean;
  title: string;
  subtitle?: string;
  placeholder?: string;
  defaultReasons?: string[];
  submitLabel?: string;
  isFalsePositive?: boolean;
  onSubmit: (reason: string) => void;
  onCancel: () => void;
}

export const ReasonPromptModal: React.FC<ReasonPromptModalProps> = ({
  isOpen,
  title,
  subtitle,
  placeholder = 'Enter triage reason or operational notes...',
  defaultReasons = [
    'Camera calibration / environmental noise',
    'Authorized security personnel movement',
    'Wildlife / non-human intrusion',
    'Simulated test event verification',
    'Incident investigated and cleared on site'
  ],
  submitLabel = 'Confirm Action',
  isFalsePositive = false,
  onSubmit,
  onCancel,
}) => {
  const [reason, setReason] = useState<string>('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (!isOpen) {
      setReason('');
      return;
    }
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel();
    };
    window.addEventListener('keydown', handleKeyDown);
    setTimeout(() => inputRef.current?.focus(), 50);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) return;
    onSubmit(reason.trim());
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="reason-modal-title"
      className="fixed inset-0 z-[250] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel();
      }}
    >
      <div className="bg-ink-900 border border-rind-500/20 rounded-rad w-full max-w-[480px] overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
        {/* Header */}
        <div className="flex items-center gap-2.5 px-4 py-3 border-b border-rind-500/15 bg-ink-850">
          <div className={`w-7 h-7 rounded-rad3 flex items-center justify-center text-sm ${
            isFalsePositive ? 'bg-warning-d text-warning-400 border border-warning-400/30' : 'bg-instrument-d text-instrument-400 border border-instrument-400/30'
          }`}>
            <i className={`ti ${isFalsePositive ? 'ti-alert-circle' : 'ti-edit'}`}></i>
          </div>
          <div className="flex-1 min-w-0">
            <h3 id="reason-modal-title" className="text-sm font-bold font-display text-rind-100 truncate">
              {title}
            </h3>
            {subtitle && (
              <p className="text-[10.5px] text-rind-500 truncate">{subtitle}</p>
            )}
          </div>
          <button
            onClick={onCancel}
            aria-label="Close dialog"
            className="w-6 h-6 rounded-rad3 text-rind-500 hover:text-rind-100 flex items-center justify-center transition-colors"
          >
            <i className="ti ti-x text-sm"></i>
          </button>
        </div>

        {/* Body */}
        <form onSubmit={handleSubmit} className="p-4 space-y-3">
          {/* Quick Select Buttons */}
          <div>
            <label className="text-[10px] font-bold uppercase tracking-wider text-rind-500 mb-1.5 block">
              Quick Reason Codes:
            </label>
            <div className="flex flex-wrap gap-1.5">
              {defaultReasons.map((r, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setReason(r)}
                  className={`text-[10.5px] px-2.5 py-1 rounded-rad3 border text-left transition-colors ${
                    reason === r
                      ? 'bg-instrument-d text-instrument-400 border-instrument-400/40 font-medium'
                      : 'bg-ink-800 text-rind-300 border-rind-500/20 hover:text-rind-100 hover:border-rind-500/40'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>

          {/* Text Area */}
          <div>
            <label htmlFor="reason-text" className="text-[10px] font-bold uppercase tracking-wider text-rind-500 mb-1 block">
              Audit Justification / Resolution Note (Required):
            </label>
            <textarea
              id="reason-text"
              ref={inputRef}
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder={placeholder}
              required
              className="w-full bg-ink-950 border border-rind-500/25 rounded-rad3 text-rind-100 text-xs p-2.5 outline-none focus:border-instrument-400 focus:ring-1 focus:ring-instrument-400 transition-colors placeholder:text-rind-500"
            />
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-rind-500/15">
            <button
              type="button"
              onClick={onCancel}
              className="px-3.5 py-1.5 rounded-rad3 text-xs font-medium text-rind-300 hover:text-rind-100 bg-ink-800 border border-rind-500/20 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!reason.trim()}
              className={`px-3.5 py-1.5 rounded-rad3 text-xs font-bold transition-all shadow-sm ${
                !reason.trim()
                  ? 'bg-ink-800 text-rind-500 border border-rind-500/20 cursor-not-allowed'
                  : isFalsePositive
                  ? 'bg-warning-400 hover:bg-warning-500 text-ink-950 shadow-warning-glow/30'
                  : 'bg-instrument-400 hover:bg-instrument-500 text-ink-950 shadow-instrument-glow/30'
              }`}
            >
              {submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
