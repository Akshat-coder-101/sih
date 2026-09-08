import React from 'react';

export const About: React.FC = () => {
  const team = [
    { role: 'Team Lead', name: 'Ayush Kumar', detail: 'System Architecture & Integration' },
    { role: 'AI / CV Engineer', name: 'Abhishek Kumar', detail: 'Object Detection & TensorRT Optimization' },
    { role: 'Backend Engineer', name: 'Amit Singh', detail: 'FastAPI, TimescaleDB & WebSockets' },
    { role: 'Frontend Engineer', name: 'Rohan Sharma', detail: 'React Command Center & Tactical UI' },
  ];

  const techStack = [
    { name: 'React + TypeScript', icon: 'ti-brand-react' },
    { name: 'TensorFlow.js COCO-SSD', icon: 'ti-cpu' },
    { name: 'Tailwind CSS + DaisyUI', icon: 'ti-brand-tailwind' },
    { name: 'YOLOv8 / YOLOv9', icon: 'ti-scan' },
    { name: 'ByteTrack / DeepSORT', icon: 'ti-route' },
    { name: 'RetinaFace + ArcFace', icon: 'ti-fingerprint' },
    { name: 'PaddleOCR (ANPR)', icon: 'ti-license' },
    { name: 'Zero-DCE (Low Light)', icon: 'ti-moon' },
    { name: 'FastAPI Backend', icon: 'ti-bolt' },
    { name: 'PostgreSQL + TimescaleDB', icon: 'ti-database' },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-[24px]">
      {/* Hero Banner */}
      <div className="text-center py-[40px] px-[20px] pb-[32px] bg-gradient-to-b from-s2 to-s1 border border-b1 rounded-rad mb-[20px] relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_600px_300px_at_50%_0%,rgba(0,229,184,0.08),transparent)] pointer-events-none" />
        <div className="w-[72px] h-[72px] rounded-[20px] bg-gradient-to-br from-cyan to-[#008a6e] flex items-center justify-center mx-auto mb-[16px] shadow-[0_0_40px_rgba(0,229,184,0.35)] relative z-10">
          <i className="ti ti-shield-check text-[36px] text-black"></i>
        </div>
        <div className="text-[26px] font-[900] tracking-[-0.6px] text-tx mb-[4px] relative z-10">IBVAP</div>
        <div className="text-[12.5px] text-tx3 mb-[16px] relative z-10">Intelligent Border Video Analytics Platform</div>
        <div className="inline-block text-[10px] font-mono font-[700] px-[12px] py-[3px] rounded-[20px] bg-cyan-d text-cyan border border-cyan/25 relative z-10">
          Prototype v0.1 &middot; Smart India Hackathon (SIH 2026)
        </div>
      </div>

      {/* Team Grid */}
      <div className="bg-s2 border border-b1 rounded-rad p-[20px] mb-[16px]">
        <div className="flex items-center gap-[10px] pb-[14px] mb-[16px] border-b border-b1">
          <div className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center bg-cyan-d text-cyan text-[14px]">
            <i className="ti ti-users"></i>
          </div>
          <h3 className="text-[13px] font-[700] text-tx flex-1">Team Members</h3>
        </div>

        <div className="grid grid-cols-4 gap-[14px]">
          {team.map((m, idx) => (
            <div key={idx} className="bg-s1 border border-b1 rounded-rad p-[18px] text-center hover:-translate-y-[2px] transition-transform">
              <div className="w-[50px] h-[50px] rounded-full border-2 border-b2 flex items-center justify-center mx-auto mb-[12px] text-[20px] bg-cyan-d text-cyan">
                <i className="ti ti-user"></i>
              </div>
              <div className="text-[9.5px] font-[700] tracking-[1px] uppercase px-[8px] py-[2px] rounded-[20px] inline-block mb-[6px] bg-s3 text-tx3 border border-b1">
                {m.role}
              </div>
              <div className="text-[14px] font-[700] text-tx mb-[2px]">{m.name}</div>
              <div className="text-[11px] text-tx3">{m.detail}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tech Stack */}
      <div className="bg-s2 border border-b1 rounded-rad p-[20px]">
        <div className="flex items-center gap-[10px] pb-[14px] mb-[16px] border-b border-b1">
          <div className="w-[30px] h-[30px] rounded-[8px] flex items-center justify-center bg-blue-d text-blue text-[14px]">
            <i className="ti ti-stack-2"></i>
          </div>
          <h3 className="text-[13px] font-[700] text-tx flex-1">Technology Architecture</h3>
        </div>

        <div className="flex flex-wrap gap-[8px]">
          {techStack.map((tech, idx) => (
            <span key={idx} className="inline-flex items-center gap-[6px] px-[12px] py-[6px] rounded-[20px] bg-s3 border border-b1 text-[11.5px] text-tx2">
              <i className={`ti ${tech.icon} text-[14px] text-cyan`}></i>
              {tech.name}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
