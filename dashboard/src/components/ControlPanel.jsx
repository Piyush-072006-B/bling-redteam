import React, { useState } from 'react';
import { Play, Square, RefreshCw, ShieldAlert } from 'lucide-react';

export default function ControlPanel({ status, onStart, onStop, onClear, demoSafeMode, setDemoSafeMode }) {
  const [attackType, setAttackType] = useState('layering_chain');
  const [depth, setDepth] = useState(6);
  const [tps, setTps] = useState(3.0);

  const attacks = [
    'layering_chain', 'round_trip', 'mule_network', 
    'structuring', 'dormant_activation', 'velocity_attack', 'fan_in_fan_out'
  ];

  const handleStart = () => {
    onStart({ attack_type: attackType, attack_depth: depth, tps, demo_safe_mode: demoSafeMode });
  };

  const isRunning = status.state === 'RUNNING' || status.state === 'STARTING';

  return (
    <div className="glass p-4 rounded-xl shadow-lg flex flex-col gap-4 border border-slate-700">
      <h2 className="text-lg font-bold flex items-center gap-2"><ShieldAlert size={18} className="text-rose-500" /> Sandbox Controls</h2>
      
      <div className="flex flex-col gap-2">
        <label className="text-xs text-slate-400">Attack Topology</label>
        <select 
          className="bg-slate-800 border border-slate-700 rounded p-2 text-sm focus:outline-none focus:border-blue-500"
          value={attackType} 
          onChange={e => setAttackType(e.target.value)}
          disabled={isRunning}
        >
          {attacks.map(a => <option key={a} value={a}>{a.replace('_', ' ').toUpperCase()}</option>)}
        </select>
      </div>

      <div className="flex gap-4">
        <div className="flex flex-col gap-2 flex-1">
          <label className="text-xs text-slate-400">Depth</label>
          <input 
            type="number" min="2" max="20" 
            className="bg-slate-800 border border-slate-700 rounded p-2 text-sm"
            value={depth} onChange={e => setDepth(parseInt(e.target.value))} 
            disabled={isRunning}
          />
        </div>
        <div className="flex flex-col gap-2 flex-1">
          <label className="text-xs text-slate-400">TPS</label>
          <input 
            type="number" step="0.5" min="0.5" max="20"
            className="bg-slate-800 border border-slate-700 rounded p-2 text-sm"
            value={tps} onChange={e => setTps(parseFloat(e.target.value))} 
            disabled={isRunning}
          />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer mt-2">
        <input 
          type="checkbox" 
          checked={demoSafeMode} 
          onChange={e => setDemoSafeMode(e.target.checked)} 
          disabled={isRunning}
          className="accent-emerald-500"
        />
        Demo Safe Mode (Capped Load)
      </label>

      <div className="flex gap-2 mt-4">
        {!isRunning ? (
          <button 
            onClick={handleStart}
            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white p-2 rounded flex items-center justify-center gap-2 text-sm transition-colors"
          >
            <Play size={16} /> Start
          </button>
        ) : (
          <button 
            onClick={onStop}
            className="flex-1 bg-rose-600 hover:bg-rose-500 text-white p-2 rounded flex items-center justify-center gap-2 text-sm transition-colors"
          >
            <Square size={16} /> Stop
          </button>
        )}
        <button 
          onClick={onClear}
          disabled={isRunning}
          className="bg-slate-700 hover:bg-slate-600 p-2 rounded flex items-center justify-center transition-colors disabled:opacity-50"
          title="Reset Graph"
        >
          <RefreshCw size={16} />
        </button>
      </div>
    </div>
  );
}
