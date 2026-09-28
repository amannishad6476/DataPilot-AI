'use client';

import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileJson, ChevronDown } from 'lucide-react';
import { api } from '@/lib/api';

interface ExportDropdownProps {
  runId: string;
}

export function ExportDropdown({ runId }: ExportDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);

  const handleDownloadCsv = () => {
    window.open(api.getExportCsvUrl(runId), '_blank');
    setIsOpen(false);
  };

  const handleDownloadJson = () => {
    window.open(api.getExportJsonUrl(runId), '_blank');
    setIsOpen(false);
  };

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs transition-all shadow-md shadow-cyan-500/20 active:scale-95"
      >
        <Download className="w-3.5 h-3.5" />
        <span>Export Dataset</span>
        <ChevronDown className="w-3.5 h-3.5" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-20"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-48 rounded-xl bg-slate-900 border border-slate-800 shadow-2xl z-30 py-1.5 focus:outline-none backdrop-blur-md">
            <button
              onClick={handleDownloadCsv}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-200 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span>Export as CSV (.csv)</span>
            </button>
            <button
              onClick={handleDownloadJson}
              className="w-full flex items-center gap-2.5 px-3.5 py-2 text-xs text-slate-200 hover:bg-slate-800 hover:text-white transition-colors"
            >
              <FileJson className="w-4 h-4 text-amber-400" />
              <span>Export as JSON (.json)</span>
            </button>
          </div>
        </>
      )}
    </div>
  );
}
