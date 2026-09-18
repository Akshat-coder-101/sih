export type AlertType = 'intrusion' | 'watchlist' | 'anpr' | 'loiter' | 'night' | 'weapon';
export type AlertSeverity = 'high' | 'med' | 'low';
export type AlertState = 'open' | 'acknowledged' | 'resolved' | 'false_positive';
export type AlertProvenance = 'detector' | 'simulation';
export type PageId = 'monitor' | 'camgrid' | 'alerts' | 'analytics' | 'models' | 'cam-config' | 'fence-config' | 'contact' | 'privacy' | 'terms' | 'not-found';

export type CameraSourceType = 'rtsp' | 'webcam' | 'file' | 'simulation';

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
  sourceType?: CameraSourceType;
  supportsWebcam?: boolean;
  activeModelVersion?: string;
  activeRuleVersion?: string;
  siteId?: string;
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
  state: AlertState;
  provenance: AlertProvenance;
  ruleId?: string;
  ruleVersion?: string;
  sourceFrameTime?: Date | string;
  assignedTo?: string | null;
  resolutionNote?: string | null;
  resolvedAt?: Date | string | null;
  evidenceHash?: string | null;
  ts: Date;
  snapshot?: string | null;
}

export interface FenceRule {
  id: string;
  cameraId: string;
  name: string;
  ruleType: 'tripwire' | 'polygon_zone' | 'loiter_zone';
  direction: 'bidirectional' | 'left_to_right' | 'right_to_left' | 'entry' | 'exit';
  coordinates: number[][];
  targetClasses: string[];
  severity: AlertSeverity;
  enabled: boolean;
  cooldownSeconds: number;
  createdAt?: string;
  updatedAt?: string;
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
