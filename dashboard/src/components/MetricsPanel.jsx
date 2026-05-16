import React from 'react';
import { Activity, Network, Zap, ShieldAlert } from 'lucide-react';
import { motion } from 'framer-motion';

export default function MetricsPanel({ metrics, nodesCount, edgesCount }) {
  const StatBox = ({ title, value, icon, color }) => (
    <motion.div 
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="bg-slate-800/80 p-3 rounded-lg border border-slate-700 flex flex-col gap-1"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs text-slate-400 font-medium uppercase tracking-wider">{title}</span>
        {icon}
      </div>
      <span className={`text-xl font-bold ${color}`}>{value}</span>
    </motion.div>
  );

  return (
    <div className="glass p-4 rounded-xl shadow-lg border border-slate-700 flex flex-col gap-4">
      <h2 className="text-lg font-bold flex items-center gap-2 text-slate-200">
        <Activity size={18} className="text-blue-400" /> Live Metrics
      </h2>
      
      <div className="grid grid-cols-2 gap-3">
        <StatBox 
          title="Active Nodes" 
          value={nodesCount.toLocaleString()} 
          icon={<Network size={14} className="text-slate-500" />}
          color="text-blue-400"
        />
        <StatBox 
          title="Active Edges" 
          value={edgesCount.toLocaleString()} 
          icon={<Zap size={14} className="text-slate-500" />}
          color="text-amber-400"
        />
        <StatBox 
          title="Novelty Score" 
          value={metrics?.novelty_score !== undefined ? metrics.novelty_score.toFixed(3) : '0.000'} 
          icon={<Activity size={14} className="text-slate-500" />}
          color="text-emerald-400"
        />
        <StatBox 
          title="Struct Divergence" 
          value={metrics?.structural_divergence !== undefined ? metrics.structural_divergence.toFixed(3) : '0.000'} 
          icon={<ShieldAlert size={14} className="text-slate-500" />}
          color="text-rose-400"
        />
      </div>

      {metrics?.topology_family && (
        <div className="bg-slate-800/80 p-3 rounded-lg border border-slate-700 mt-1">
          <div className="text-xs text-slate-400 font-medium uppercase tracking-wider mb-1">Evolving Morphology</div>
          <div className="text-sm font-mono text-blue-300 break-words">{metrics.topology_family}</div>
        </div>
      )}

      <div className="mt-2">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-slate-400">Detection Evasion Rate</span>
          <span className="text-emerald-400 font-mono">
            {((1 - (metrics?.detection_rate || 1)) * 100).toFixed(1)}%
          </span>
        </div>
        <div className="w-full bg-slate-700 rounded-full h-1.5">
          <motion.div 
            className="bg-emerald-500 h-1.5 rounded-full" 
            initial={{ width: 0 }}
            animate={{ width: `${(1 - (metrics?.detection_rate || 1)) * 100}%` }}
            transition={{ duration: 0.5 }}
          ></motion.div>
        </div>
      </div>
    </div>
  );
}
