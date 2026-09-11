import React, { useState } from 'react';
import { useApp, TYPE_META } from '../../context/AppContext';
import {
  api,
  LedgerVerifyResponse,
  LedgerAnchor,
  LedgerAnchorVerifyResult,
  MerkleProof,
  MerkleProofVerifyResult,
  AlertProvenance as AlertProvenanceType,
  AlertProvenanceVerifyResult,
  AnchorProposal,
} from '../../services/api';
import { AlertState, AlertProvenance } from '../../types';
import { ReasonPromptModal } from '../Modals/ReasonPromptModal';

export const AlertsLog: React.FC = () => {
  const { alerts, cams, openLightbox, currentUser, updateAlertState, showNotice } = useApp();
  const [filterType, setFilterType] = useState<string>('');
  const [filterSev, setFilterSev] = useState<string>('');
  const [filterCam, setFilterCam] = useState<string>('');
  const [filterState, setFilterState] = useState<string>('');
  const [filterProvenance, setFilterProvenance] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Ledger verification state
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [ledgerResult, setLedgerResult] = useState<LedgerVerifyResponse | null>(null);
  const [showLedgerModal, setShowLedgerModal] = useState<boolean>(false);
  const [tamperLoading, setTamperLoading] = useState<boolean>(false);
  const [exportLoading, setExportLoading] = useState<boolean>(false);

  // Blockchain Anchoring State (PRD v1.0)
  const [anchors, setAnchors] = useState<LedgerAnchor[]>([]);
  const [selectedAnchor, setSelectedAnchor] = useState<LedgerAnchor | null>(null);
  const [anchorVerifyResult, setAnchorVerifyResult] = useState<LedgerAnchorVerifyResult | null>(null);
  const [isAnchorVerifying, setIsAnchorVerifying] = useState<boolean>(false);
  const [isAnchoring, setIsAnchoring] = useState<boolean>(false);
  const [copiedHash, setCopiedHash] = useState<boolean>(false);
  const [showAnchorForm, setShowAnchorForm] = useState<boolean>(false);
  const [anchorFromSeq, setAnchorFromSeq] = useState<number>(0);
  const [anchorThroughSeq, setAnchorThroughSeq] = useState<number>(0);

  // Multisig & Tab State (Advanced Integrity)
  const [activeLedgerTab, setActiveLedgerTab] = useState<'anchors' | 'proposals'>('anchors');
  const [proposals, setProposals] = useState<AnchorProposal[]>([]);
  const [isProposalsLoading, setIsProposalsLoading] = useState<boolean>(false);
  const [showProposalForm, setShowProposalForm] = useState<boolean>(false);
  const [proposalFromSeq, setProposalFromSeq] = useState<number>(0);
  const [proposalThroughSeq, setProposalThroughSeq] = useState<number>(0);
  const [isCreatingProposal, setIsCreatingProposal] = useState<boolean>(false);
  const [rejectingProposalId, setRejectingProposalId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState<string>('');

  // Merkle Proof Inspection Modal State
  const [proofTargetAlertId, setProofTargetAlertId] = useState<string | null>(null);
  const [merkleProof, setMerkleProof] = useState<MerkleProof | null>(null);
  const [isProofLoading, setIsProofLoading] = useState<boolean>(false);
  const [proofVerifyResult, setProofVerifyResult] = useState<MerkleProofVerifyResult | null>(null);
  const [isProofVerifying, setIsProofVerifying] = useState<boolean>(false);

  // Model Provenance Inspection Modal State
  const [provTargetAlertId, setProvTargetAlertId] = useState<string | null>(null);
  const [alertProvenance, setAlertProvenance] = useState<AlertProvenanceType | null>(null);
  const [isProvLoading, setIsProvLoading] = useState<boolean>(false);
  const [provVerifyResult, setProvVerifyResult] = useState<AlertProvenanceVerifyResult | null>(null);
  const [isProvVerifying, setIsProvVerifying] = useState<boolean>(false);

  // Reason Code Prompt Modal State
  const [promptTarget, setPromptTarget] = useState<{ id: string; targetState: 'resolved' | 'false_positive' } | null>(null);

  const canExport = currentUser?.role === 'supervisor' || currentUser?.role === 'admin';
  const isAdmin = currentUser?.role === 'admin';
  const isSupervisor = currentUser?.role === 'supervisor' || currentUser?.role === 'admin';

  const filtered = alerts.filter(a => {
    if (filterType && a.type !== filterType) return false;
    if (filterSev && a.sev !== filterSev) return false;
    if (filterCam && a.camId !== filterCam) return false;
    if (filterState && (a.state || (a.reviewed ? 'resolved' : 'open')) !== filterState) return false;
    if (filterProvenance && (a.provenance || 'detector') !== filterProvenance) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchId = a.id.toLowerCase().includes(q);
      const matchDetail = a.detail.toLowerCase().includes(q);
      const matchCam = a.camName.toLowerCase().includes(q);
      if (!matchId && !matchDetail && !matchCam) return false;
    }
    return true;
  }).sort((a, b) => b.ts.getTime() - a.ts.getTime());

  const handleExportCSV = async () => {
    if (!canExport) {
      showNotice('error', 'Supervisor or Administrator role required for audit CSV export.');
      return;
    }
    setExportLoading(true);
    try {
      await api.downloadAlertsCsv(currentUser?.accessToken);
      showNotice('success', 'Cryptographically verified CSV export downloaded.');
    } catch (err: any) {
      showNotice('error', `Server export failed: ${err.message}. To maintain audit integrity, offline downloads are prohibited.`);
    } finally {
      setExportLoading(false);
    }
  };

  const loadAnchors = async () => {
    try {
      const list = await api.getAnchors(undefined, undefined, currentUser?.accessToken);
      setAnchors(list);
      if (list.length > 0) {
        setSelectedAnchor(list[0]);
      }
    } catch {
      // Non-blocking for offline / disabled modes
    }
  };

  const handleVerifyIntegrity = async () => {
    setIsVerifying(true);
    setShowLedgerModal(true);
    setAnchorVerifyResult(null);
    try {
      const res = await api.verifyLedger(currentUser?.accessToken);
      setLedgerResult(res);
      if (res.checkedRecords > 0) {
        setAnchorThroughSeq(Math.max(0, res.checkedRecords - 1));
        setProposalThroughSeq(Math.max(0, res.checkedRecords - 1));
      }
      await Promise.all([loadAnchors(), loadProposals()]);
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

  const loadProposals = async () => {
    setIsProposalsLoading(true);
    try {
      const list = await api.getAnchorProposals(undefined, undefined, currentUser?.accessToken);
      setProposals(list);
    } catch {
      // Non-blocking
    } finally {
      setIsProposalsLoading(false);
    }
  };

  const handleOpenMerkleProof = async (alertId: string) => {
    setProofTargetAlertId(alertId);
    setProofVerifyResult(null);
    setIsProofLoading(true);
    try {
      const p = await api.getAlertMerkleProof(alertId, currentUser?.accessToken);
      setMerkleProof(p);
    } catch (err: any) {
      showNotice('error', 'Failed to load Merkle proof: ' + err.message);
      setProofTargetAlertId(null);
    } finally {
      setIsProofLoading(false);
    }
  };

  const handleVerifyMerkleProof = async () => {
    if (!merkleProof) return;
    setIsProofVerifying(true);
    try {
      const res = await api.verifyMerkleProof(merkleProof, currentUser?.accessToken);
      setProofVerifyResult(res);
      if (res.valid) {
        showNotice('success', 'Merkle inclusion proof verified: alert is included in the root!');
      } else {
        showNotice('error', 'Merkle verification failed: ' + res.message);
      }
    } catch (err: any) {
      showNotice('error', 'Proof verification error: ' + err.message);
    } finally {
      setIsProofVerifying(false);
    }
  };

  const handleOpenProvenance = async (alertId: string) => {
    setProvTargetAlertId(alertId);
    setProvVerifyResult(null);
    setIsProvLoading(true);
    try {
      const p = await api.getAlertProvenance(alertId, currentUser?.accessToken);
      setAlertProvenance(p);
    } catch (err: any) {
      showNotice('error', 'Failed to load provenance: ' + err.message);
      setProvTargetAlertId(null);
    } finally {
      setIsProvLoading(false);
    }
  };

  const handleVerifyProvenance = async () => {
    if (!provTargetAlertId) return;
    setIsProvVerifying(true);
    try {
      const res = await api.verifyAlertProvenance(provTargetAlertId, currentUser?.accessToken);
      setProvVerifyResult(res);
      if (res.matches) {
        showNotice('success', 'Model and rule provenance verified intact.');
      } else {
        showNotice('error', 'Provenance mismatch: ' + res.message);
      }
    } catch (err: any) {
      showNotice('error', 'Provenance verification error: ' + err.message);
    } finally {
      setIsProvVerifying(false);
    }
  };

  const handleCreateProposal = async () => {
    if (!isAdmin) return;
    setIsCreatingProposal(true);
    try {
      const p = await api.createAnchorProposal({
        fromSequence: Number(proposalFromSeq),
        throughSequence: Number(proposalThroughSeq),
        expiresInHours: 24,
      }, currentUser?.accessToken);
      showNotice('success', `Created multisig proposal ${p.id}!`);
      setShowProposalForm(false);
      loadProposals();
    } catch (err: any) {
      showNotice('error', 'Failed to create proposal: ' + err.message);
    } finally {
      setIsCreatingProposal(false);
    }
  };

  const handleSignProposal = async (proposalId: string) => {
    if (!isSupervisor) return;
    try {
      const p = await api.signAnchorProposal(proposalId, undefined, currentUser?.accessToken);
      showNotice('success', `Signed proposal ${proposalId} (Status: ${p.status}, ${p.signaturesCount}/${p.thresholdRequired} signatures)`);
      loadProposals();
    } catch (err: any) {
      showNotice('error', 'Failed to sign proposal: ' + err.message);
    }
  };

  const handleRejectProposal = async () => {
    if (!rejectingProposalId || !rejectionReason.trim()) return;
    try {
      await api.rejectAnchorProposal(rejectingProposalId, rejectionReason, currentUser?.accessToken);
      showNotice('error', `Rejected proposal ${rejectingProposalId}`);
      setRejectingProposalId(null);
      setRejectionReason('');
      loadProposals();
    } catch (err: any) {
      showNotice('error', 'Failed to reject proposal: ' + err.message);
    }
  };

  const handleSubmitProposal = async (proposalId: string) => {
    if (!isAdmin) return;
    try {
      const p = await api.submitAnchorProposal(proposalId, currentUser?.accessToken);
      showNotice('success', `Submitted proposal ${proposalId} to blockchain (Status: ${p.status})`);
      loadProposals();
    } catch (err: any) {
      showNotice('error', 'Submission failed: ' + err.message);
    }
  };

  const handleVerifyAnchor = async (anchorId: string) => {
    if (!isSupervisor) {
      showNotice('error', 'Supervisor or Admin role required to verify blockchain anchors.');
      return;
    }
    setIsAnchorVerifying(true);
    try {
      const res = await api.verifyAnchor(anchorId, currentUser?.accessToken);
      setAnchorVerifyResult(res);
      if (res.verified) {
        showNotice('success', `On-chain anchor commitment verified against local ledger!`);
      } else {
        showNotice('error', `Anchor verification failed: ${res.message}`);
      }
      await loadAnchors();
    } catch (err: any) {
      showNotice('error', 'Blockchain verification failed: ' + err.message);
    } finally {
      setIsAnchorVerifying(false);
    }
  };

  const handleCreateAnchor = async () => {
    if (!isAdmin) {
      showNotice('error', 'Administrator role required to anchor ledger range to blockchain.');
      return;
    }
    setIsAnchoring(true);
    try {
      const created = await api.anchorLedger({
        fromSequence: Number(anchorFromSeq),
        throughSequence: Number(anchorThroughSeq),
        force: false,
      }, currentUser?.accessToken);
      showNotice('success', `Anchored sequence range [${created.fromSequence}, ${created.throughSequence}] (Anchor ID: ${created.id})`);
      setShowAnchorForm(false);
      await loadAnchors();
      setSelectedAnchor(created);
    } catch (err: any) {
      showNotice('error', 'Anchor creation failed: ' + err.message);
    } finally {
      setIsAnchoring(false);
    }
  };

  const handleRetryAnchor = async (anchorId: string) => {
    if (!isAdmin) return;
    try {
      const retried = await api.retryAnchor(anchorId, currentUser?.accessToken);
      showNotice('success', `Retried anchor ${retried.id}: status is now ${retried.status}`);
      await loadAnchors();
      setSelectedAnchor(retried);
    } catch (err: any) {
      showNotice('error', 'Retry failed: ' + err.message);
    }
  };

  const handleCopyHash = (text: string) => {
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(text);
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
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
      showNotice('error', `Simulated database tamper injected on ${targetAlert.id}!`);
      // Re-verify immediately to display the live tampered breach!
      const res = await api.verifyLedger(token);
      setLedgerResult(res);
    } catch (err: any) {
      showNotice('error', 'Tamper demo failed: ' + err.message);
    } finally {
      setTamperLoading(false);
    }
  };

  const handleReasonSubmit = (reason: string) => {
    if (!promptTarget) return;
    updateAlertState(promptTarget.id, promptTarget.targetState, currentUser?.username || 'operator', reason);
    setPromptTarget(null);
  };

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      {/* View Header */}
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <h1 className="text-lg md:text-xl font-bold font-display tracking-tight text-rind-100">Alerts Operations Log</h1>
          <p className="text-xs text-rind-500 mt-0.5">Tactical event history, triage lifecycle, and cryptographic evidence verification</p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Export CSV Button */}
          <button
            onClick={handleExportCSV}
            disabled={!canExport || exportLoading}
            title={canExport ? 'Export audit-verified CSV report' : 'Requires Supervisor or Admin role'}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-rad3 text-xs font-semibold transition-all border ${
              canExport
                ? 'bg-ink-900 border-rind-500/20 text-rind-100 hover:border-instrument-400 hover:text-instrument-400 hover:bg-ink-850 shadow-sm'
                : 'bg-ink-900/50 border-rind-500/10 text-rind-500 cursor-not-allowed opacity-60'
            }`}
          >
            <i className={`ti ${exportLoading ? 'ti-loader animate-spin' : 'ti-download'} text-sm`} />
            <span>Export CSV</span>
            {!canExport && <span className="text-[9.5px] text-warning-400">(Supervisor)</span>}
          </button>

          {/* Cryptographic Ledger Verify Button */}
          <button
            onClick={handleVerifyIntegrity}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-instrument-d border border-instrument-400/40 hover:border-instrument-400 text-instrument-400 hover:bg-instrument-400/20 text-xs font-bold rounded-rad3 transition-all shadow-[0_0_15px_rgba(86,199,217,0.15)]"
          >
            <i className="ti ti-shield-check text-sm"></i>
            <span>Verify Log Integrity</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-ink-900 p-3 rounded-rad border border-rind-500/15 mb-4 flex flex-wrap gap-2 items-center">
        <span className="text-xs text-rind-500 font-semibold mr-1">Filters:</span>

        {/* Search Box */}
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search ID, camera, detail..."
            className="bg-ink-950 border border-rind-500/20 rounded-rad3 text-rind-100 text-xs pl-7 pr-2.5 py-1.5 outline-none focus:border-instrument-400 w-44 md:w-56 placeholder:text-rind-500"
          />
          <i className="ti ti-search absolute left-2 top-2 text-xs text-rind-500 pointer-events-none"></i>
        </div>

        <select
          value={filterType}
          onChange={e => setFilterType(e.target.value)}
          className="bg-ink-950 border border-rind-500/20 rounded-rad3 text-rind-200 text-xs px-2.5 py-1.5 outline-none focus:border-instrument-400"
        >
          <option value="">All Alert Types</option>
          <option value="intrusion">Virtual Fence Intrusion</option>
          <option value="weapon">Weapon / Threat</option>
          <option value="watchlist">Watchlist Match</option>
          <option value="anpr">ANPR Plate</option>
          <option value="loiter">Loitering</option>
          <option value="night">Night Movement</option>
        </select>

        <select
          value={filterSev}
          onChange={e => setFilterSev(e.target.value)}
          className="bg-ink-950 border border-rind-500/20 rounded-rad3 text-rind-200 text-xs px-2.5 py-1.5 outline-none focus:border-instrument-400"
        >
          <option value="">All Severity</option>
          <option value="high">High (Critical)</option>
          <option value="med">Medium (Warning)</option>
          <option value="low">Low (Info)</option>
        </select>

        <select
          value={filterCam}
          onChange={e => setFilterCam(e.target.value)}
          className="bg-ink-950 border border-rind-500/20 rounded-rad3 text-rind-200 text-xs px-2.5 py-1.5 outline-none focus:border-instrument-400"
        >
          <option value="">All Cameras</option>
          {cams.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        <select
          value={filterState}
          onChange={e => setFilterState(e.target.value)}
          className="bg-ink-950 border border-rind-500/20 rounded-rad3 text-rind-200 text-xs px-2.5 py-1.5 outline-none focus:border-instrument-400"
        >
          <option value="">All Lifecycle States</option>
          <option value="open">Open (Unreviewed)</option>
          <option value="acknowledged">Acknowledged</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>

        <select
          value={filterProvenance}
          onChange={e => setFilterProvenance(e.target.value)}
          className="bg-ink-950 border border-rind-500/20 rounded-rad3 text-rind-200 text-xs px-2.5 py-1.5 outline-none focus:border-instrument-400"
        >
          <option value="">All Provenance</option>
          <option value="detector">Live Detector AI</option>
          <option value="simulation">Simulation</option>
        </select>

        <span className="text-[10px] text-rind-500 font-mono ml-auto">
          Showing {filtered.length} of {alerts.length} events
        </span>
      </div>

      {/* Table with Bounded Responsive Scrolling */}
      <div className="overflow-x-auto rounded-rad border border-rind-500/15 bg-ink-900 shadow-sm max-w-full">
        <table className="w-full border-collapse text-xs min-w-[760px]">
          <thead>
            <tr className="bg-ink-850 border-b border-rind-500/15 text-rind-500 uppercase tracking-wider text-[9px] font-bold">
              <th className="px-3.5 py-2.5 text-left">ID</th>
              <th className="px-3.5 py-2.5 text-left">Type</th>
              <th className="px-3.5 py-2.5 text-left">Provenance</th>
              <th className="px-3.5 py-2.5 text-left">Detail</th>
              <th className="px-3.5 py-2.5 text-left">Camera</th>
              <th className="px-3.5 py-2.5 text-left">Conf</th>
              <th className="px-3.5 py-2.5 text-left">Sev</th>
              <th className="px-3.5 py-2.5 text-left">State</th>
              <th className="px-3.5 py-2.5 text-left">Timestamp</th>
              <th className="px-3.5 py-2.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-rind-500/10 bg-ink-900">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan={10} className="px-4 py-12 text-center">
                  <i className="ti ti-inbox text-3xl text-rind-500 opacity-50" />
                  <div className="text-xs font-bold text-rind-100 mt-2">No matching alerts found</div>
                  <div className="text-[11px] text-rind-500 mt-0.5">Try adjusting your filters or search terms.</div>
                </td>
              </tr>
            ) : filtered.map(a => {
              const meta = TYPE_META[a.type] || TYPE_META.intrusion;
              const currentState = a.state || (a.reviewed ? 'resolved' : 'open');
              const isDetector = (a.provenance || 'detector') === 'detector';
              return (
                <tr key={a.id} className="hover:bg-ink-800 transition-colors">
                  <td className="px-3.5 py-2.5 font-mono font-bold text-instrument-400 text-xs">{a.id}</td>
                  <td className="px-3.5 py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider border ${
                      a.sev === 'high' ? 'bg-melon-d text-melon-500 border-melon-500/30' : 'bg-instrument-d text-instrument-400 border-instrument-400/30'
                    }`}>
                      {a.type}
                    </span>
                  </td>
                  <td className="px-3.5 py-2.5">
                    <span className={`px-1.5 py-0.5 rounded text-[8.5px] font-bold uppercase ${
                      isDetector ? 'bg-leaf-900 text-leaf-500 border border-leaf-500/30' : 'bg-ink-800 text-rind-500 border border-rind-500/20'
                    }`}>
                      {isDetector ? 'DETECTOR' : 'SIMULATION'}
                    </span>
                  </td>
                  <td className="px-3.5 py-2.5 text-rind-100 font-medium max-w-[240px] truncate" title={a.detail}>
                    {a.detail}
                  </td>
                  <td className="px-3.5 py-2.5 text-rind-300">{a.camName.split('·')[0].trim()}</td>
                  <td className="px-3.5 py-2.5 font-mono text-rind-300">{a.confidence}%</td>
                  <td className="px-3.5 py-2.5">
                    <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                      a.sev === 'high' ? 'bg-melon-d text-melon-500' : a.sev === 'med' ? 'bg-warning-d text-warning-400' : 'bg-instrument-d text-instrument-400'
                    }`}>
                      {a.sev}
                    </span>
                  </td>
                  <td className="px-3.5 py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase ${
                      currentState === 'open' ? 'bg-melon-d text-melon-500 border border-melon-500/30' :
                      currentState === 'acknowledged' ? 'bg-warning-d text-warning-400 border border-warning-400/30' :
                      currentState === 'false_positive' ? 'bg-ink-800 text-rind-500 border border-rind-500/25' :
                      'bg-leaf-900 text-leaf-500 border border-leaf-500/30'
                    }`}>
                      {currentState}
                    </span>
                  </td>
                  <td className="px-3.5 py-2.5 font-mono text-rind-500 text-[10.5px]">
                    {a.ts.toLocaleString('en-IN', { hour12: false })}
                  </td>
                  <td className="px-3.5 py-2.5 text-right space-x-1 whitespace-nowrap">
                    {currentState === 'open' && (
                      <button
                        onClick={() => updateAlertState(a.id, 'acknowledged')}
                        title="Acknowledge Alert"
                        className="px-2 py-1 bg-warning-d hover:bg-warning-500/20 text-warning-400 border border-warning-400/30 text-[9.5px] rounded font-semibold transition-colors"
                      >
                        Ack
                      </button>
                    )}
                    {currentState !== 'resolved' && currentState !== 'false_positive' && (
                      <>
                        <button
                          onClick={() => setPromptTarget({ id: a.id, targetState: 'resolved' })}
                          title="Resolve Alert with Justification Note"
                          className="px-2 py-1 bg-leaf-900 hover:bg-leaf-900/80 text-leaf-500 border border-leaf-500/30 text-[9.5px] rounded font-semibold transition-colors"
                        >
                          Resolve
                        </button>
                        <button
                          onClick={() => setPromptTarget({ id: a.id, targetState: 'false_positive' })}
                          title="Mark as False Positive"
                          className="px-2 py-1 bg-ink-800 hover:bg-ink-700 text-rind-300 border border-rind-500/20 text-[9.5px] rounded font-semibold transition-colors"
                        >
                          FP
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => handleOpenMerkleProof(a.id)}
                      title="Inspect Deterministic Merkle Inclusion Proof"
                      className="px-2 py-1 bg-ink-800 hover:bg-ink-750 text-instrument-400 border border-instrument-400/30 text-[9.5px] rounded font-semibold transition-colors"
                    >
                      Proof
                    </button>
                    <button
                      onClick={() => handleOpenProvenance(a.id)}
                      title="Inspect AI Model & Rule Provenance"
                      className="px-2 py-1 bg-ink-800 hover:bg-ink-750 text-leaf-500 border border-leaf-500/30 text-[9.5px] rounded font-semibold transition-colors"
                    >
                      Prov
                    </button>
                    <button
                      onClick={() => openLightbox(a.id)}
                      className="px-2.5 py-1 bg-ink-800 border border-rind-500/20 hover:border-instrument-400 text-rind-300 hover:text-instrument-400 text-[10px] rounded font-medium transition-colors"
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

      {/* SHA-256 Hash-Chain Integrity & Blockchain Anchoring Modal (PRD v1.0) */}
      {showLedgerModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-ink-900 border border-rind-500/20 rounded-rad w-full max-w-[660px] max-h-[92vh] flex flex-col overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3.5 border-b border-rind-500/15 bg-ink-850 shrink-0">
              <div className="flex items-center gap-2.5">
                <div className={`w-7 h-7 rounded-rad3 flex items-center justify-center text-sm ${
                  ledgerResult?.intact ? 'bg-leaf-900 text-leaf-500 border border-leaf-500/30' : 'bg-melon-d text-melon-500 border border-melon-500/30'
                }`}>
                  <i className={`ti ${ledgerResult?.intact ? 'ti-shield-check' : 'ti-shield-alert'}`}></i>
                </div>
                <div>
                  <div className="text-sm font-bold font-display text-rind-100">Cryptographic Ledger Integrity & Blockchain Anchoring</div>
                  <div className="text-[10px] text-rind-500 font-mono">Local SHA-256 Hash-Chain + External Blockchain Commitment</div>
                </div>
              </div>
              <button
                onClick={() => setShowLedgerModal(false)}
                aria-label="Close ledger modal"
                className="text-rind-500 hover:text-rind-100 text-base p-1"
              >
                <i className="ti ti-x"></i>
              </button>
            </div>

            {/* Content (Scrollable) */}
            <div className="p-5 space-y-5 overflow-y-auto max-h-[calc(92vh-125px)]">
              {isVerifying ? (
                <div className="p-10 flex flex-col items-center justify-center gap-3">
                  <div className="w-8 h-8 border-2 border-instrument-400 border-t-transparent rounded-full animate-spin"></div>
                  <div className="text-xs text-rind-300 font-medium">Walking SHA-256 hash-chain and querying blockchain commitments...</div>
                </div>
              ) : ledgerResult ? (
                <>
                  {/* Section 1: Local SHA-256 Hash-Chain */}
                  <div>
                    <div className="text-xs font-bold font-display text-rind-200 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                      <i className="ti ti-database text-instrument-400"></i>
                      Local SHA-256 Hash-Chain
                    </div>

                    {/* Status Banner */}
                    <div className={`p-3.5 rounded-rad border flex items-start gap-3 ${
                      ledgerResult.intact
                        ? 'bg-leaf-900/50 border-leaf-500/30 text-leaf-500'
                        : 'bg-melon-d border-melon-500/40 text-melon-500'
                    }`}>
                      <i className={`ti ${ledgerResult.intact ? 'ti-circle-check' : 'ti-alert-octagon'} text-xl shrink-0 mt-0.5`}></i>
                      <div>
                        <div className="text-xs font-bold tracking-wide font-display">
                          {ledgerResult.intact ? 'LOCAL LEDGER CHAIN VERIFIED INTACT' : 'CHAIN INTEGRITY COMPROMISED'}
                        </div>
                        <div className="text-[11px] mt-0.5 opacity-90">
                          {ledgerResult.message}
                        </div>
                      </div>
                    </div>

                    {/* Verification Stats */}
                    <div className="grid grid-cols-2 gap-2.5 mt-2.5">
                      <div className="bg-ink-800 p-3 rounded-rad border border-rind-500/15">
                        <div className="text-[10px] text-rind-500 font-mono uppercase">Verified Records</div>
                        <div className="text-lg font-bold text-rind-100 mt-0.5">{ledgerResult.checkedRecords}</div>
                      </div>
                      <div className="bg-ink-800 p-3 rounded-rad border border-rind-500/15">
                        <div className="text-[10px] text-rind-500 font-mono uppercase">Tamper Status</div>
                        <div className={`text-sm font-bold mt-1 ${ledgerResult.intact ? 'text-leaf-500' : 'text-melon-500'}`}>
                          {ledgerResult.intact ? '0 Tampered' : `Broken at seq #${ledgerResult.brokenAtSeq}`}
                        </div>
                      </div>
                    </div>

                    {/* Tamper Demo Action */}
                    <div className="bg-ink-800/70 p-3 rounded-rad border border-rind-500/15 mt-2.5">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-xs font-semibold text-rind-200">Forensic Tamper Detection Demo</div>
                          <div className="text-[10.5px] text-rind-500">Simulates an unauthorized SQL alteration bypassing the API.</div>
                        </div>
                        <button
                          onClick={handleTamperDemo}
                          disabled={tamperLoading || !isAdmin}
                          className={`px-3 py-1.5 text-xs font-bold rounded-rad3 transition-colors shrink-0 ${
                            isAdmin
                              ? 'bg-melon-d text-melon-500 border border-melon-500/30 hover:bg-melon-500/20'
                              : 'bg-ink-850 text-rind-500 border border-rind-500/10 cursor-not-allowed opacity-50'
                          }`}
                        >
                          {tamperLoading ? 'Injecting...' : 'Simulate Tamper (Admin)'}
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Section 2: External Blockchain Anchoring & Multisignature Anchoring (PRD v1.0) */}
                  <div className="pt-2 border-t border-rind-500/15">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setActiveLedgerTab('anchors')}
                          className={`px-3 py-1 text-xs font-bold font-display uppercase tracking-wider rounded-rad3 transition-colors flex items-center gap-1.5 ${
                            activeLedgerTab === 'anchors'
                              ? 'bg-instrument-400 text-ink-950'
                              : 'bg-ink-800 text-rind-400 hover:text-rind-200 border border-rind-500/15'
                          }`}
                        >
                          <i className="ti ti-link"></i>
                          Anchors ({anchors.length})
                        </button>
                        <button
                          onClick={() => setActiveLedgerTab('proposals')}
                          className={`px-3 py-1 text-xs font-bold font-display uppercase tracking-wider rounded-rad3 transition-colors flex items-center gap-1.5 ${
                            activeLedgerTab === 'proposals'
                              ? 'bg-instrument-400 text-ink-950'
                              : 'bg-ink-800 text-rind-400 hover:text-rind-200 border border-rind-500/15'
                          }`}
                        >
                          <i className="ti ti-shield-lock"></i>
                          Multisig Proposals ({proposals.length})
                        </button>
                      </div>
                    </div>

                    {activeLedgerTab === 'anchors' ? (
                      selectedAnchor ? (
                        <div className="space-y-3">
                          {/* Anchor Status & Network Bar */}
                          <div className="flex items-center justify-between bg-ink-800 p-2.5 rounded-rad border border-rind-500/15">
                            <div className="flex items-center gap-2">
                              <span className={`px-2 py-0.5 rounded text-[10.5px] font-bold uppercase tracking-wider flex items-center gap-1 border ${
                                selectedAnchor.status === 'confirmed'
                                  ? 'bg-leaf-900/60 text-leaf-500 border-leaf-500/30'
                                  : selectedAnchor.status === 'submitted'
                                  ? 'bg-cyan-950/60 text-cyan-400 border-cyan-500/30'
                                  : selectedAnchor.status === 'failed' || selectedAnchor.status === 'verification_failed'
                                  ? 'bg-melon-d text-melon-500 border-melon-500/30'
                                  : 'bg-amber-950/60 text-amber-400 border-amber-500/30'
                              }`}>
                                <i className={`ti ${
                                  selectedAnchor.status === 'confirmed' ? 'ti-circle-check' :
                                  selectedAnchor.status === 'submitted' ? 'ti-clock' :
                                  selectedAnchor.status === 'failed' ? 'ti-alert-triangle' : 'ti-loader'
                                }`}></i>
                                {selectedAnchor.status === 'confirmed' ? 'Confirmed On-Chain' : selectedAnchor.status}
                              </span>
                              <span className="text-xs font-bold text-rind-200 font-mono">{selectedAnchor.id}</span>
                            </div>

                            <div className="text-[10.5px] font-mono text-rind-400">
                              {selectedAnchor.network} (Chain ID: {selectedAnchor.chainId})
                            </div>
                          </div>

                          {/* Anchor Detail Grid */}
                          <div className="bg-ink-850 p-3 rounded-rad border border-rind-500/15 space-y-2 text-xs">
                            <div className="grid grid-cols-2 gap-2">
                              <div>
                                <span className="text-[10px] text-rind-500 uppercase font-mono block">Anchored Range</span>
                                <span className="font-semibold text-rind-200">
                                  Seq #{selectedAnchor.fromSequence} → #{selectedAnchor.throughSequence}
                                </span>
                              </div>
                              <div>
                                <span className="text-[10px] text-rind-500 uppercase font-mono block">Confirmations</span>
                                <span className="font-semibold text-rind-200">
                                  {selectedAnchor.confirmations} confs (Block #{selectedAnchor.blockNumber || 'Pending'})
                                </span>
                              </div>
                            </div>

                            {/* Merkle Root Hash with 1-click Copy */}
                            <div>
                              <div className="flex items-center justify-between text-[10px] text-rind-500 uppercase font-mono mb-1">
                                <span>Deterministic Merkle Root Hash</span>
                                {copiedHash && <span className="text-leaf-500 font-sans font-semibold">Copied to clipboard!</span>}
                              </div>
                              <div className="flex items-center gap-1.5 bg-ink-950 px-2 py-1.5 rounded border border-rind-500/20 font-mono text-[11px] text-rind-200">
                                <span className="truncate flex-1">{selectedAnchor.rootHash}</span>
                                <button
                                  onClick={() => handleCopyHash(selectedAnchor.rootHash)}
                                  className="text-rind-400 hover:text-rind-100 p-0.5 shrink-0 transition-colors"
                                  title="Copy 64-character SHA-256 root hash"
                                >
                                  <i className={`ti ${copiedHash ? 'ti-check text-leaf-500' : 'ti-copy'}`}></i>
                                </button>
                              </div>
                            </div>

                            {/* Transaction Hash & Explorer Link */}
                            <div className="flex items-center justify-between pt-1 border-t border-rind-500/10 text-[11px]">
                              <span className="text-rind-500">Tx Hash:</span>
                              {selectedAnchor.explorerUrl ? (
                                <a
                                  href={selectedAnchor.explorerUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="text-instrument-400 hover:underline flex items-center gap-1 font-mono truncate max-w-[280px]"
                                >
                                  {selectedAnchor.transactionHash?.slice(0, 18)}...
                                  <i className="ti ti-external-link text-[10px]"></i>
                                </a>
                              ) : (
                                <span className="font-mono text-rind-400 truncate max-w-[280px]">
                                  {selectedAnchor.transactionHash || 'Pending transaction broadcast'}
                                </span>
                              )}
                            </div>
                          </div>

                          {/* Live Verification Result Banner */}
                          {anchorVerifyResult && (
                            <div className={`p-3 rounded-rad border flex items-start gap-2.5 text-xs ${
                              anchorVerifyResult.verified
                                ? 'bg-leaf-900/40 border-leaf-500/30 text-leaf-500'
                                : 'bg-melon-d border-melon-500/40 text-melon-500'
                            }`}>
                              <i className={`ti ${anchorVerifyResult.verified ? 'ti-shield-check' : 'ti-shield-alert'} text-lg shrink-0 mt-0.5`}></i>
                              <div>
                                <div className="font-bold font-display">
                                  {anchorVerifyResult.verified
                                    ? 'ON-CHAIN COMMITMENT FULLY VERIFIED'
                                    : 'BLOCKCHAIN VERIFICATION ALERT'}
                                </div>
                                <div className="text-[11px] mt-0.5 opacity-90">{anchorVerifyResult.message}</div>
                                {anchorVerifyResult.onChainRootHash && (
                                  <div className="text-[10px] font-mono mt-1 opacity-80">
                                    Local: {anchorVerifyResult.localRootHash.slice(0, 16)}... | On-Chain: {anchorVerifyResult.onChainRootHash.slice(0, 16)}...
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Blockchain Action Bar */}
                          <div className="flex items-center justify-between gap-2 pt-1 flex-wrap">
                            <div className="flex items-center gap-2">
                              {isSupervisor && (
                                <button
                                  onClick={() => handleVerifyAnchor(selectedAnchor.id)}
                                  disabled={isAnchorVerifying}
                                  className="px-3 py-1.5 bg-instrument-400/10 hover:bg-instrument-400/20 text-instrument-400 border border-instrument-400/30 text-xs font-semibold rounded-rad3 flex items-center gap-1.5 transition-colors"
                                >
                                  <i className={`ti ${isAnchorVerifying ? 'ti-loader animate-spin' : 'ti-shield-check'}`}></i>
                                  {isAnchorVerifying ? 'Verifying On-Chain...' : 'Verify Anchor'}
                                </button>
                              )}

                              {isAdmin && selectedAnchor.status === 'failed' && (
                                <button
                                  onClick={() => handleRetryAnchor(selectedAnchor.id)}
                                  className="px-3 py-1.5 bg-amber-950/60 hover:bg-amber-950 text-amber-400 border border-amber-500/30 text-xs font-semibold rounded-rad3 flex items-center gap-1.5 transition-colors"
                                >
                                  <i className="ti ti-refresh"></i>
                                  Retry Anchor
                                </button>
                              )}
                            </div>

                            {isAdmin && !showAnchorForm && (
                              <button
                                onClick={() => setShowAnchorForm(true)}
                                className="px-3 py-1.5 bg-ink-800 hover:bg-ink-750 text-rind-200 border border-rind-500/20 text-xs font-semibold rounded-rad3 flex items-center gap-1.5 transition-colors"
                              >
                                <i className="ti ti-plus"></i>
                                Anchor Range...
                              </button>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="bg-ink-850 p-4 rounded-rad border border-rind-500/15 text-center">
                          <div className="text-xs text-rind-400 mb-2">No external blockchain anchors created for this site yet.</div>
                          {isAdmin ? (
                            <button
                              onClick={() => setShowAnchorForm(true)}
                              className="px-3.5 py-1.5 bg-instrument-400 text-ink-950 text-xs font-bold rounded-rad3 hover:bg-instrument-300 transition-colors inline-flex items-center gap-1.5"
                            >
                              <i className="ti ti-link"></i>
                              Anchor Initial Ledger Range
                            </button>
                          ) : (
                            <div className="text-[11px] text-rind-500">Administrator role required to create blockchain anchors.</div>
                          )}
                        </div>
                      )
                    ) : (
                      /* Multisig Proposals List View */
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="text-[11px] text-rind-400">
                            2-of-3 multisig policy: requires 2 distinct Admin/Supervisor signatures to commit.
                          </div>
                          {isAdmin && !showProposalForm && (
                            <button
                              onClick={() => setShowProposalForm(true)}
                              className="px-2.5 py-1 bg-instrument-400 text-ink-950 text-[11px] font-bold rounded-rad3 hover:bg-instrument-300 transition-colors flex items-center gap-1"
                            >
                              <i className="ti ti-plus"></i>
                              New Proposal
                            </button>
                          )}
                        </div>

                        {showProposalForm && isAdmin && (
                          <div className="bg-ink-800 p-3 rounded-rad border border-instrument-400/30 space-y-2.5">
                            <div className="text-xs font-bold text-rind-100 flex items-center justify-between">
                              <span>Create Multisig Anchor Proposal</span>
                              <button onClick={() => setShowProposalForm(false)} className="text-rind-500 hover:text-rind-200 text-xs">
                                Cancel
                              </button>
                            </div>
                            <div className="grid grid-cols-2 gap-2 text-xs">
                              <div>
                                <label className="text-[10px] text-rind-500 block mb-1">From Sequence #</label>
                                <input
                                  type="number"
                                  min="0"
                                  value={proposalFromSeq}
                                  onChange={(e) => setProposalFromSeq(parseInt(e.target.value) || 0)}
                                  className="w-full bg-ink-900 border border-rind-500/20 rounded px-2 py-1 text-rind-100 font-mono text-xs focus:outline-none focus:border-instrument-400"
                                />
                              </div>
                              <div>
                                <label className="text-[10px] text-rind-500 block mb-1">Through Sequence #</label>
                                <input
                                  type="number"
                                  min={proposalFromSeq}
                                  value={proposalThroughSeq}
                                  onChange={(e) => setProposalThroughSeq(parseInt(e.target.value) || 0)}
                                  className="w-full bg-ink-900 border border-rind-500/20 rounded px-2 py-1 text-rind-100 font-mono text-xs focus:outline-none focus:border-instrument-400"
                                />
                              </div>
                            </div>
                            <button
                              onClick={handleCreateProposal}
                              disabled={isCreatingProposal}
                              className="w-full py-1.5 bg-instrument-400 hover:bg-instrument-300 text-ink-950 text-xs font-bold rounded-rad3 transition-colors flex items-center justify-center gap-1"
                            >
                              <i className={`ti ${isCreatingProposal ? 'ti-loader animate-spin' : 'ti-shield-plus'}`}></i>
                              {isCreatingProposal ? 'Creating...' : 'Initialize Proposal (Admin)'}
                            </button>
                          </div>
                        )}

                        {isProposalsLoading ? (
                          <div className="p-6 text-center text-xs text-rind-400">Loading proposals...</div>
                        ) : proposals.length === 0 ? (
                          <div className="bg-ink-850 p-4 rounded-rad border border-rind-500/15 text-center text-xs text-rind-400">
                            No multisig proposals created yet.
                          </div>
                        ) : (
                          proposals.map((p) => (
                            <div key={p.id} className="bg-ink-850 p-3 rounded-rad border border-rind-500/15 space-y-2 text-xs">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                                    p.status === 'confirmed' ? 'bg-leaf-900/60 text-leaf-500 border-leaf-500/30' :
                                    p.status === 'submitted' ? 'bg-cyan-950/60 text-cyan-400 border-cyan-500/30' :
                                    p.status === 'approved' ? 'bg-leaf-900 text-leaf-500 border-leaf-500/30' :
                                    p.status === 'rejected' ? 'bg-melon-d text-melon-500 border-melon-500/30' :
                                    'bg-amber-950/60 text-amber-400 border-amber-500/30'
                                  }`}>
                                    {p.status}
                                  </span>
                                  <span className="font-mono text-rind-200 font-bold">{p.id}</span>
                                </div>
                                <span className="font-mono text-[11px] text-rind-400">
                                  Seq #{p.fromSequence} → #{p.throughSequence}
                                </span>
                              </div>

                              <div className="bg-ink-900 p-2 rounded border border-rind-500/15 font-mono text-[10.5px] space-y-1">
                                <div className="text-rind-500 truncate">Root: <span className="text-rind-200">{p.merkleRoot}</span></div>
                                <div className="text-rind-500 truncate">Prov Root: <span className="text-leaf-400">{p.provenanceRoot}</span></div>
                                <div className="text-rind-400 text-[10px] pt-1 border-t border-rind-500/10 flex justify-between">
                                  <span>Signatures: {p.signaturesCount} / {p.thresholdRequired} required</span>
                                  {p.signatures.length > 0 && (
                                    <span className="text-rind-500">Signers: {p.signatures.map(s => s.signerRole).join(', ')}</span>
                                  )}
                                </div>
                              </div>

                              {p.signatures.some(s => s.status === 'rejected' && s.reason) && (
                                <div className="text-[11px] text-melon-500 bg-melon-d/20 p-2 rounded border border-melon-500/20">
                                  Rejection Reason: {p.signatures.find(s => s.status === 'rejected' && s.reason)?.reason}
                                </div>
                              )}

                              {/* Proposal Action Buttons */}
                              <div className="flex items-center gap-2 pt-1">
                                {isSupervisor && (p.status === 'proposed' || p.status === 'partially_signed') && (
                                  <>
                                    <button
                                      onClick={() => handleSignProposal(p.id)}
                                      className="px-2.5 py-1 bg-leaf-900 hover:bg-leaf-900/80 text-leaf-500 border border-leaf-500/30 text-[11px] rounded font-semibold transition-colors flex items-center gap-1"
                                    >
                                      <i className="ti ti-writing-sign"></i>
                                      Sign (2-of-3)
                                    </button>
                                    <button
                                      onClick={() => setRejectingProposalId(p.id)}
                                      className="px-2.5 py-1 bg-melon-d hover:bg-melon-500/20 text-melon-500 border border-melon-500/30 text-[11px] rounded font-semibold transition-colors"
                                    >
                                      Reject...
                                    </button>
                                  </>
                                )}

                                {isAdmin && p.status === 'approved' && (
                                  <button
                                    onClick={() => handleSubmitProposal(p.id)}
                                    className="px-3 py-1 bg-cyan-600 hover:bg-cyan-500 text-ink-950 text-[11px] rounded font-bold transition-colors flex items-center gap-1"
                                  >
                                    <i className="ti ti-arrow-up-circle"></i>
                                    Submit to Blockchain
                                  </button>
                                )}

                                {p.status === 'submitted' && (
                                  <span className="text-[10.5px] text-cyan-400 font-mono">
                                    Submitted (Tx: {p.transactionHash?.slice(0, 14)}...)
                                  </span>
                                )}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    )}

                    {/* Admin Sequence Range Creation Form */}
                    {activeLedgerTab === 'anchors' && showAnchorForm && isAdmin && (
                      <div className="bg-ink-800 p-3.5 rounded-rad border border-instrument-400/30 mt-3 space-y-3">
                        <div className="text-xs font-bold text-rind-100 flex items-center justify-between">
                          <span>Submit Ledger Range to Blockchain</span>
                          <button
                            onClick={() => setShowAnchorForm(false)}
                            className="text-rind-500 hover:text-rind-200 text-xs"
                          >
                            Cancel
                          </button>
                        </div>
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div>
                            <label className="text-[10.5px] text-rind-500 block mb-1">From Sequence #</label>
                            <input
                              type="number"
                              min="0"
                              value={anchorFromSeq}
                              onChange={(e) => setAnchorFromSeq(parseInt(e.target.value) || 0)}
                              className="w-full bg-ink-900 border border-rind-500/20 rounded px-2.5 py-1 text-rind-100 font-mono text-xs focus:outline-none focus:border-instrument-400"
                            />
                          </div>
                          <div>
                            <label className="text-[10.5px] text-rind-500 block mb-1">Through Sequence #</label>
                            <input
                              type="number"
                              min={anchorFromSeq}
                              value={anchorThroughSeq}
                              onChange={(e) => setAnchorThroughSeq(parseInt(e.target.value) || 0)}
                              className="w-full bg-ink-900 border border-rind-500/20 rounded px-2.5 py-1 text-rind-100 font-mono text-xs focus:outline-none focus:border-instrument-400"
                            />
                          </div>
                        </div>
                        <div className="text-[10.5px] text-rind-500">
                          Deterministic Merkle root will be calculated locally and anchored to the configured provider without publishing alert details or coordinates.
                        </div>
                        <button
                          onClick={handleCreateAnchor}
                          disabled={isAnchoring}
                          className="w-full py-1.5 bg-instrument-400 hover:bg-instrument-300 text-ink-950 text-xs font-bold rounded-rad3 transition-colors flex items-center justify-center gap-1.5"
                        >
                          <i className={`ti ${isAnchoring ? 'ti-loader animate-spin' : 'ti-link'}`}></i>
                          {isAnchoring ? 'Calculating Root & Submitting...' : 'Commit Root to Blockchain'}
                        </button>
                      </div>
                    )}
                  </div>
                </>
              ) : null}
            </div>

            {/* Footer */}
            <div className="px-4 py-3 bg-ink-850 border-t border-rind-500/15 flex justify-end shrink-0">
              <button
                onClick={() => setShowLedgerModal(false)}
                className="px-3.5 py-1.5 bg-ink-800 border border-rind-500/20 hover:border-rind-500/40 text-rind-200 text-xs font-semibold rounded-rad3 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Reason Prompt Modal for Operator Triage Action */}
      <ReasonPromptModal
        isOpen={Boolean(promptTarget)}
        title={promptTarget?.targetState === 'false_positive' ? 'Mark Alert as False Positive' : 'Resolve Security Incident'}
        subtitle={`Alert ID: ${promptTarget?.id}`}
        isFalsePositive={promptTarget?.targetState === 'false_positive'}
        submitLabel={promptTarget?.targetState === 'false_positive' ? 'Confirm False Positive' : 'Confirm Resolution'}
        onSubmit={handleReasonSubmit}
        onCancel={() => setPromptTarget(null)}
      />
      {/* Merkle Proof Inspection Modal (FR-MP-2) */}
      {proofTargetAlertId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-ink-900 border border-rind-500/20 rounded-rad w-full max-w-[640px] max-h-[90vh] flex flex-col overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
            <div className="flex items-center justify-between px-4 py-3.5 border-b border-rind-500/15 bg-ink-850 shrink-0">
              <div className="flex items-center gap-2">
                <i className="ti ti-binary-tree text-instrument-400 text-lg"></i>
                <div>
                  <div className="text-sm font-bold font-display text-rind-100">Merkle Tree Inclusion Proof</div>
                  <div className="text-[10.5px] text-rind-500 font-mono">Single-Alert Verification Without Full-Ledger Scan</div>
                </div>
              </div>
              <button
                onClick={() => { setProofTargetAlertId(null); setMerkleProof(null); setProofVerifyResult(null); }}
                className="text-rind-500 hover:text-rind-100 text-base p-1"
              >
                <i className="ti ti-x"></i>
              </button>
            </div>

            <div className="p-4 space-y-3.5 overflow-y-auto max-h-[calc(90vh-120px)] text-xs">
              {isProofLoading ? (
                <div className="p-8 flex flex-col items-center justify-center gap-2">
                  <div className="w-7 h-7 border-2 border-instrument-400 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-rind-400 text-xs font-medium">Constructing Merkle leaf & sibling path...</span>
                </div>
              ) : merkleProof ? (
                <>
                  <div className="bg-ink-850 p-3 rounded-rad border border-rind-500/15 space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-rind-500">Alert ID:</span>
                      <span className="text-instrument-400 font-bold">{merkleProof.alertId}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-rind-500">Ledger Sequence:</span>
                      <span className="text-rind-200">#{merkleProof.sequence}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-rind-500">Range:</span>
                      <span className="text-rind-200">Seq #{merkleProof.fromSequence} → #{merkleProof.throughSequence}</span>
                    </div>
                    <div>
                      <span className="text-rind-500 block mb-0.5">Leaf Hash (Canonical SHA-256):</span>
                      <div className="bg-ink-950 p-1.5 rounded border border-rind-500/20 text-instrument-400 text-[10.5px] truncate">
                        {merkleProof.leafHash}
                      </div>
                    </div>
                    <div>
                      <span className="text-rind-500 block mb-0.5">Expected Merkle Root:</span>
                      <div className="bg-ink-950 p-1.5 rounded border border-rind-500/20 text-rind-200 text-[10.5px] truncate">
                        {merkleProof.rootHash}
                      </div>
                    </div>
                  </div>

                  {/* Sibling Path */}
                  <div className="bg-ink-850 p-3 rounded-rad border border-rind-500/15 space-y-2">
                    <div className="flex items-center justify-between text-rind-200 font-semibold font-display text-xs">
                      <span>Cryptographic Sibling Path</span>
                      <span className="text-[10px] font-mono text-rind-500">{merkleProof.siblingHashes.length} Siblings</span>
                    </div>
                    {merkleProof.siblingHashes.length === 0 ? (
                      <div className="text-[11px] text-rind-500 italic">Single-leaf tree (leaf equals root).</div>
                    ) : (
                      <div className="space-y-1.5 max-h-[160px] overflow-y-auto">
                        {merkleProof.siblingHashes.map((sib, idx) => (
                          <div key={idx} className="flex items-center gap-2 bg-ink-950 p-1.5 rounded border border-rind-500/15 text-[10.5px] font-mono">
                            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
                              merkleProof.positions[idx] === 'left' ? 'bg-cyan-950 text-cyan-400 border border-cyan-500/30' : 'bg-instrument-d text-instrument-400 border border-instrument-400/30'
                            }`}>
                              {merkleProof.positions[idx]}
                            </span>
                            <span className="text-rind-300 truncate flex-1">{sib}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Verification Banner */}
                  {proofVerifyResult && (
                    <div className={`p-3 rounded-rad border flex items-start gap-2.5 ${
                      proofVerifyResult.valid ? 'bg-leaf-900/50 border-leaf-500/30 text-leaf-500' : 'bg-melon-d border-melon-500/40 text-melon-500'
                    }`}>
                      <i className={`ti ${proofVerifyResult.valid ? 'ti-circle-check' : 'ti-alert-octagon'} text-base shrink-0 mt-0.5`}></i>
                      <div>
                        <div className="font-bold">{proofVerifyResult.valid ? 'INCLUSION PROOF MATHEMATICALLY VERIFIED' : 'PROOF VERIFICATION FAILED'}</div>
                        <div className="text-[11px] mt-0.5 opacity-90">{proofVerifyResult.message}</div>
                        <div className="text-[10px] font-mono mt-1 opacity-80">
                          Computed: {proofVerifyResult.calculatedRootHash?.slice(0, 16)}... | Expected: {proofVerifyResult.rootHash?.slice(0, 16)}...
                        </div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="p-4 text-center text-rind-500 text-xs">No proof data available.</div>
              )}
            </div>

            <div className="px-4 py-3 bg-ink-850 border-t border-rind-500/15 flex items-center justify-between shrink-0">
              <button
                onClick={handleVerifyMerkleProof}
                disabled={!merkleProof || isProofVerifying}
                className="px-3.5 py-1.5 bg-instrument-400 hover:bg-instrument-300 text-ink-950 font-bold text-xs rounded-rad3 flex items-center gap-1.5 transition-colors"
              >
                <i className={`ti ${isProofVerifying ? 'ti-loader animate-spin' : 'ti-shield-check'}`}></i>
                {isProofVerifying ? 'Verifying Path...' : 'Verify Inclusion Proof'}
              </button>
              <button
                onClick={() => { setProofTargetAlertId(null); setMerkleProof(null); setProofVerifyResult(null); }}
                className="px-3.5 py-1.5 bg-ink-800 text-rind-200 border border-rind-500/20 text-xs rounded-rad3 hover:bg-ink-750"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Model Provenance Modal (FR-MP-5) */}
      {provTargetAlertId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-ink-900 border border-rind-500/20 rounded-rad w-full max-w-[600px] max-h-[90vh] flex flex-col overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
            <div className="flex items-center justify-between px-4 py-3.5 border-b border-rind-500/15 bg-ink-850 shrink-0">
              <div className="flex items-center gap-2">
                <i className="ti ti-cpu text-leaf-500 text-lg"></i>
                <div>
                  <div className="text-sm font-bold font-display text-rind-100">AI Model & Rule Provenance</div>
                  <div className="text-[10.5px] text-rind-500 font-mono">Alert ID: {provTargetAlertId}</div>
                </div>
              </div>
              <button
                onClick={() => { setProvTargetAlertId(null); setAlertProvenance(null); setProvVerifyResult(null); }}
                className="text-rind-500 hover:text-rind-100 text-base p-1"
              >
                <i className="ti ti-x"></i>
              </button>
            </div>

            <div className="p-4 space-y-3.5 overflow-y-auto max-h-[calc(90vh-120px)] text-xs">
              {isProvLoading ? (
                <div className="p-8 flex flex-col items-center justify-center gap-2">
                  <div className="w-7 h-7 border-2 border-leaf-500 border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-rind-400 text-xs font-medium">Retrieving registered model weights & hashes...</span>
                </div>
              ) : alertProvenance ? (
                <>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${
                      alertProvenance.provenance === 'detector' ? 'bg-leaf-900 text-leaf-500 border-leaf-500/30' : 'bg-ink-800 text-rind-400 border-rind-500/20'
                    }`}>
                      {alertProvenance.provenance.toUpperCase()}
                    </span>
                    {alertProvenance.provenance === 'simulation' && (
                      <span className="text-[11px] text-amber-400">
                        Explicit simulation provenance enforced (synthetic artifact).
                      </span>
                    )}
                  </div>

                  <div className="bg-ink-850 p-3 rounded-rad border border-rind-500/15 space-y-2 font-mono text-[11px]">
                    <div className="flex justify-between">
                      <span className="text-rind-500">Model Name:</span>
                      <span className="text-rind-200 font-semibold">{alertProvenance.modelName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-rind-500">Model Version:</span>
                      <span className="text-rind-200">{alertProvenance.modelVersion}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-rind-500">Runtime Version:</span>
                      <span className="text-rind-200">{alertProvenance.runtimeVersion}</span>
                    </div>
                    <div>
                      <span className="text-rind-500 block mb-0.5">Model Artifact SHA-256:</span>
                      <div className="bg-ink-950 p-1.5 rounded border border-rind-500/20 text-rind-200 text-[10.5px] truncate">
                        {alertProvenance.modelArtifactHash}
                      </div>
                    </div>
                    <div>
                      <span className="text-rind-500 block mb-0.5">Rule Config SHA-256:</span>
                      <div className="bg-ink-950 p-1.5 rounded border border-rind-500/20 text-rind-200 text-[10.5px] truncate">
                        {alertProvenance.ruleConfigHash}
                      </div>
                    </div>
                    <div>
                      <span className="text-rind-500 block mb-0.5">Canonical Provenance Hash:</span>
                      <div className="bg-ink-950 p-1.5 rounded border border-rind-500/20 text-leaf-400 text-[10.5px] truncate font-bold">
                        {alertProvenance.provenanceHash}
                      </div>
                    </div>
                  </div>

                  {provVerifyResult && (
                    <div className={`p-3 rounded-rad border flex items-start gap-2.5 ${
                      provVerifyResult.matches ? 'bg-leaf-900/50 border-leaf-500/30 text-leaf-500' : 'bg-melon-d border-melon-500/40 text-melon-500'
                    }`}>
                      <i className={`ti ${provVerifyResult.matches ? 'ti-circle-check' : 'ti-alert-octagon'} text-base shrink-0 mt-0.5`}></i>
                      <div>
                        <div className="font-bold">{provVerifyResult.matches ? 'PROVENANCE INTEGRITY VERIFIED' : 'PROVENANCE MISMATCH'}</div>
                        <div className="text-[11px] mt-0.5 opacity-90">{provVerifyResult.message}</div>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="p-4 text-center text-rind-500 text-xs">No provenance record found.</div>
              )}
            </div>

            <div className="px-4 py-3 bg-ink-850 border-t border-rind-500/15 flex items-center justify-between shrink-0">
              <button
                onClick={handleVerifyProvenance}
                disabled={!alertProvenance || isProvVerifying}
                className="px-3.5 py-1.5 bg-leaf-600 hover:bg-leaf-500 text-ink-950 font-bold text-xs rounded-rad3 flex items-center gap-1.5 transition-colors"
              >
                <i className={`ti ${isProvVerifying ? 'ti-loader animate-spin' : 'ti-shield-check'}`}></i>
                {isProvVerifying ? 'Verifying Hashes...' : 'Verify Provenance Integrity'}
              </button>
              <button
                onClick={() => { setProvTargetAlertId(null); setAlertProvenance(null); setProvVerifyResult(null); }}
                className="px-3.5 py-1.5 bg-ink-800 text-rind-200 border border-rind-500/20 text-xs rounded-rad3 hover:bg-ink-750"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Multisig Proposal Reason Prompt Modal */}
      {rejectingProposalId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
          <div className="bg-ink-900 border border-melon-500/30 rounded-rad w-full max-w-[460px] flex flex-col overflow-hidden shadow-[0_16px_50px_rgba(0,0,0,0.7)]">
            <div className="px-4 py-3 bg-ink-850 border-b border-rind-500/15 flex items-center justify-between">
              <div className="text-xs font-bold text-melon-500 flex items-center gap-1.5 font-display">
                <i className="ti ti-shield-x"></i>
                Reject Multisig Proposal
              </div>
              <button onClick={() => setRejectingProposalId(null)} className="text-rind-500 hover:text-rind-200 text-xs">
                <i className="ti ti-x"></i>
              </button>
            </div>
            <div className="p-4 space-y-3 text-xs">
              <div className="text-rind-300">
                Rejecting proposal <span className="font-mono font-bold text-rind-100">{rejectingProposalId}</span> will prevent it from reaching consensus. Please provide a forensic reason:
              </div>
              <textarea
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                placeholder="e.g. Ledger sequence range overlaps with unreviewed forensic incident..."
                rows={3}
                className="w-full bg-ink-950 border border-rind-500/20 rounded p-2 text-rind-100 text-xs focus:outline-none focus:border-melon-500"
              />
            </div>
            <div className="px-4 py-3 bg-ink-850 border-t border-rind-500/15 flex justify-end gap-2">
              <button
                onClick={() => setRejectingProposalId(null)}
                className="px-3 py-1.5 bg-ink-800 text-rind-300 text-xs rounded-rad3 hover:bg-ink-750"
              >
                Cancel
              </button>
              <button
                onClick={handleRejectProposal}
                disabled={!rejectionReason.trim()}
                className="px-3.5 py-1.5 bg-melon-d text-melon-500 border border-melon-500/30 hover:bg-melon-500/20 text-xs font-bold rounded-rad3 transition-colors disabled:opacity-50"
              >
                Confirm Rejection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

