import React, { useState } from 'react';
import { History, PlayCircle, PauseCircle, SkipBack, SkipForward } from 'lucide-react';

export default function TimelineReplay({ lineage }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(100);

  // Lineage contains historical mutation events
  const totalFrames = lineage.length;

  return (
    <div className="glass mx-auto w-[600px] p-4 rounded-xl shadow-lg border border-slate-700 flex flex-col gap-3">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-semibold flex items-center gap-2 text-slate-200">
          <History size={16} className="text-blue-400" /> Topology Lineage Replay
        </h3>
        <span className="text-xs text-slate-400">{totalFrames} Mutations Recorded</span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex gap-2">
          <button className="text-slate-400 hover:text-white transition-colors" title="Previous Frame"><SkipBack size={18} /></button>
          <button 
            className="text-slate-400 hover:text-white transition-colors" 
            onClick={() => setIsPlaying(!isPlaying)}
          >
            {isPlaying ? <PauseCircle size={20} className="text-amber-400" /> : <PlayCircle size={20} className="text-emerald-400" />}
          </button>
          <button className="text-slate-400 hover:text-white transition-colors" title="Next Frame"><SkipForward size={18} /></button>
        </div>

        <input 
          type="range" 
          min="0" 
          max="100" 
          value={progress} 
          onChange={e => setProgress(e.target.value)}
          className="w-full accent-blue-500 h-1 bg-slate-700 rounded-lg appearance-none cursor-pointer"
        />
        <span className="text-xs font-mono w-8 text-right text-slate-400">{progress}%</span>
      </div>
    </div>
  );
}
