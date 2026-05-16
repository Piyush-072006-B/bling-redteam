import React from 'react';
import { Terminal, Wifi, WifiOff, Activity, RefreshCw } from 'lucide-react';

export default function DebugPanel({ isConnected, status, lastPacket, lastMutation, backendHealth, reconnectCount }) {
  const apiHealthy = !!backendHealth;
  const wsClients  = backendHealth?.ws_clients ?? '—';

  return (
    <div className="absolute top-20 right-4 z-50 glass p-4 rounded-xl shadow-lg border border-slate-700 w-80 text-xs overflow-hidden flex flex-col gap-2">
      <h3 className="font-bold flex items-center gap-2 text-rose-400 mb-1 border-b border-slate-700 pb-2">
        <Terminal size={14} /> Sandbox Debug Panel
      </h3>

      {/* Connectivity grid */}
      <div className="grid grid-cols-2 gap-x-2 gap-y-1">
        <span className="text-slate-400 flex items-center gap-1">
          {isConnected ? <Wifi size={10} className="text-emerald-400" /> : <WifiOff size={10} className="text-rose-400" />}
          WebSocket:
        </span>
        <span className={isConnected ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
          {isConnected ? 'CONNECTED' : `DISCONNECTED${reconnectCount > 0 ? ` (retry #${reconnectCount})` : ''}`}
        </span>

        <span className="text-slate-400 flex items-center gap-1">
          <Activity size={10} className={apiHealthy ? 'text-emerald-400' : 'text-rose-400'} />
          Backend API:
        </span>
        <span className={apiHealthy ? 'text-emerald-400 font-bold' : 'text-rose-400 font-bold'}>
          {apiHealthy ? 'HEALTHY' : 'UNREACHABLE'}
        </span>

        <span className="text-slate-400">Sandbox State:</span>
        <span className="text-blue-400 font-mono">{status?.state ?? '—'}</span>

        <span className="text-slate-400">WS Clients (server):</span>
        <span className="text-yellow-300 font-mono">{wsClients}</span>

        <span className="text-slate-400">Kafka Consumer:</span>
        <span className={apiHealthy ? 'text-emerald-400' : 'text-slate-500'}>
          {apiHealthy ? 'ACTIVE' : 'UNKNOWN'}
        </span>
      </div>

      {/* Last graph packet */}
      <div className="flex flex-col gap-1 mt-1">
        <span className="text-slate-400 font-semibold border-b border-slate-700 pb-1 flex items-center gap-1">
          <RefreshCw size={10} /> Last Graph Packet
        </span>
        <pre className="bg-slate-900 p-2 rounded overflow-x-auto text-[10px] text-emerald-300 max-h-20">
          {lastPacket ? JSON.stringify(lastPacket, null, 2) : 'Awaiting stream...'}
        </pre>
      </div>

      {/* Last mutation packet */}
      <div className="flex flex-col gap-1">
        <span className="text-slate-400 font-semibold border-b border-slate-700 pb-1">Last Mutation / Evasion</span>
        <pre className="bg-slate-900 p-2 rounded overflow-x-auto text-[10px] text-orange-300 max-h-20">
          {lastMutation ? JSON.stringify(lastMutation, null, 2) : 'No mutations yet.'}
        </pre>
      </div>
    </div>
  );
}
