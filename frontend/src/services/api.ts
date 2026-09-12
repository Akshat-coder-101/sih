import { Camera, Alert, FenceRule, AlertState } from '../types';

const getHost = (): string => {
  if (typeof window !== 'undefined' && window.location && window.location.hostname) {
    return window.location.hostname;
  }
  return '127.0.0.1';
};

const API_BASE = (import.meta as any).env?.VITE_API_BASE || `http://${getHost()}:8000`;

export interface LedgerVerifyResponse {
  intact: boolean;
  checkedRecords: number;
  brokenAtSeq?: number | null;
  brokenAlertId?: string | null;
  message: string;
  blockchainAnchorsAvailable?: boolean;
  latestAnchorId?: string | null;
  latestAnchorStatus?: string | null;
  latestAnchorMatches?: boolean | null;
}

export interface LedgerAnchor {
  id: string;
  siteId: string;
  network: string;
  chainId: number;
  contractAddress: string;
  anchorId: string;
  fromSequence: number;
  throughSequence: number;
  rootHash: string;
  schemaVersion: number;
  transactionHash?: string | null;
  blockNumber?: number | null;
  confirmations: number;
  status: 'pending' | 'submitted' | 'confirmed' | 'failed' | 'verification_failed';
  attemptCount: number;
  nextRetryAt?: string | null;
  submittedAt?: string | null;
  confirmedAt?: string | null;
  lastVerifiedAt?: string | null;
  lastError?: string | null;
  explorerUrl?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface LedgerAnchorVerifyResult {
  anchorId: string;
  localLedgerIntact: boolean;
  localRootHash: string;
  onChainRootHash?: string | null;
  rootMatches: boolean;
  blockchainConfirmed: boolean;
  verified: boolean;
  message: string;
  brokenAtSeq?: number | null;
  status?: string | null;
}

export interface AnchorLedgerRequest {
  siteId?: string;
  fromSequence: number;
  throughSequence: number;
  force?: boolean;
}

export interface MerkleProof {
  alertId: string;
  sequence: number;
  leafHash: string;
  leafPayload: Record<string, any>;
  siblingHashes: string[];
  positions: string[];
  rootHash: string;
  schemaVersion: string;
  fromSequence: number;
  throughSequence: number;
}

export interface MerkleProofVerifyResult {
  valid: boolean;
  alertId: string;
  rootHash: string;
  calculatedRootHash: string;
  message: string;
}

export interface ModelProvenance {
  id: string;
  modelName: string;
  modelVersion: string;
  artifactHash: string;
  runtimeVersion: string;
  ruleVersion: string;
  ruleConfigHash: string;
  preprocessingConfigHash: string;
  provenanceHash: string;
  registeredBy: string;
  createdAt: string;
}

export interface AlertProvenance {
  alertId: string;
  provenance: string;
  modelName?: string | null;
  modelVersion?: string | null;
  modelArtifactHash?: string | null;
  runtimeVersion?: string | null;
  ruleVersion?: string | null;
  ruleConfigHash?: string | null;
  preprocessingConfigHash?: string | null;
  provenanceHash?: string | null;
  isValid: boolean;
}

export interface AlertProvenanceVerifyResult {
  alertId: string;
  provenance: string;
  storedHash?: string | null;
  recomputedHash?: string | null;
  matches: boolean;
  message: string;
}

export interface AnchorSignature {
  id: number;
  signerUserId: string;
  signerRole: string;
  signatureAlgorithm: string;
  publicKeyId: string;
  signature: string;
  payloadDigest: string;
  status: string;
  reason?: string | null;
  signedAt: string;
}

export interface AnchorProposal {
  id: string;
  siteId: string;
  fromSequence: number;
  throughSequence: number;
  merkleRoot: string;
  provenanceRoot: string;
  schemaVersion: string;
  status: 'proposed' | 'partially_signed' | 'approved' | 'submitted' | 'confirmed' | 'rejected' | 'expired' | 'failed';
  network: string;
  chainId: number;
  contractAddress: string;
  transactionHash?: string | null;
  blockNumber?: number | null;
  createdBy: string;
  createdAt: string;
  submittedAt?: string | null;
  confirmedAt?: string | null;
  expiresAt?: string | null;
  lastError?: string | null;
  signatures: AnchorSignature[];
  signaturesCount: number;
  thresholdRequired: number;
  thresholdMet: boolean;
  payloadDigest?: string | null;
}

export interface UserAuth {
  username: string;
  role: 'operator' | 'supervisor' | 'admin';
  accessToken: string;
}

export interface AuditLogEntry {
  id: number;
  username: string;
  action: string;
  detail?: string;
  ts: string;
}

export interface ReadinessResponse {
  ready: boolean;
  database: boolean;
  modelLoaded: boolean;
  cameraWorkers: number;
  activeStreams: string[];
  timestamp: string;
  statusCode?: number;
}

export interface MetricsResponse {
  timestamp: string;
  totalAlerts: number;
  activeWsClients: number;
  cameraWorkers: number;
  modelRegistry: Record<string, any>;
  cameraTelemetry: Record<string, {
    fps: number;
    processedFrames: number;
    inferenceLatencyMs: number;
    queue: Record<string, any>;
    lastError?: string | null;
  }>;
}

export interface TerrainEnrichment {
  id: string;
  alertId: string;
  siteId: string;
  latitude: number;
  longitude: number;
  elevationM: number;
  slopeDeg: number;
  landCover: string;
  nearestRoadDistanceM: number;
  waterProximityM: number;
  datasetSource: string;
  dataFreshness: string;
  isPartial: boolean;
  createdAt: string;
}

export interface TacticalRecommendation {
  id: string;
  alertId: string;
  siteId: string;
  status: 'draft' | 'reviewed' | 'approved' | 'rejected' | 'stale';
  actionSummary: string;
  tacticalActions: string[];
  contributingFactors: Record<string, any>;
  citations: string[];
  uncertaintyScore: number;
  reviewedBy?: string | null;
  reviewNotes?: string | null;
  reviewedAt?: string | null;
  createdAt: string;
}

export interface SingleFrameDetection {
  className: string;
  confidence: number;
  box: [number, number, number, number];
  normalizedBox: [number, number, number, number];
}

export interface SingleFrameAnalysis {
  camId: string;
  timestamp: number;
  detections: SingleFrameDetection[];
  numDetections: number;
  alertTriggered: boolean;
  alertId?: string | null;
  alertType?: string | null;
  processingTimeMs: number;
  detectorModel: string;
}

export const api = {
  getBaseUrl(): string {
    return API_BASE;
  },

  getStreamUrl(camId: string, token?: string): string {
    return token ? `${API_BASE}/cameras/${camId}/stream?token=${encodeURIComponent(token)}` : `${API_BASE}/cameras/${camId}/stream`;
  },

  getWsUrl(token?: string): string {
    const wsProto = (typeof window !== 'undefined' && window.location?.protocol === 'https:') ? 'wss:' : 'ws:';
    const host = getHost();
    const base = `${wsProto}//${host}:8000/ws/alerts`;
    return token ? `${base}?token=${encodeURIComponent(token)}` : base;
  },

  async login(username: string, password: string): Promise<UserAuth> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(err.detail || 'Invalid credentials');
    }
    const data = await res.json();
    return {
      username: data.username,
      role: data.role,
      accessToken: data.accessToken
    };
  },

  normalizeReadiness(data: any, statusCode?: number): ReadinessResponse {
    return {
      ready: Boolean(data?.ready),
      database: Boolean(data?.database),
      modelLoaded: Boolean(data?.modelLoaded ?? data?.model_loaded),
      cameraWorkers: Number(data?.cameraWorkers ?? data?.camera_workers ?? 0),
      activeStreams: Array.isArray(data?.activeStreams)
        ? data.activeStreams
        : Array.isArray(data?.active_streams)
        ? data.active_streams
        : [],
      timestamp: data?.timestamp || new Date().toISOString(),
      statusCode
    };
  },

  async getReadiness(): Promise<ReadinessResponse> {
    const res = await fetch(`${API_BASE}/ready`);
    let data: any = null;
    try {
      data = await res.json();
    } catch {
      if (!res.ok) {
        throw new Error(`Failed to fetch readiness status (HTTP ${res.status})`);
      }
      throw new Error('Readiness response was not valid JSON');
    }

    if (!data || typeof data !== 'object') {
      throw new Error('Invalid readiness payload received');
    }

    return this.normalizeReadiness(data, res.status);
  },

  normalizeMetrics(data: any): MetricsResponse {
    const telemetry = data.cameraTelemetry || data.camera_telemetry || data.workerTelemetry || data.worker_telemetry || {};
    const cameraTelemetry = Object.fromEntries(Object.entries(telemetry).map(([cameraId, item]: [string, any]) => [cameraId, {
      ...item,
      fps: Number(item.fps ?? 0),
      inferenceLatencyMs: Number(item.inferenceLatencyMs ?? item.inference_latency_ms ?? 0),
      processedFrames: Number(item.processedFrames ?? item.processed_frames ?? 0),
      queue: item.queue || {},
      lastError: item.lastError ?? item.last_error ?? null
    }]));
    return {
      ...data,
      cameraTelemetry,
      totalAlerts: Number(data.totalAlerts ?? data.total_alerts ?? 0),
      activeWsClients: Number(data.activeWsClients ?? data.active_ws_clients ?? 0),
      cameraWorkers: Number(data.cameraWorkers ?? data.camera_workers ?? 0),
      modelRegistry: data.modelRegistry || data.model_registry || {}
    };
  },

  async getMetrics(token?: string): Promise<MetricsResponse> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/metrics`, { headers });
    if (!res.ok) throw new Error('Failed to fetch live metrics');
    const data = await res.json();
    return this.normalizeMetrics(data);
  },

  async getCameras(token?: string): Promise<Camera[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/cameras`, { headers });
    if (!res.ok) throw new Error('Failed to fetch cameras');
    const items = await res.json();
    return items.map((c: any) => ({
      ...c,
      rtspUrl: c.rtspUrl || c.rtsp_url || '',
      sourceType: c.sourceType || c.source_type,
      supportsWebcam: c.supportsWebcam ?? c.supports_webcam,
      activeModelVersion: c.activeModelVersion || c.active_model_version || undefined,
      activeRuleVersion: c.activeRuleVersion || c.active_rule_version || undefined,
      siteId: c.siteId || c.site_id || undefined
    }));
  },

  async toggleCamera(camId: string, token?: string): Promise<Camera> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/cameras/${camId}/toggle`, {
      method: 'PATCH',
      headers
    });
    if (!res.ok) throw new Error('Failed to toggle camera (requires Admin)');
    const c = await res.json();
    return {
      ...c,
      rtspUrl: c.rtspUrl || c.rtsp_url || '',
      sourceType: c.sourceType || c.source_type,
      supportsWebcam: c.supportsWebcam ?? c.supports_webcam,
      activeModelVersion: c.activeModelVersion || c.active_model_version || undefined,
      activeRuleVersion: c.activeRuleVersion || c.active_rule_version || undefined,
      siteId: c.siteId || c.site_id
    };
  },

  async toggleNight(camId: string, token?: string): Promise<Camera> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/cameras/${camId}/night`, {
      method: 'PATCH',
      headers
    });
    if (!res.ok) throw new Error('Failed to toggle night mode');
    const c = await res.json();
    return {
      ...c,
      rtspUrl: c.rtspUrl || c.rtsp_url || '',
      sourceType: c.sourceType || c.source_type,
      supportsWebcam: c.supportsWebcam ?? c.supports_webcam,
      activeModelVersion: c.activeModelVersion || c.active_model_version || undefined,
      activeRuleVersion: c.activeRuleVersion || c.active_rule_version || undefined,
      siteId: c.siteId || c.site_id
    };
  },

  async getAlerts(
    filters?: {
      type?: string;
      sev?: string;
      camId?: string;
      reviewed?: boolean;
      state?: AlertState;
      provenance?: string;
    },
    token?: string
  ): Promise<Alert[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const params = new URLSearchParams();
    if (filters?.type) params.append('type', filters.type);
    if (filters?.sev) params.append('sev', filters.sev);
    if (filters?.camId) params.append('camId', filters.camId);
    if (filters?.reviewed !== undefined) params.append('reviewed', String(filters.reviewed));
    if (filters?.state) params.append('state', filters.state);
    if (filters?.provenance) params.append('provenance', filters.provenance);

    const url = `${API_BASE}/alerts${params.toString() ? '?' + params.toString() : ''}`;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error('Failed to fetch alerts');
    const items = await res.json();
    return items.map((a: any) => ({
      ...a,
      ts: new Date(a.ts)
    }));
  },

  async createAlert(alert: Partial<Alert>, token?: string): Promise<Alert> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const payload = {
      type: alert.type,
      camId: alert.camId,
      detail: alert.detail,
      confidence: alert.confidence,
      trackId: alert.trackId,
      snapshot: alert.snapshot,
      sev: alert.sev,
      provenance: alert.provenance || 'detector',
      ruleId: alert.ruleId
    };

    const res = await fetch(`${API_BASE}/alerts`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to save alert');
    const saved = await res.json();
    return {
      ...saved,
      ts: new Date(saved.ts)
    };
  },

  async updateAlert(
    alertId: string,
    patch: {
      state?: AlertState;
      reviewed?: boolean;
      assignedTo?: string;
      resolutionNote?: string;
    },
    token?: string
  ): Promise<Alert> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/alerts/${alertId}`, {
      method: 'PATCH',
      headers,
      body: JSON.stringify(patch)
    });
    if (!res.ok) throw new Error('Failed to update alert');
    const item = await res.json();
    return {
      ...item,
      ts: new Date(item.ts)
    };
  },

  async markReviewed(alertId: string, token?: string): Promise<Alert> {
    return this.updateAlert(alertId, { reviewed: true, state: 'acknowledged' }, token);
  },

  async getEvidence(alertId: string, token?: string): Promise<{ alertId: string; hasSnapshot: boolean; snapshot?: string }> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/alerts/${alertId}/evidence`, { headers });
    if (!res.ok) throw new Error('Failed to fetch alert evidence');
    return res.json();
  },

  async downloadAlertsCsv(token?: string): Promise<void> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/alerts/export.csv`, { headers });
    if (!res.ok) throw new Error('CSV Export requires Supervisor role');
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `ibvap_alerts_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
  },

  async getFenceRules(camId?: string, token?: string): Promise<FenceRule[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const url = camId ? `${API_BASE}/fence-rules?camId=${camId}` : `${API_BASE}/fence-rules`;
    const res = await fetch(url, { headers });
    if (!res.ok) throw new Error('Failed to fetch virtual fence rules');
    return res.json();
  },

  async createFenceRule(rule: Partial<FenceRule>, token?: string): Promise<FenceRule> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/fence-rules`, {
      method: 'POST',
      headers,
      body: JSON.stringify(rule)
    });
    if (!res.ok) throw new Error('Failed to create fence rule (requires Supervisor)');
    return res.json();
  },

  async deleteFenceRule(ruleId: string, token?: string): Promise<void> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/fence-rules/${ruleId}`, {
      method: 'DELETE',
      headers
    });
    if (!res.ok) throw new Error('Failed to delete fence rule');
  },

  async verifyLedger(token?: string): Promise<LedgerVerifyResponse> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/verify`, { headers });
    if (!res.ok) throw new Error('Failed to verify ledger integrity');
    return res.json();
  },

  async tamperDemo(alertId: string, token?: string): Promise<{ status: string; alertId: string }> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/tamper-demo/${alertId}`, {
      method: 'POST',
      headers
    });
    if (!res.ok) throw new Error('Tamper demo failed (requires Admin)');
    return res.json();
  },

  async anchorLedger(payload: AnchorLedgerRequest, token?: string): Promise<LedgerAnchor> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchor`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        siteId: payload.siteId || 'site-alpha',
        fromSequence: payload.fromSequence,
        throughSequence: payload.throughSequence,
        force: !!payload.force
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create ledger anchor' }));
      throw new Error(err.detail || 'Failed to create ledger anchor');
    }
    return res.json();
  },

  async getAnchors(siteId?: string, status?: string, token?: string): Promise<LedgerAnchor[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const params = new URLSearchParams();
    if (siteId) params.append('site_id', siteId);
    if (status) params.append('status', status);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/ledger/anchors${qs}`, { headers });
    if (!res.ok) throw new Error('Failed to fetch blockchain anchors');
    return res.json();
  },

  async getAnchor(anchorId: string, token?: string): Promise<LedgerAnchor> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/${anchorId}`, { headers });
    if (!res.ok) throw new Error(`Failed to fetch anchor ${anchorId}`);
    return res.json();
  },

  async verifyAnchor(anchorId: string, token?: string): Promise<LedgerAnchorVerifyResult> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/${anchorId}/verify`, {
      method: 'POST',
      headers
    });
    if (!res.ok) throw new Error(`Failed to verify anchor ${anchorId}`);
    return res.json();
  },

  async retryAnchor(anchorId: string, token?: string): Promise<LedgerAnchor> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/${anchorId}/retry`, {
      method: 'POST',
      headers
    });
    if (!res.ok) throw new Error(`Failed to retry anchor ${anchorId}`);
    return res.json();
  },

  async getAlertMerkleProof(alertId: string, token?: string): Promise<MerkleProof> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/alerts/${alertId}/merkle-proof`, { headers });
    if (!res.ok) throw new Error(`Failed to fetch Merkle proof for ${alertId}`);
    return res.json();
  },

  async verifyMerkleProof(proof: MerkleProof, token?: string): Promise<MerkleProofVerifyResult> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/proof/verify`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        alertId: proof.alertId,
        leafHash: proof.leafHash,
        siblingHashes: proof.siblingHashes,
        positions: proof.positions,
        rootHash: proof.rootHash,
        schemaVersion: proof.schemaVersion || 'merkle-v1'
      })
    });
    if (!res.ok) throw new Error('Failed to verify Merkle proof');
    return res.json();
  },

  async getModelProvenance(modelVersion: string, token?: string): Promise<ModelProvenance> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/models/${modelVersion}/provenance`, { headers });
    if (!res.ok) throw new Error(`Failed to fetch provenance for model ${modelVersion}`);
    return res.json();
  },

  async getAlertProvenance(alertId: string, token?: string): Promise<AlertProvenance> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/alerts/${alertId}/provenance`, { headers });
    if (!res.ok) throw new Error(`Failed to fetch provenance for alert ${alertId}`);
    return res.json();
  },

  async verifyAlertProvenance(alertId: string, token?: string): Promise<AlertProvenanceVerifyResult> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/alerts/${alertId}/provenance/verify`, {
      method: 'POST',
      headers
    });
    if (!res.ok) throw new Error(`Failed to verify provenance for alert ${alertId}`);
    return res.json();
  },

  async getAnchorProposals(siteId?: string, status?: string, token?: string): Promise<AnchorProposal[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const params = new URLSearchParams();
    if (siteId) params.append('site_id', siteId);
    if (status) params.append('status', status);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/ledger/anchors/proposals${qs}`, { headers });
    if (!res.ok) throw new Error('Failed to fetch anchor proposals');
    return res.json();
  },

  async createAnchorProposal(payload: { siteId?: string; fromSequence: number; throughSequence: number; expiresInHours?: number }, token?: string): Promise<AnchorProposal> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/proposals`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        siteId: payload.siteId || 'site-alpha',
        fromSequence: payload.fromSequence,
        throughSequence: payload.throughSequence,
        expiresInHours: payload.expiresInHours || 24
      })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to create proposal' }));
      throw new Error(err.detail || 'Failed to create proposal');
    }
    return res.json();
  },

  async signAnchorProposal(proposalId: string, reason?: string, token?: string): Promise<AnchorProposal> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/proposals/${proposalId}/sign`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ reason: reason || 'Approved cryptographic commitment' })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to sign proposal' }));
      throw new Error(err.detail || 'Failed to sign proposal');
    }
    return res.json();
  },

  async rejectAnchorProposal(proposalId: string, reason: string, token?: string): Promise<AnchorProposal> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/proposals/${proposalId}/reject`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ reason })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to reject proposal' }));
      throw new Error(err.detail || 'Failed to reject proposal');
    }
    return res.json();
  },

  async submitAnchorProposal(proposalId: string, token?: string): Promise<AnchorProposal> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/proposals/${proposalId}/submit`, {
      method: 'POST',
      headers
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Failed to submit proposal' }));
      throw new Error(err.detail || 'Failed to submit proposal');
    }
    return res.json();
  },

  async verifyAnchorProposal(proposalId: string, token?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/ledger/anchors/proposals/${proposalId}/verify`, {
      method: 'POST',
      headers
    });
    if (!res.ok) throw new Error('Failed to verify anchor proposal');
    return res.json();
  },

  async getAuditLog(token?: string): Promise<AuditLogEntry[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/audit-log`, { headers });
    if (!res.ok) throw new Error('Failed to fetch audit log (requires Supervisor)');
    return res.json();
  },

  getSingleFrameUrl(camId: string, token?: string): string {
    return token ? `${API_BASE}/cameras/${camId}/frame?token=${encodeURIComponent(token)}` : `${API_BASE}/cameras/${camId}/frame`;
  },

  async stepFrame(camId: string, token?: string): Promise<{ camId: string; frameIndex: number; hasDetections: boolean; detectionsCount: number }> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/cameras/${camId}/step-frame`, {
      method: 'POST',
      headers
    });
    if (!res.ok) throw new Error('Failed to step frame');
    return res.json();
  },

  async processSingleFrame(camId: string, file?: File, token?: string): Promise<SingleFrameAnalysis> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    let body: any = undefined;
    if (file) {
      const formData = new FormData();
      formData.append('file', file);
      body = formData;
    }

    const res = await fetch(`${API_BASE}/cameras/${camId}/process-frame`, {
      method: 'POST',
      headers,
      body
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Single frame processing failed' }));
      throw new Error(err.detail || 'Single frame processing failed');
    }
    return res.json();
  },

  async getAlertTerrain(alertId: string, token?: string): Promise<TerrainEnrichment> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/alerts/${alertId}/terrain`, { headers });
    if (!res.ok) throw new Error('Failed to fetch terrain enrichment');
    return res.json();
  },

  async getAlertRecommendation(alertId: string, token?: string): Promise<TacticalRecommendation> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/alerts/${alertId}/recommendation`, { headers });
    if (!res.ok) throw new Error('Failed to fetch tactical recommendation');
    return res.json();
  },

  async reviewRecommendation(recId: string, status: string, notes?: string, token?: string): Promise<TacticalRecommendation> {
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/recommendations/${recId}/review`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ status, reviewNotes: notes })
    });
    if (!res.ok) throw new Error('Failed to review tactical recommendation (requires Supervisor)');
    return res.json();
  },

  async getC2Deliveries(token?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/c2/deliveries`, { headers });
    if (!res.ok) throw new Error('Failed to fetch C2 deliveries');
    return res.json();
  },

  async retryC2Delivery(deliveryId: string, token?: string): Promise<any> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/api/c2/deliveries/${deliveryId}/retry`, {
      method: 'POST',
      headers
    });
    if (!res.ok) throw new Error('Failed to retry C2 delivery (requires Admin)');
    return res.json();
  }
};
