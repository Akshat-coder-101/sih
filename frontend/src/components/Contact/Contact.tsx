import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';

export const Contact: React.FC = () => {
  const { showNotice } = useApp();
  const [sent, setSent] = useState(false);

  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSent(true);
    showNotice('success', 'Transmission recorded for the IBVAP deployment operations team.');
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      <div className="max-w-[760px] mx-auto">
        <div className="mb-5">
          <h1 className="text-lg md:text-xl font-bold font-display tracking-tight text-rind-100">Contact &amp; Operations Support</h1>
          <p className="text-xs text-rind-500 mt-0.5">Connect with the engineering and deployment team for field pilot inquiries and telemetry integration.</p>
        </div>
        <div className="grid md:grid-cols-[0.85fr_1.15fr] gap-4">
          <section className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5 h-fit shadow-sm">
            <h2 className="text-xs font-bold font-display text-rind-100 mb-3">Operations Desk</h2>
            <a className="flex items-center gap-2 text-xs text-instrument-400 hover:underline mb-2.5 break-all" href="mailto:team@ibvap.example">
              <i className="ti ti-mail text-sm" /> team@ibvap.example
            </a>
            <a className="flex items-center gap-2 text-xs text-instrument-400 hover:underline break-all" href="tel:+911800123456">
              <i className="ti ti-phone text-sm" /> +91 1800 123 456
            </a>
            <div className="mt-4 pt-3 border-t border-rind-500/10 text-[11px] text-rind-500">
              Headquarters: Border Operations Command Center, BOP Sector Alpha.
            </div>
          </section>
          <form onSubmit={submit} className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5 space-y-3 shadow-sm">
            <h2 className="text-xs font-bold font-display text-rind-100">Transmit Dispatch Note</h2>
            {sent ? (
              <div className="p-3.5 rounded-rad3 bg-leaf-900 border border-leaf-500/30 text-xs text-leaf-500 font-medium">
                Transmission recorded. The engineering response unit will review your request.
              </div>
            ) : (
              <>
                <input required name="name" placeholder="Your Operator Name / Call Sign" aria-label="Your name" className="w-full bg-ink-950 border border-rind-500/20 rounded-rad3 px-3 py-2 text-xs text-rind-100 outline-none focus:border-instrument-400 focus:ring-1 focus:ring-instrument-400 placeholder:text-rind-500" />
                <input required type="email" name="email" placeholder="Operational Email Address" aria-label="Email address" className="w-full bg-ink-950 border border-rind-500/20 rounded-rad3 px-3 py-2 text-xs text-rind-100 outline-none focus:border-instrument-400 focus:ring-1 focus:ring-instrument-400 placeholder:text-rind-500" />
                <textarea required name="message" placeholder="Deployment inquiry or incident feedback..." aria-label="Message" rows={4} className="w-full bg-ink-950 border border-rind-500/20 rounded-rad3 px-3 py-2 text-xs text-rind-100 outline-none focus:border-instrument-400 focus:ring-1 focus:ring-instrument-400 placeholder:text-rind-500 resize-y" />
                <button type="submit" className="px-4 py-2 rounded-rad3 bg-instrument-400 hover:bg-instrument-500 text-ink-950 text-xs font-bold transition-all shadow-sm">
                  Send Transmission
                </button>
              </>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

