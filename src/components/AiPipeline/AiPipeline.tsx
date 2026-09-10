import React from 'react';
import { useApp } from '../../context/AppContext';

export const AiPipeline: React.FC = () => {
  const { webcamActive } = useApp();

  const models = [
    {
      stage: 'Stage 1 (Active on CAM-01)',
      name: 'TensorFlow.js COCO-SSD / MobileNetV2',
      desc: 'Real-time human, weapon proxy & object detection running fully client-side on browser webcam frames',
      icon: 'ti-scan',
      lat: '~12ms',
      fps: webcamActive ? '30 fps (Webcam Live)' : 'Standby / Simulated',
      active: true
    },
    {
      stage: 'Stage 2',
      name: 'ByteTrack / DeepSORT Tracker',
      desc: 'Multi-object Kalman filter tracking — builds continuous tracklets and directional velocity vectors',
      icon: 'ti-route',
      lat: '~2ms',
      fps: 'CPU-light',
      active: true
    },
    {
      stage: 'Stage 3a',
      name: 'Virtual Boundary & Loitering Rules Engine',
      desc: 'Polygon geometry line-crossing checks and dwell time analytics (4s+ stationary trigger)',
      icon: 'ti-fence',
      lat: '<1ms',
      fps: 'Rule-based',
      active: true
    },
    {
      stage: 'Stage 3b',
      name: 'RetinaFace + ArcFace Matcher',
      desc: 'Forensic face detection & embedding matching against authorized watchlist — triggered on person detections',
      icon: 'ti-fingerprint',
      lat: '~18ms',
      fps: 'On-trigger',
      active: false
    },
    {
      stage: 'Stage 3c',
      name: 'PaddleOCR / ANPR Engine',
      desc: 'High-speed number plate localization & character recognition for approach road checkpoints',
      icon: 'ti-license',
      lat: '~22ms',
      fps: 'On-trigger',
      active: false
    },
    {
      stage: 'Stage 3d',
      name: 'Zero-DCE Low-Light Enhancer',
      desc: 'Zero-reference deep curve estimation for tactical low-light and infrared camera streams',
      icon: 'ti-moon',
      lat: '~5ms',
      fps: 'On low-light',
      active: false
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-[24px]">
      <div className="flex items-center justify-between mb-[22px]">
        <div>
          <div className="text-[18px] font-[800] tracking-[-0.4px] text-tx">AI Inference Pipeline</div>
          <div className="text-[11.5px] text-tx3 mt-[1px]">Cascaded AI pipeline — continuous edge detection with on-demand forensic models</div>
        </div>
      </div>

      <div className="bg-s2 border border-b1 rounded-rad p-[20px] divide-y divide-b1">
        {models.map((m, idx) => (
          <div key={idx} className="flex items-center gap-[16px] py-[18px] first:pt-0 last:pb-0">
            <div className={`w-[46px] h-[46px] rounded-[10px] shrink-0 flex items-center justify-center text-[22px] border ${
              m.active ? 'bg-cyan-d text-cyan border-cyan/25 shadow-[0_0_12px_rgba(0,229,184,0.15)]' : 'bg-s3 text-tx3 border-b1'
            }`}>
              <i className={`ti ${m.icon}`}></i>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-[8px] mb-[2px]">
                <div className="text-[13.5px] font-[700] text-tx font-mono">{m.name}</div>
                {m.active && (
                  <span className="text-[8.5px] font-bold uppercase tracking-wider bg-cyan-dd text-cyan border border-cyan/30 px-[6px] py-[1px] rounded-full">
                    Active
                  </span>
                )}
              </div>
              <div className="text-[11.5px] text-tx3">{m.desc}</div>
              <div className="flex gap-[16px] mt-[6px]">
                <span className="text-[10.5px] text-tx4">Latency: <strong className="text-cyan font-mono">{m.lat}</strong></span>
                <span className="text-[10.5px] text-tx4">Throughput: <strong className="text-cyan font-mono">{m.fps}</strong></span>
              </div>
            </div>

            <div className="text-[9px] font-[700] tracking-[0.5px] uppercase px-[10px] py-[3px] rounded-[20px] bg-s3 text-tx3 border border-b1 shrink-0">
              {m.stage}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
