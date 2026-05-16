import React, { useState } from 'react';
import Graph3D from './components/Graph3D';
import ControlPanel from './components/ControlPanel';
import StatusIndicator from './components/StatusIndicator';
import TimelineReplay from './components/TimelineReplay';
import MetricsPanel from './components/MetricsPanel';
import EvidenceViewer from './components/EvidenceViewer';
import DebugPanel from './components/DebugPanel';
import { useSandboxSocket } from './hooks/useSandboxSocket';

function App() {
  const {
    isConnected,
    backendHealth,
    graphData,
    status,
    startSandbox,
    stopSandbox,
    createBundle,
    clearGraph,
    lastPacket,
    lastMutation,
    reconnectCount,
  } = useSandboxSocket('ws://localhost:8081/ws/stream');

  const [demoSafeMode, setDemoSafeMode] = useState(false);

  return (
    <div className="h-screen w-screen relative overflow-hidden flex flex-col">
      <DebugPanel
        isConnected={isConnected}
        status={status}
        lastPacket={lastPacket}
        lastMutation={lastMutation}
        backendHealth={backendHealth}
        reconnectCount={reconnectCount}
      />
      {/* Background 3D Graph */}
      <div className="absolute inset-0 z-0">
        <Graph3D graphData={graphData} />
      </div>

      {/* Header Overlay */}
      <header className="z-10 flex justify-between items-center p-4 glass m-4 rounded-xl shadow-lg">
        <div>
          <h1 className="text-2xl font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-emerald-400">
            BLING
          </h1>
          <p className="text-xs text-slate-400">Adversarial Graph Evolution Laboratory</p>
        </div>
        <StatusIndicator isConnected={isConnected} status={status} />
      </header>

      {/* Main Content Overlay */}
      <main className="z-10 flex-grow flex justify-between p-4 pointer-events-none">
        
        {/* Left Sidebar - Controls */}
        <div className="w-80 flex flex-col gap-4 pointer-events-auto">
          <ControlPanel 
            status={status} 
            onStart={startSandbox} 
            onStop={stopSandbox} 
            onClear={clearGraph}
            demoSafeMode={demoSafeMode}
            setDemoSafeMode={setDemoSafeMode}
          />
          <EvidenceViewer onBundle={createBundle} />
        </div>

        {/* Right Sidebar - Metrics */}
        <div className="w-80 flex flex-col gap-4 pointer-events-auto">
          <MetricsPanel metrics={graphData.metrics} nodesCount={graphData.nodes.length} edgesCount={graphData.links.length} />
        </div>

      </main>

      {/* Footer Overlay - Timeline */}
      <footer className="z-10 p-4 pointer-events-auto">
        <TimelineReplay lineage={graphData.lineage} />
      </footer>
    </div>
  );
}

export default App;
