import React, { useState } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';
import { api, LedgerVerifyResponse } from '../../services/api';

export const AlertsLog: React.FC = () => {
  const { alerts, cams, openLightbox, currentUser } = useApp();
  const [filterType, setFilterType] = useState<string>('');
  const [filterSev, setFilterSev] = useState<string>('');
  const [filterCam, setFilterCam] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');

  // Ledger verification state
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [ledgerResult, setLedgerResult] = useState<LedgerVerifyResponse | null>(null);
  const [showLedgerModal, setShowLedgerModal] = useState<boolean>(false);
  const [tamperLoading, setTamperLoading] = useState<boolean>(false);

  const canExport = currentUser?.role === 'supervisor' || currentUser?.role === 'admin';
  const isAdmin = currentUser?.role === 'admin';

  const filtered = alerts.filter(a => {
    if (filterType && a.type !== filterType) return false;
    if (filterSev && a.sev !== filterSev) return false;
    if (filterCam && a.camId !== filterCam) return false;
    if (filterStatus) {
      if (filterStatus === 'reviewed' && !a.reviewed) return false;
      if (filterStatus === 'pending' && a.reviewed) return false;
    }
    return true;
  }).sort((a, b) => b.ts.getTime() - a.ts.getTime());

  const exportCSV = () => {
    if (!canExport) return;
    const headers = ['Event ID', 'Type', 'Detail', 'Camera', 'Location', 'Confidence (%)', 'Severity', 'Reviewed', 'Timestamp', 'Has Snapshot'];
    const rows = filtered.map(a => [
      a.id,
      a.type,
      `"${a.detail.replace(/"/g, '""')}"`,
      `"${a.camName}"`,
      `"${a.location}"`,
      a.confidence,
      a.sev.toUpperCase(),
      a.reviewed ? 'Yes' : 'No',
      `"${a.ts.toISOString()}"`,
      a.snapshot ? 'Yes' : 'No'
    ]);
    const csvContent = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `IBVAP_Alerts_Export_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleVerifyIntegrity = async () => {
    setIsVerifying(true);
    setShowLedgerModal(true);
    try {
      const res = await api.verifyLedger(currentUser?.accessToken);
      setLedgerResult(res);
    } catch (err: any) {
      setLedgerResult({
        intact: false,
        checkedRecords: 0,
        message: err.message || 'Failed to verify ledger integrity'
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const handleTamperDemo = async () => {
    if (filtered.length === 0) return;
    const targetAlert = filtered[0];
    setTamperLoading(true);
    try {
      let token = currentUser?.accessToken;
      if (!token) {
        const auth = await api.login('admin', 'admin123');
        token = auth.accessToken;
      }
      await api.tamperDemo(targetAlert.id, token);
      // Re-verify immediately to display the live tampered breach!
      const res = await api.verifyLedger(token);
      setLedgerResult(res);
    } catch (err: any) {
      alert('Tamper demo failed: ' + err.message);
    } finally {
      setTamperLoading(false);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-[24px]">
      <div className="flex items-center justify-between mb-[22px] flex-wrap gap-[10px]">
        <div>
          <div className="text-[18px] font-[800] tracking-[-0.4px] text-tx">Alerts Log</div>
          <div className="text-[11.5px] text-tx3 mt-[1px]">Full tactical event history with forensic evidence metadata</div>
        </div>
        
        <div className="flex items-center gap-[8px]">
          {/* FR-8.6: Verify Log Integrity Button */}
          <button
            onClick={handleVerifyIntegrity}
            className="flex items-center gap-[6px] px-[14px] py-[7px] rounded-rad2 bg-cyan-dd border border-cyan/40 text-cyan hover:bg-cyan-d/50 font-[700] text-[12px] shadow-[0_0_12px_rgba(0,229,184,0.15)] transition-all"
            title="Walk the SHA-256 hash-chain ledger to verify no historical records have been altered"
          >
            <i className="ti ti-shield-lock text-[14px]"></i>
            Verify Log Integrity
          </button>

          {/* Export CSV Button (Supervisor+) */}
          <button
            onClick={exportCSV}
            disabled={!canExport}
            className={`flex items-center gap-[6px] px-[15px] py-[7px] rounded-rad2 font-[700] text-[12px] transition-opacity ${
              canExport
                ? 'bg-gradient-to-br from-cyan to-cyan-2 text-black shadow-[0_0_15px_rgba(0,229,184,0.3)] hover:opacity-90 cursor-pointer'
                : 'bg-s3 text-tx4 border border-b1 cursor-not-allowed opacity-60'
            }`}
            title={canExport ? 'Export filtered records to CSV' : 'Supervisor or Admin role required to export'}
          >
            <i className="ti ti-download text-[14px]"></i>
            Export CSV
          </button>
        </div>
      </div>

      {/* Filter Row */}
      <div className="flex gap-[8px] items-center flex-wrap mb-[14px] p-[12px] px-[16px] bg-s2 border border-b1 rounded-rad">
        <span className="text-[9.5px] text-tx3 uppercase tracking-[1px] font-[600]">Filter</span>

        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="bg-s1 border border-b1 rounded-rad3 text-tx2 text-[11.5px] px-[10px] py-[5px] outline-none focus:border-cyan"
        >
          <option value="">All Types</option>
          <option value="intrusion">Intrusion</option>
          <option value="weapon">Weapon Threat</option>
          <option value="watchlist">Watchlist Match</option>
          <option value="anpr">ANPR Match</option>
          <option value="loiter">Loitering</option>
          <option value="night">Night Movement</option>
        </select>

        <select
          value={filterSev}
          onChange={e => setFilterSev(e.target.value)}
          className="bg-s1 border border-b1 rounded-rad3 text-tx2 text-[11.5px] px-[10px] py-[5px] outline-none focus:border-cyan"
        >
          <option value="">All Severity</option>
          <option value="high">Critical</option>
          <option value="med">Warning</option>
          <option value="low">Info</option>
        </select>

        <select
          value={filterCam}
          onChange={e => setFilterCam(e.target.value)}
          className="bg-s1 border border-b1 rounded-rad3 text-tx2 text-[11.5px] px-[10px] py-[5px] outline-none focus:border-cyan"
        >
          <option value="">All Cameras</option>
          {cams.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          className="bg-s1 border border-b1 rounded-rad3 text-tx2 text-[11.5px] px-[10px] py-[5px] outline-none focus:border-cyan"
        >
          <option value="">All Status</option>
          <option value="pending">Pending</option>
          <option value="reviewed">Reviewed</option>
        </select>
      </div>

      {/* Table */}
      <div className="overflow-auto rounded-rad border border-b1">
        <table className="w-full border-collapse text-[12px]">
          <thead>
            <tr className="bg-s2 border-b border-b1 text-tx3 uppercase tracking-[1.4px] text-[9px] font-[700]">
              <th className="px-[13px] py-[9px] text-left">ID</th>
              <th className="px-[13px] py-[9px] text-left">Type</th>
              <th className="px-[13px] py-[9px] text-left">Detail</th>
              <th className="px-[13px] py-[9px] text-left">Camera</th>
              <th className="px-[13px] py-[9px] text-left">Confidence</th>
              <th className="px-[13px] py-[9px] text-left">Severity</th>
              <th className="px-[13px] py-[9px] text-left">Reviewed</th>
              <th className="px-[13px] py-[9px] text-left">Timestamp</th>
              <th className="px-[13px] py-[9px] text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-b0 bg-s1">
            {filtered.map(a => {
              const meta = TYPE_META[a.type] || TYPE_META.intrusion;
              return (
                <tr key={a.id} className="hover:bg-s2 transition-colors">
                  <td className="px-[13px] py-[10px] font-mono font-bold text-cyan text-[11.5px]">{a.id}</td>
                  <td className="px-[13px] py-[10px]">
                    <span className={`px-[7px] py-[2px] rounded-[4px] text-[9px] font-bold uppercase tracking-[0.5px] border ${meta.cls}`}>
                      {a.type}
                    </span>
                  </td>
                  <td className="px-[13px] py-[10px] text-tx font-medium max-w-[280px] truncate" title={a.detail}>
                    {a.detail}
                  </td>
                  <td className="px-[13px] py-[10px] text-tx2">{a.camName.split('·')[0].trim()}</td>
                  <td className="px-[13px] py-[10px] font-mono text-tx2">{a.confidence}%</td>
                  <td className="px-[13px] py-[10px]">
                    <span className={`px-[6px] py-[1px] rounded text-[9px] font-bold uppercase ${
                      a.sev === 'high' ? 'bg-red-d text-red' : a.sev === 'med' ? 'bg-amber-d text-amber' : 'bg-blue-d text-blue'
                    }`}>
                      {a.sev}
                    </span>
                  </td>
                  <td className="px-[13px] py-[10px]">
                    <span className={`text-[10px] font-bold ${a.reviewed ? 'text-cyan' : 'text-amber'}`}>
                      {a.reviewed ? 'Reviewed' : 'Pending'}
                    </span>
                  </td>
                  <td className="px-[13px] py-[10px] font-mono text-tx3 text-[10.5px]">
                    {a.ts.toLocaleString('en-IN', { hour12: false })}
                  </td>
                  <td className="px-[13px] py-[10px] text-right">
                    <button
                      onClick={() => openLightbox(a.id)}
                      className="px-[10px] py-[4px] bg-s2 border border-b1 hover:border-cyan text-tx2 hover:text-cyan text-[10px] rounded-rad3 font-medium transition-colors"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* SHA-256 Hash-Chain Integrity Verification Modal */}
      {showLedgerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-[16px] animate-fade-in">
          <div className="bg-s1 border border-b2 rounded-rad w-full max-w-[560px] overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
            {/* Header */}
            <div className="flex items-center justify-between px-[18px] py-[14px] border-b border-b1 bg-s2">
              <div className="flex items-center gap-[9px]">
                <div className={`w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[15px] ${
                  ledgerResult?.intact ? 'bg-cyan-d text-cyan border border-cyan/30' : 'bg-red-d text-red border border-red/30'
                }`}>
                  <i className={`ti ${ledgerResult?.intact ? 'ti-shield-check' : 'ti-shield-alert'}`}></i>
                </div>
                <div>
                  <div className="text-[14px] font-[800] text-tx">Cryptographic Ledger Integrity</div>
                  <div className="text-[10px] text-tx3 font-mono">SHA-256 Chained Block Verification (FR-10)</div>
                </div>
              </div>
              <button
                onClick={() => setShowLedgerModal(false)}
                className="text-tx3 hover:text-tx text-[16px] p-[4px]"
              >
                <i className="ti ti-x"></i>
              </button>
            </div>

            {/* Content */}
            <div className="p-[20px] space-y-[16px]">
              {isVerifying ? (
                <div className="p-[30px] flex flex-col items-center justify-center gap-[12px]">
                  <div className="w-[32px] h-[32px] border-2 border-cyan border-t-transparent rounded-full animate-spin"></div>
                  <div className="text-[12px] text-tx2 font-medium">Walking SHA-256 hash-chain across alert records...</div>
                </div>
              ) : ledgerResult ? (
                <>
                  {/* Status Banner */}
                  <div className={`p-[14px] rounded-rad border flex items-start gap-[12px] ${
                    ledgerResult.intact
                      ? 'bg-cyan-dd border-cyan/30 text-cyan'
                      : 'bg-red-d border-red/40 text-red'
                  }`}>
                    <i className={`ti ${ledgerResult.intact ? 'ti-circle-check' : 'ti-alert-octagon'} text-[22px] shrink-0 mt-[2px]`}></i>
                    <div>
                      <div className="text-[13px] font-[800] tracking-wide">
                        {ledgerResult.intact ? 'LEDGER CHAIN VERIFIED INTACT' : 'CHAIN INTEGRITY COMPROMISED'}
                      </div>
                      <div className="text-[11px] mt-[2px] opacity-90">
                        {ledgerResult.message}
                      </div>
                    </div>
                  </div>

                  {/* Metadata Stats */}
                  <div className="grid grid-cols-3 gap-[10px]">
                    <div className="p-[10px] bg-s2 border border-b1 rounded-rad3">
                      <div className="text-[9px] uppercase tracking-[1px] text-tx3 font-bold">Records Walked</div>
                      <div className="text-[18px] font-mono font-bold text-tx mt-[2px]">{ledgerResult.checkedRecords}</div>
                    </div>
                    <div className="p-[10px] bg-s2 border border-b1 rounded-rad3">
                      <div className="text-[9px] uppercase tracking-[1px] text-tx3 font-bold">Hash Algorithm</div>
                      <div className="text-[15px] font-mono font-bold text-cyan mt-[2px]">SHA-256</div>
                    </div>
                    <div className="p-[10px] bg-s2 border border-b1 rounded-rad3">
                      <div className="text-[9px] uppercase tracking-[1px] text-tx3 font-bold">Tamper Status</div>
                      <div className={`text-[14px] font-mono font-bold mt-[2px] ${ledgerResult.intact ? 'text-green' : 'text-red'}`}>
                        {ledgerResult.intact ? '0 MUTATIONS' : 'MUTATION DETECTED'}
                      </div>
                    </div>
                  </div>

                  {/* Tampered Record Detail (if broken) */}
                  {!ledgerResult.intact && ledgerResult.brokenAlertId && (
                    <div className="p-[12px] bg-[#2a0f12] border border-red/40 rounded-rad3 text-[11px] font-mono text-red space-y-[4px]">
                      <div className="font-bold">⚠ Breakpoint Details:</div>
                      <div>Sequence Block: #{ledgerResult.brokenAtSeq}</div>
                      <div>Target Alert ID: {ledgerResult.brokenAlertId}</div>
                      <div className="text-[10px] text-tx3 mt-[2px]">
                        The stored record ciphertext no longer matches the immutable ledger hash computed at event creation time.
                      </div>
                    </div>
                  )}

                  {/* Live Judging Demo Action: Tamper Database Record */}
                  <div className="pt-[10px] border-t border-b1 flex items-center justify-between">
                    <div>
                      <div className="text-[11.5px] font-bold text-tx">Live Judging Demo Mode</div>
                      <div className="text-[10px] text-tx3">Directly mutate a DB row bypassing the ledger to verify detection</div>
                    </div>

                    <button
                      onClick={handleTamperDemo}
                      disabled={tamperLoading || !isAdmin}
                      className={`px-[12px] py-[6px] rounded-rad3 font-mono font-bold text-[11px] border transition-all ${
                        isAdmin
                          ? 'bg-red-d border-red/40 text-red hover:bg-red/20 cursor-pointer'
                          : 'bg-s3 border-b1 text-tx4 cursor-not-allowed opacity-50'
                      }`}
                      title={isAdmin ? 'Simulate unauthorized database modification' : 'Admin role required'}
                    >
                      {tamperLoading ? 'Mutating DB...' : '⚡ Simulate Tampering'}
                    </button>
                  </div>
                </>
              ) : null}
            </div>

            {/* Footer */}
            <div className="px-[18px] py-[12px] border-t border-b1 bg-s2 flex justify-end">
              <button
                onClick={() => setShowLedgerModal(false)}
                className="px-[16px] py-[6px] rounded-rad3 bg-s1 border border-b1 text-tx2 hover:text-tx text-[11.5px] font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
