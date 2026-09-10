import { Camera, Alert } from '../types';

const API_BASE = 'http://127.0.0.1:8000';

export interface LedgerVerifyResponse {
  intact: boolean;
  checkedRecords: number;
  brokenAtSeq?: number | null;
  brokenAlertId?: string | null;
  message: string;
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

export const api = {
  getBaseUrl(): string {
    return API_BASE;
  },

  getStreamUrl(camId: string): string {
    return `${API_BASE}/cameras/${camId}/stream`;
  },

  getWsUrl(): string {
    return `ws://127.0.0.1:8000/ws/alerts`;
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

  async getCameras(token?: string): Promise<Camera[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/cameras`, { headers });
    if (!res.ok) throw new Error('Failed to fetch cameras');
    return res.json();
  },

  async toggleCamera(camId: string, token?: string): Promise<Camera> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/cameras/${camId}/toggle`, {
      method: 'PATCH',
      headers
    });
    if (!res.ok) throw new Error('Failed to toggle camera (requires Admin)');
    return res.json();
  },

  async toggleNight(camId: string, token?: string): Promise<Camera> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/cameras/${camId}/night`, {
      method: 'PATCH',
      headers
    });
    if (!res.ok) throw new Error('Failed to toggle night mode');
    return res.json();
  },

  async getAlerts(filters?: { type?: string; sev?: string; camId?: string; reviewed?: boolean }, token?: string): Promise<Alert[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const params = new URLSearchParams();
    if (filters?.type) params.append('type', filters.type);
    if (filters?.sev) params.append('sev', filters.sev);
    if (filters?.camId) params.append('camId', filters.camId);
    if (filters?.reviewed !== undefined) params.append('reviewed', String(filters.reviewed));

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
      sev: alert.sev
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

  async markReviewed(alertId: string, token?: string): Promise<Alert> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/alerts/${alertId}/reviewed`, {
      method: 'PATCH',
      headers
    });
    if (!res.ok) throw new Error('Failed to mark alert reviewed (requires Supervisor)');
    const item = await res.json();
    return {
      ...item,
      ts: new Date(item.ts)
    };
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

  async getAuditLog(token?: string): Promise<AuditLogEntry[]> {
    const headers: Record<string, string> = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${API_BASE}/audit-log`, { headers });
    if (!res.ok) throw new Error('Failed to fetch audit log (requires Supervisor)');
    return res.json();
  }
};
