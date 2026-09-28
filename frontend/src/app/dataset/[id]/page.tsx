'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Database,
  CheckCircle2,
  AlertTriangle,
  GitMerge,
  Layers,
  Sparkles,
  Loader2,
  Table2,
  FileSpreadsheet,
} from 'lucide-react';
import { api } from '@/lib/api';
import { DatasetResponse } from '@/lib/types';
import { DatasetTable } from '@/components/dataset/DatasetTable';
import { ExportDropdown } from '@/components/dataset/ExportDropdown';

export default function DatasetPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const runId = resolvedParams.id;

  const [dataset, setDataset] = useState<DatasetResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDataset() {
      try {
        const data = await api.getDataset(runId, { page: 1, page_size: 100 });
        setDataset(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load dataset');
      } finally {
        setLoading(false);
      }
    }
    loadDataset();
  }, [runId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <p className="text-sm text-slate-400 font-mono">Loading structured intelligence dataset...</p>
      </div>
    );
  }

  if (error || !dataset) {
    return (
      <div className="max-w-xl mx-auto my-12 p-6 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Dataset Not Found</h2>
        <p className="text-xs text-rose-200">{error || 'Could not retrieve records for this run.'}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 text-xs font-semibold text-white hover:bg-slate-700"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Studio
        </Link>
      </div>
    );
  }

  const avgConfidence = Math.round(
    (dataset.records.reduce((acc, r) => acc + (r.confidence_score || 0.95), 0) /
      Math.max(dataset.records.length, 1)) *
      100
  );

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Link href="/" className="hover:text-cyan-400 transition-colors">
              Studio
            </Link>
            <span>/</span>
            <Link href={`/plan/${dataset.workflow_id}`} className="hover:text-cyan-400 transition-colors">
              Workflow DAG
            </Link>
            <span>/</span>
            <span className="text-slate-200 font-mono">Dataset ({dataset.records.length} records)</span>
          </div>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-2.5">
              <Table2 className="w-7 h-7 text-cyan-400" />
              <span>Intelligence Dataset</span>
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              {dataset.execution_mode.toUpperCase()} MODE
            </span>
          </div>

          <p className="text-xs text-slate-400 max-w-3xl truncate italic">
            &ldquo;{dataset.prompt}&rdquo;
          </p>
        </div>

        {/* Action Buttons: Export & Workflow Link */}
        <div className="flex items-center gap-3">
          <Link
            href={`/plan/${dataset.workflow_id}`}
            className="px-3.5 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1.5"
          >
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>View Workflow Graph</span>
          </Link>

          <ExportDropdown runId={runId} />
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
            Active Dataset Records
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-white">
              {dataset.records.length}
            </span>
            <span className="text-xs text-slate-500">rows</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[11px] uppercase tracking-wider text-emerald-400 font-medium">
            Strictly Valid
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">
              {dataset.valid_records}
            </span>
            <span className="text-xs text-slate-500">RFC passed</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[11px] uppercase tracking-wider text-rose-400 font-medium">
            Deduplicated & Merged
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-rose-400">
              {dataset.duplicate_records}
            </span>
            <span className="text-xs text-slate-500">near-duplicates</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
          <span className="text-[11px] uppercase tracking-wider text-cyan-400 font-medium">
            Average Confidence
          </span>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold font-mono text-cyan-300">
              {avgConfidence}%
            </span>
            <span className="text-xs text-slate-500">integrity</span>
          </div>
        </div>
      </div>

      {/* Main Interactive Table & Evidence Drawer */}
      <DatasetTable fields={dataset.fields} records={dataset.records} />
    </div>
  );
}
