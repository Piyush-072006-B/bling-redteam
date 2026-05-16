import React, { useState } from 'react';
import { PackageOpen, DownloadCloud } from 'lucide-react';

export default function EvidenceViewer({ onBundle }) {
  const [isExporting, setIsExporting] = useState(false);

  const handleBundle = async () => {
    setIsExporting(true);
    await onBundle();
    setTimeout(() => setIsExporting(false), 2000); // Visual delay for demo
  };

  return (
    <div className="glass p-4 rounded-xl shadow-lg border border-slate-700 flex flex-col gap-3 mt-auto">
      <h3 className="text-sm font-semibold flex items-center gap-2 text-slate-200">
        <PackageOpen size={16} className="text-indigo-400" /> Auto Evidence Bundler
      </h3>
      <p className="text-xs text-slate-400 leading-tight">
        Packages graph snapshots, exported JSONs, replay hashes, and metrics into a zip archive.
      </p>
      
      <button 
        onClick={handleBundle}
        disabled={isExporting}
        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white p-2 rounded flex items-center justify-center gap-2 text-sm transition-colors disabled:opacity-50"
      >
        <DownloadCloud size={16} />
        {isExporting ? 'Packaging Evidence...' : 'Download Demo Bundle'}
      </button>
    </div>
  );
}
