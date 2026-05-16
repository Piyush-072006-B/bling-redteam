import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Wifi, WifiOff } from 'lucide-react';

export default function StatusIndicator({ isConnected, status }) {
  const stateColors = {
    IDLE: 'bg-slate-500',
    STARTING: 'bg-amber-500',
    RUNNING: 'bg-emerald-500',
    PAUSED: 'bg-amber-500',
    EXPORTING: 'bg-blue-500',
    COMPLETED: 'bg-indigo-500',
    ERROR: 'bg-rose-500',
  };

  const bgColor = stateColors[status.state] || 'bg-slate-500';

  return (
    <div className="flex items-center gap-6">
      
      {/* Sandbox Status */}
      <div className="flex items-center gap-3 bg-slate-800/80 px-4 py-2 rounded-full border border-slate-700">
        <div className="relative flex h-3 w-3">
          {(status.state === 'RUNNING' || status.state === 'STARTING') && (
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${bgColor}`}></span>
          )}
          <span className={`relative inline-flex rounded-full h-3 w-3 ${bgColor}`}></span>
        </div>
        <span className="text-xs font-semibold tracking-wider text-slate-300">
          {status.state}
        </span>
        {status.current_attack_type && (
          <span className="text-xs px-2 py-0.5 bg-slate-700 rounded text-slate-400 uppercase">
            {status.current_attack_type.replace('_', ' ')}
          </span>
        )}
      </div>

      {/* Connection Status */}
      <div className="flex items-center gap-2 text-xs font-medium text-slate-400">
        {isConnected ? (
          <><Wifi size={14} className="text-emerald-500" /> Connected</>
        ) : (
          <><WifiOff size={14} className="text-rose-500" /> Disconnected</>
        )}
      </div>

    </div>
  );
}
