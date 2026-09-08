export type AlertType = 'intrusion' | 'watchlist' | 'anpr' | 'loiter' | 'night' | 'weapon';
export type AlertSeverity = 'high' | 'med' | 'low';
export type PageId = 'monitor' | 'camgrid' | 'alerts' | 'analytics' | 'models' | 'cam-config' | 'about';

export interface Camera {
  id: string;
  name: string;
  location: string;
  online: boolean;
  priority: 'High' | 'Medium' | 'Low';
  fps: number;
  night: boolean;
  scene: 'fence' | 'gate' | 'night';
  geo: string;
  anchor: {
    left: number;
    top: number;
    w: number;
    h: number;
  };
  rtspUrl?: string;
}

export interface Alert {
  id: string;
  type: AlertType;
  sev: AlertSeverity;
  camId: string;
  camName: string;
  location: string;
  confidence: number;
  trackId: string;
  detail: string;
  reviewed: boolean;
  ts: Date;
  snapshot?: string | null;
}

export interface DetectionBox {
  left: number;
  top: number;
  w: number;
  h: number;
  label: string;
  watch?: boolean;
  score?: number;
  class?: string;
}

export interface TypeMeta {
  label: string;
  icon: string;
  cls: string;
  sev: AlertSeverity;
}
