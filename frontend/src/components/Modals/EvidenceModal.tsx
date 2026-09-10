import React from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';
import { getSceneSvg } from '../../services/mockScenes';

export const EvidenceModal: React.FC = () => {
  const { activeLightboxAlert, closeLightbox, markReviewed, cams } = useApp();

  if (!activeLightboxAlert) return null;

  const a = activeLightboxAlert;
  const meta = TYPE_META[a.type] || TYPE_META.intrusion;
  const cam = cams.find(c => c.id === a.camId);
  const isThreat = a.type === 'watchlist' || a.type === 'weapon' || a.sev === 'high';

  const fields = [
    { key: 'Event Type', val: meta.label },
    { key: 'Severity', val: a.sev === 'high' ? 'CRITICAL' : a.sev === 'med' ? 'WARNING' : 'INFO' },
    { key: 'Camera Source', val: a.camName },
    { key: 'Sector Location', val: a.location },
    { key: 'AI Confidence', val: `${a.confidence}%` },
    { key: 'Track ID', val: a.trackId },
    { key: 'Event Detail', val: a.detail },
    { key: 'Timestamp', val: a.ts.toLocaleString('en-GB') },
    { key: 'Audit Status', val: a.reviewed ? 'Verified & Reviewed' : 'Action Pending' },
    { key: 'Event UID', val: a.id },
  ];

  return (
    <div
      onClick={e => {
        if (e.target === e.currentTarget) closeLightbox();
      }}
      className="fixed inset-0 z-[200] bg-black/85 backdrop-blur-[8px] flex items-center justify-center p-[20px] overflow-y-auto animate-fade-in"
    >
      <div className="bg-s1 border border-b2 rounded-rad max-w-[540px] w-full overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.6)]">
        {/* Header */}
        <div className="flex items-center gap-[10px] px-[18px] py-[14px] border-b border-b1 bg-s2">
          <span className={`text-[9px] font-[700] uppercase px-[8px] py-[2px] rounded-[4px] border ${meta.cls}`}>
            {a.type}
          </span>
          <div className="text-[13.5px] font-[700] text-tx flex-1 truncate">
            {meta.label} — {a.id}
          </div>
          <button
            onClick={closeLightbox}
            className="w-[28px] h-[28px] rounded-rad3 border border-b1 hover:bg-red-d hover:text-red flex items-center justify-center text-[14px] text-tx3 transition-colors"
          >
            <i className="ti ti-x"></i>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-[18px]">
          {/* Evidence Frame / Simulated Box */}
          <div className="w-full aspect-[16/10] rounded-rad2 overflow-hidden border border-b1 mb-[16px] bg-[#04070b] relative">
            {a.snapshot ? (
              <img
                src={a.snapshot}
                alt="Forensic Frame Snapshot"
                className="w-full h-full object-cover block"
              />
            ) : (
              <>
                <div
                  className="absolute inset-0"
                  dangerouslySetInnerHTML={{ __html: getSceneSvg(cam?.scene || 'fence') }}
                />
                <div className="cv-vignette absolute inset-0" />
                <div className="scanlines absolute inset-0" />

                {/* Simulated Bounding Box for past mock alerts */}
                <div
                  className={`dbox ${isThreat ? 'threat' : ''}`}
                  style={{
                    left: `${(cam?.anchor.left || 44) - 6}%`,
                    top: `${(cam?.anchor.top || 46) - 4}%`,
                    width: `${(cam?.anchor.w || 10) + 12}%`,
                    height: `${(cam?.anchor.h || 24) + 8}%`,
                    zIndex: 2
                  }}
                >
                  <div className="dbox-tag">{a.type.toUpperCase()} {a.confidence}%</div>
                </div>
              </>
            )}

            {/* Evidence Badges */}
            <div className="absolute top-[9px] right-[9px] z-[3] flex items-center gap-[5px] bg-black/75 px-[9px] py-[4px] rounded-[6px] text-[9.5px] font-[700] text-tx2 border border-b2">
              <i className="ti ti-camera text-cyan"></i>
              {a.snapshot ? 'Live Frame Burn-In' : 'Evidence Capture'}
            </div>

            <div className="absolute bottom-[9px] left-[9px] z-[3] font-mono text-[9px] text-tx2 bg-black/75 px-[8px] py-[3px] rounded-[5px] border border-b1">
              {a.camName.split('·')[0].trim()} · {cam?.geo || 'GPS LOCKED'}
            </div>
          </div>

          {/* Key-Value Fields Grid */}
          <div className="grid grid-cols-2 border border-b1 rounded-rad2 overflow-hidden mb-[14px]">
            {fields.map((f, i) => (
              <div
                key={i}
                className={`p-[9px] px-[12px] border-b border-b0 bg-s2/40 ${
                  i % 2 === 0 ? 'border-r border-b0' : ''
                } ${i >= fields.length - 2 ? 'border-b-0' : ''}`}
              >
                <div className="text-[9px] text-tx3 uppercase tracking-[1px] font-[600] mb-[2px]">{f.key}</div>
                <div className="text-[11.5px] text-tx font-mono font-medium truncate">{f.val}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Modal Actions */}
        <div className="flex gap-[8px] px-[18px] py-[14px] border-t border-b1 bg-s2">
          {!a.reviewed && (
            <button
              onClick={() => markReviewed(a.id)}
              className="flex items-center gap-[6px] px-[15px] py-[7px] rounded-rad2 bg-gradient-to-br from-cyan to-cyan-2 text-black font-[700] text-[12px] hover:opacity-90 transition-opacity"
            >
              <i className="ti ti-check text-[14px]"></i>
              Mark Reviewed &amp; Verified
            </button>
          )}
          <button
            onClick={closeLightbox}
            className="px-[15px] py-[7px] rounded-rad2 border border-b2 text-tx2 hover:bg-s3 hover:text-tx text-[12px] font-[500] transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
