import React from 'react';

export const About: React.FC = () => {
  const team = [
    { role: 'Team Lead', name: 'Ayush Kumar', detail: 'System Architecture & Integration' },
    { role: 'AI / CV Engineer', name: 'Abhishek Kumar', detail: 'Object Detection & Edge Optimization' },
    { role: 'Backend Engineer', name: 'Amit Singh', detail: 'FastAPI, TimescaleDB & WebSockets' },
    { role: 'Frontend Engineer', name: 'Rohan Sharma', detail: 'Command Center & Tactical UI/UX' },
  ];

  const techStack = [
    { name: 'React 18 + TypeScript', icon: 'ti-brand-react' },
    { name: 'TensorFlow.js + COCO-SSD', icon: 'ti-cpu' },
    { name: 'Tailwind CSS + DaisyUI', icon: 'ti-brand-tailwind' },
    { name: 'YOLOv8 Edge Detectors', icon: 'ti-scan' },
    { name: 'ByteTrack Tracker', icon: 'ti-route' },
    { name: 'RetinaFace + ArcFace', icon: 'ti-fingerprint' },
    { name: 'PaddleOCR (ANPR)', icon: 'ti-license' },
    { name: 'Zero-DCE (Low Light)', icon: 'ti-moon' },
    { name: 'FastAPI Backend', icon: 'ti-bolt' },
    { name: 'PostgreSQL + SQLite', icon: 'ti-database' },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6 bg-ink-950">
      {/* Hero Banner */}
      <div className="text-center py-8 md:py-10 px-4 bg-gradient-to-b from-ink-900 to-ink-950 border border-rind-500/15 rounded-rad mb-5 relative overflow-hidden shadow-sm">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_600px_300px_at_50%_0%,rgba(86,199,217,0.08),transparent)] pointer-events-none" />
        <div className="w-16 h-16 rounded-rad bg-gradient-to-br from-leaf-500 to-leaf-900 flex items-center justify-center mx-auto mb-3.5 shadow-[0_0_35px_rgba(101,214,139,0.3)] relative z-10">
          <i className="ti ti-shield-check text-3xl text-ink-950 font-bold"></i>
        </div>
        <h1 className="text-2xl md:text-3xl font-black font-display tracking-tight text-rind-100 mb-1 relative z-10">IBVAP</h1>
        <div className="text-xs text-rind-300 mb-3.5 relative z-10">Intelligent Border Video Analytics Platform &mdash; Watermelon Command</div>
        <div className="inline-block text-[10px] font-mono font-bold px-3 py-1 rounded-full bg-instrument-d text-instrument-400 border border-instrument-400/30 relative z-10">
          Pilot Release v1.0 &middot; Team PERCEPTRONS
        </div>
      </div>

      {/* Team Grid */}
      <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5 mb-4 shadow-sm">
        <div className="flex items-center gap-2.5 pb-3 mb-4 border-b border-rind-500/15">
          <div className="w-7 h-7 rounded-rad3 flex items-center justify-center bg-instrument-d text-instrument-400 text-sm">
            <i className="ti ti-users"></i>
          </div>
          <h2 className="text-xs font-bold font-display text-rind-100 flex-1">Engineering Team</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3.5">
          {team.map((m, idx) => (
            <div key={idx} className="bg-ink-850 border border-rind-500/10 rounded-rad p-4 text-center hover:-translate-y-0.5 transition-transform">
              <div className="w-12 h-12 rounded-full border-2 border-rind-500/20 flex items-center justify-center mx-auto mb-2.5 text-lg bg-instrument-d text-instrument-400">
                <i className="ti ti-user"></i>
              </div>
              <div className="text-[9px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full inline-block mb-1.5 bg-ink-800 text-rind-500 border border-rind-500/15">
                {m.role}
              </div>
              <div className="text-xs font-bold text-rind-100 mb-0.5">{m.name}</div>
              <div className="text-[10.5px] text-rind-500">{m.detail}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="bg-ink-900 border border-rind-500/15 rounded-rad p-4 md:p-5 shadow-sm">
        <div className="flex items-center gap-2.5 pb-3 mb-4 border-b border-rind-500/15">
          <div className="w-7 h-7 rounded-rad3 flex items-center justify-center bg-instrument-d text-instrument-400 text-sm">
            <i className="ti ti-stack-2"></i>
          </div>
          <h2 className="text-xs font-bold font-display text-rind-100 flex-1">Technology Architecture</h2>
        </div>

        <div className="flex flex-wrap gap-2">
          {techStack.map((tech, idx) => (
            <span key={idx} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-ink-850 border border-rind-500/15 text-xs text-rind-200">
              <i className={`ti ${tech.icon} text-xs text-instrument-400`}></i>
              {tech.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

