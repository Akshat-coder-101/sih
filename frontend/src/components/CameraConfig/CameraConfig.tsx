import React from 'react';
import { useApp } from '../../context/AppContext';

export const CameraConfig: React.FC = () => {
  const { cams, toggleCamOnline } = useApp();

  return (
    <div className="flex-1 overflow-y-auto p-[24px]">
      <div className="flex items-center justify-between mb-[22px]">
        <div>
          <div className="text-[18px] font-[800] tracking-[-0.4px] text-tx">Camera Configuration</div>
          <div className="text-[11.5px] text-tx3 mt-[1px]">Registered camera nodes &amp; edge RTSP stream endpoints</div>
        </div>
      </div>

      <div className="bg-s2 border border-b1 rounded-rad p-[20px] divide-y divide-b0">
        {cams.map(c => (
          <div key={c.id} className="flex items-center gap-[16px] py-[16px] first:pt-0 last:pb-0">
            <div className={`w-[36px] h-[36px] rounded-[10px] flex items-center justify-center text-[16px] ${
              c.online ? 'bg-cyan-d text-cyan border border-cyan/20' : 'bg-red-d text-red border border-red/20'
            }`}>
              <i className={`ti ${c.online ? 'ti-video' : 'ti-video-off'}`}></i>
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-[8px]">
                <strong className="text-[13px] text-tx font-bold">{c.name}</strong>
                {c.id === 'cam-1' && (
                  <span className="text-[9px] font-mono text-cyan bg-cyan-dd border border-cyan/30 px-[6px] py-[1px] rounded">
                    Webcam / AI Feed
                  </span>
                )}
              </div>
              <div className="text-[11px] text-tx3 font-mono mt-[2px]">{c.rtspUrl} &nbsp;·&nbsp; {c.location}</div>
            </div>

            <span className={`text-[9.5px] font-[700] uppercase tracking-[0.4px] px-[8px] py-[2px] rounded-[5px] border ${
              c.priority === 'High' ? 'bg-red-d text-red border-red/25' : 'bg-amber-d text-amber border-amber/25'
            }`}>
              {c.priority} priority
            </span>

            <span className={`text-[9.5px] font-[700] uppercase tracking-[0.4px] px-[8px] py-[2px] rounded-[5px] border ${
              c.online ? 'bg-cyan-d text-cyan border-cyan/25' : 'bg-s3 text-tx4 border-b1'
            }`}>
              {c.online ? 'Connected' : 'Disconnected'}
            </span>

            {/* Toggle Switch */}
            <div
              onClick={() => toggleCamOnline(c.id)}
              className={`w-[40px] h-[22px] rounded-[11px] border cursor-pointer relative transition-colors duration-200 shrink-0 ${
                c.online ? 'bg-cyan border-cyan' : 'bg-s4 border-b2'
              }`}
            >
              <div className={`w-[16px] h-[16px] rounded-full bg-white absolute top-[2px] left-[2px] transition-transform duration-200 ${
                c.online ? 'translate-x-[18px]' : 'translate-x-0'
              }`} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
