import React from 'react';

type LegalType = 'privacy' | 'terms';

export const LegalPage: React.FC<{ type: LegalType }> = ({ type }) => {
  const privacy = type === 'privacy';
  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      <article className="max-w-[760px] mx-auto bg-ink-900 border border-rind-500/15 rounded-rad p-5 md:p-7 text-xs text-rind-300 shadow-sm">
        <h1 className="text-lg md:text-xl font-bold font-display text-rind-100 mb-1">{privacy ? 'Privacy Policy' : 'Terms of Use'}</h1>
        <div className="text-[10px] text-rind-500 mb-5 font-mono">IBVAP Platform Documentation &middot; Last updated September 2026</div>
        {privacy ? (
          <>
            <h2 className="text-xs font-bold font-display text-rind-100 mb-2">Data Handled &amp; Privacy Protections</h2>
            <p className="mb-4 leading-relaxed">
              The platform processes CCTV frame streams, bounding-box tracklets, incident evidence snapshots, and cryptographic audit records. Unapproved facial recognition and license plate detections are automatically redacted using on-device masking prior to evidence persistence or preview generation.
            </p>
            <h2 className="text-xs font-bold font-display text-rind-100 mb-2">Local Edge &amp; Browser Processing</h2>
            <p className="mb-4 leading-relaxed">
              Real-time video inference executes on edge devices and client browsers. Camera permissions are strictly user-consented and can be revoked or disconnected at any moment from the Surveillance Monitor.
            </p>
            <h2 className="text-xs font-bold font-display text-rind-100 mb-2">Inquiries &amp; Compliance</h2>
            <p className="leading-relaxed">
              For governance questions regarding forensic data retention and legal holds, contact <a className="text-instrument-400 hover:underline" href="mailto:team@ibvap.example">team@ibvap.example</a>.
            </p>
          </>
        ) : (
          <>
            <h2 className="text-xs font-bold font-display text-rind-100 mb-2">Pilot Operational Scope</h2>
            <p className="mb-4 leading-relaxed">
              IBVAP is an evaluated border video analytics pilot. Simulated benchmark events and generated synthetic feeds are distinctly labelled as non-operational intelligence to preserve tactical integrity.
            </p>
            <h2 className="text-xs font-bold font-display text-rind-100 mb-2">Cryptographic Evidence &amp; Audit Logs</h2>
            <p className="mb-4 leading-relaxed">
              All incident triage states, role transitions, and export actions are appended to a SHA-256 hash-chain ledger. Tampering with persistence records is detected via automated cryptographic verification.
            </p>
            <h2 className="text-xs font-bold font-display text-rind-100 mb-2">Authorized Operation</h2>
            <p className="leading-relaxed">
              Deployment and administrative access are restricted to credentialed defense operators, sector supervisors, and system administrators.
            </p>
          </>
        )}
      </article>
    </div>
  );
};

