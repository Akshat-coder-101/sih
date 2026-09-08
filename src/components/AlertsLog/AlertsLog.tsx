import React, { useState } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';

export const AlertsLog: React.FC = () => {
  const { alerts, cams, openLightbox } = useApp();
  const [filterType, setFilterType] = useState<string>('');
  const [filterSev, setFilterSev] = useState<string>('');
  const [filterCam, setFilterCam] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');

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

  return (
    <div className="flex-1 overflow-y-auto p-[24px]">
      <div className="flex items-center justify-between mb-[22px] flex-wrap gap-[10px]">
        <div>
          <div className="text-[18px] font-[800] tracking-[-0.4px] text-tx">Alerts Log</div>
          <div className="text-[11.5px] text-tx3 mt-[1px]">Full tactical event history with forensic evidence metadata</div>
        </div>
        <button
          onClick={exportCSV}
          className="flex items-center gap-[6px] px-[15px] py-[7px] rounded-rad2 bg-gradient-to-br from-cyan to-cyan-2 text-black font-[700] text-[12px] shadow-[0_0_15px_rgba(0,229,184,0.3)] hover:opacity-90 transition-opacity"
        >
          <i className="ti ti-download text-[14px]"></i>
          Export CSV
        </button>
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
              <th className="px-[13px] py-[9px] text-left">Location</th>
              <th className="px-[13px] py-[9px] text-left">Conf.</th>
              <th className="px-[13px] py-[9px] text-left">Severity</th>
              <th className="px-[13px] py-[9px] text-left">Time</th>
              <th className="px-[13px] py-[9px] text-left">Evidence</th>
              <th className="px-[13px] py-[9px] text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.length > 0 ? (
              filtered.map(a => {
                const meta = TYPE_META[a.type] || TYPE_META.intrusion;
                return (
                  <tr
                    key={a.id}
                    onClick={() => openLightbox(a.id)}
                    className="border-b border-b0 bg-s1 hover:bg-s2 cursor-pointer transition-colors duration-100"
                  >
                    <td className="px-[13px] py-[10px] font-mono text-[10.5px] text-tx3">{a.id}</td>
                    <td className="px-[13px] py-[10px]">
                      <span className={`text-[8.5px] font-[700] uppercase px-[7px] py-[2px] rounded-[4px] border ${meta.cls}`}>
                        {a.type}
                      </span>
                    </td>
                    <td className="px-[13px] py-[10px] max-w-[240px] truncate text-tx font-medium">{a.detail}</td>
                    <td className="px-[13px] py-[10px] text-tx2 whitespace-nowrap">{a.camName.split('·')[0].trim()}</td>
                    <td className="px-[13px] py-[10px] text-tx3 text-[11px] whitespace-nowrap">{a.location}</td>
                    <td className="px-[13px] py-[10px] font-mono">{a.confidence}%</td>
                    <td className="px-[13px] py-[10px]">
                      <span className={`text-[9.5px] font-[700] uppercase px-[8px] py-[2px] rounded-[5px] border ${
                        a.sev === 'high' ? 'bg-red-d text-red border-red/25' : a.sev === 'med' ? 'bg-amber-d text-amber border-amber/25' : 'bg-blue-d text-blue border-blue/25'
                      }`}>
                        {a.sev === 'high' ? 'Critical' : a.sev === 'med' ? 'Warning' : 'Info'}
                      </span>
                    </td>
                    <td className="px-[13px] py-[10px] font-mono text-[10.5px] text-tx3 whitespace-nowrap">
                      {a.ts.toLocaleTimeString('en-IN', { hour12: false })}
                    </td>
                    <td className="px-[13px] py-[10px]">
                      {a.snapshot ? (
                        <span className="flex items-center gap-[4px] text-[10px] font-mono font-bold text-cyan bg-cyan-dd px-[6px] py-[2px] rounded border border-cyan/20">
                          <i className="ti ti-photo"></i> Frame
                        </span>
                      ) : (
                        <span className="text-tx4 text-[10px]">Vector</span>
                      )}
                    </td>
                    <td className="px-[13px] py-[10px]">
                      <span className={`text-[9.5px] font-[700] uppercase px-[8px] py-[2px] rounded-[5px] border ${
                        a.reviewed ? 'bg-cyan-d text-cyan border-cyan/25' : 'bg-s3 text-tx4 border-b1'
                      }`}>
                        {a.reviewed ? 'Reviewed' : 'Pending'}
                      </span>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={10} className="text-center py-[40px] text-tx3">
                  No matching alerts found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
