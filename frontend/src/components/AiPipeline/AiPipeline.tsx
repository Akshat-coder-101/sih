import React from 'react';
import { useApp } from '../../context/AppContext';

export const AiPipeline: React.FC = () => {
  const { webcamActive, metrics, cams, telemetryFreshness } = useApp();

  const positiveLatencies = metrics
    ? Object.values(metrics.cameraTelemetry)
        .map(t => t.inferenceLatencyMs)
        .filter((lat): lat is number => typeof lat === 'number' && lat > 0)
    : [];

  const averageLatency = positiveLatencies.length > 0
    ? Math.round(positiveLatencies.reduce((a, b) => a + b, 0) / positiveLatencies.length)
    : null;

  const totalWorkerFps = metrics
    ? Object.values(metrics.cameraTelemetry).reduce((sum, item) => sum + (item.fps || 0), 0)
    : 0;
  const metadataFps = cams.reduce((sum, cam) => sum + (cam.online ? cam.fps : 0), 0);
  const activeFps = metrics ? totalWorkerFps : metadataFps;

  const stage1Prov = telemetryFreshness === 'stale'
    ? 'Telemetry Stale'
    : telemetryFreshness === 'unavailable'
    ? 'Telemetry Unavailable'
    : (averageLatency !== null && averageLatency > 0)
    ? 'Live Telemetry'
    : metrics
    ? 'Telemetry Idle'
    : webcamActive
    ? 'Browser WebGL'
    : 'Metadata Fallback';

  const stage1Fps = metrics
    ? `${activeFps} fps (Worker telemetry)`
    : webcamActive
    ? 'Variable (Browser MediaStream)'
    : `${metadataFps} fps (Camera metadata)`;

  const models = [
    {
      stage: 'Stage 1 · Edge Core',
      name: 'YOLOv8n / TensorFlow.js COCO-SSD',
      desc: 'Real-time human, weapon, and vehicle detector running continuous inference on frame streams',
      icon: 'ti-scan',
      lat: averageLatency === null ? 'n/a' : `${averageLatency}ms`,
      fps: stage1Fps,
      active: true,
      prov: stage1Prov
    },
    {
      stage: 'Stage 2 · Kinematics',
      name: 'ByteTrack Multi-Object Tracker',
      desc: 'Kalman filter bounding-box association — maintains consistent trajectory IDs across occlusions',
      icon: 'ti-route',
      lat: 'n/a',
      fps: metrics ? `${metrics.cameraWorkers} active worker(s)` : 'Telemetry unavailable',
      active: true,
      prov: metrics ? 'Active Tracking' : 'Metadata Fallback'
    },
    {
      stage: 'Stage 3a · Boundary Rules',
      name: 'Virtual Perimeter & Dwell Engine',
      desc: 'Polygon geometry line-crossing checks and dwell time analytics (4s+ stationary trigger)',
      icon: 'ti-fence',
      lat: 'n/a',
      fps: 'Continuous Rule Evaluation',
      active: true,
      prov: 'Deterministic Rule Engine'
    },
    {
      stage: 'Stage 3b · Biometrics (Planned)',
      name: 'RetinaFace + ArcFace Matcher',
      desc: 'Watchlist embedding matching triggered only when approved by sector governance policy',
      icon: 'ti-fingerprint',
      lat: 'n/a',
      fps: 'On-Demand Trigger',
      active: false,
      prov: 'Governance Gated'
    },
    {
      stage: 'Stage 3c · Checkpoint ANPR (Planned)',
      name: 'PaddleOCR / License Plate Localizer',
      desc: 'High-speed number plate localization & character recognition for approach road checkpoints',
      icon: 'ti-license',
      lat: 'n/a',
      fps: 'On-Demand Trigger',
      active: false,
      prov: 'Governance Gated'
    },
    {
      stage: 'Stage 3d · Low-Light Enhancement',
      name: 'Zero-DCE Low-Light Enhancer',
      desc: 'Zero-reference deep curve estimation for tactical low-light and infrared camera streams',
      icon: 'ti-moon',
      lat: 'n/a',
      fps: 'Night Sensor Active',
      active: false,
      prov: 'Hardware Mode'
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-lg md:text-xl font-bold font-display tracking-tight text-rind-100">AI Inference Pipeline Architecture</h1>
          <p className="text-xs text-rind-500 mt-0.5">Cascaded edge detection pipeline with on-demand forensic analysis and honest model provenance</p>
        </div>
      </div>

      <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5 divide-y divide-rind-500/10 shadow-sm">
        {models.map((m, idx) => (
          <div key={idx} className="flex items-center gap-3.5 py-4 first:pt-0 last:pb-0 flex-wrap sm:flex-nowrap">
            <div className={`w-11 h-11 rounded-rad3 shrink-0 flex items-center justify-center text-xl border ${
              m.active ? 'bg-instrument-d text-instrument-400 border-instrument-400/30 shadow-[0_0_12px_rgba(86,199,217,0.15)]' : 'bg-ink-800 text-rind-500 border-rind-500/15'
            }`}>
              <i className={`ti ${m.icon}`}></i>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5 flex-wrap">
                <div className="text-xs md:text-sm font-bold text-rind-100 font-mono">{m.name}</div>
                {m.active ? (
                  <span className="text-[8.5px] font-bold uppercase tracking-wider bg-leaf-900 text-leaf-500 border border-leaf-500/30 px-1.5 py-0.5 rounded-full">
                    Production Active
                  </span>
                ) : (
                  <span className="text-[8.5px] font-bold uppercase tracking-wider bg-ink-800 text-rind-500 border border-rind-500/20 px-1.5 py-0.5 rounded-full">
                    Stage Planned
                  </span>
                )}
              </div>
              <div className="text-xs text-rind-500 leading-relaxed">{m.desc}</div>
              <div className="flex gap-4 mt-1.5 flex-wrap">
                <span className="text-[10.5px] text-rind-500">Latency: <strong className="text-instrument-400 font-mono">{m.lat}</strong></span>
                <span className="text-[10.5px] text-rind-500">Throughput: <strong className="text-instrument-400 font-mono">{m.fps}</strong></span>
                <span className="text-[10.5px] text-rind-600 font-mono">({m.prov})</span>
              </div>
            </div>

            <div className="text-[9px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full bg-ink-800 text-rind-500 border border-rind-500/15 shrink-0 self-start sm:self-center">
              {m.stage}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

