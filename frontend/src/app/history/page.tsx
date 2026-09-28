'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  History,
  Layers,
  Table2,
  Play,
  Trash2,
  Loader2,
  Clock,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  Database,
} from 'lucide-react';
import { api } from '@/lib/api';
import { WorkflowResponse } from '@/lib/types';

export default function HistoryPage() {
  const router = useRouter();
  const [workflows, setWorkflows] = useState<WorkflowResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [rerunningId, setRerunningId] = useState<string | null>(null);

  const loadWorkflows = async () => {
    try {
      const data = await api.listWorkflows();
      setWorkflows(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorkflows();
  }, []);

  const handleRerun = async (workflowId: string) => {
    setRerunningId(workflowId);
    try {
      const runStatus = await api.runWorkflow(workflowId, 'demo');
      router.push(`/execution/${runStatus.run_id}`);
    } catch (err: any) {
      alert(`Rerun failed: ${err.message}`);
      setRerunningId(null);
    }
  };

  const handleDelete = async (workflowId: string) => {
    if (!confirm('Are you sure you want to delete this workflow and its records?')) return;
    try {
      await api.deleteWorkflow(workflowId);
      setWorkflows(workflows.filter((w) => w.id !== workflowId));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <History className="w-6 h-6 text-indigo-400" />
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Workflow & Dataset History
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Browse, re-inspect, or re-run historical intelligence extraction pipelines.
          </p>
        </div>

        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs transition-colors self-start sm:self-auto"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>New Pipeline</span>
        </Link>
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
          <p className="text-sm text-slate-400 font-mono">Loading workflow archive...</p>
        </div>
      ) : workflows.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {workflows.map((wf) => {
            const hasRuns = wf.run_count > 0 && wf.latest_run_id;
            const isCompleted = wf.latest_status === 'completed';

            return (
              <div
                key={wf.id}
                className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
              >
                {/* Info */}
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                      {wf.plan.domain.replace(/_/g, ' ')}
                    </span>

                    {wf.latest_status && (
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold flex items-center gap-1 ${
                          isCompleted
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                            : wf.latest_status === 'running'
                            ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {isCompleted && <CheckCircle2 className="w-3 h-3" />}
                        {wf.latest_status.toUpperCase()}
                      </span>
                    )}

                    <span className="text-xs text-slate-500 font-mono flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {new Date(wf.created_at).toLocaleString([], {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>

                  <p className="text-sm text-slate-200 font-medium line-clamp-2 leading-relaxed">
                    &ldquo;{wf.prompt}&rdquo;
                  </p>

                  <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
                    <span>{wf.plan.steps.length} DAG Steps</span>
                    <span>&bull;</span>
                    <span>{wf.plan.fields.length} Fields</span>
                    <span>&bull;</span>
                    <span>{wf.run_count} Execution(s)</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2.5 flex-shrink-0 w-full md:w-auto justify-end border-t md:border-t-0 pt-3 md:pt-0 border-slate-800">
                  <Link
                    href={`/plan/${wf.id}`}
                    className="px-3 py-2 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1.5"
                  >
                    <Layers className="w-3.5 h-3.5 text-cyan-400" />
                    <span>View DAG</span>
                  </Link>

                  {hasRuns && (
                    <Link
                      href={`/dataset/${wf.latest_run_id}`}
                      className="px-3 py-2 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1.5"
                    >
                      <Table2 className="w-3.5 h-3.5" />
                      <span>Dataset</span>
                    </Link>
                  )}

                  <button
                    onClick={() => handleRerun(wf.id)}
                    disabled={rerunningId === wf.id}
                    className="px-3 py-2 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {rerunningId === wf.id ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Play className="w-3.5 h-3.5 fill-current" />
                    )}
                    <span>Rerun</span>
                  </button>

                  <button
                    onClick={() => handleDelete(wf.id)}
                    className="p-2 rounded-xl bg-slate-950 hover:bg-rose-950/40 border border-slate-800 hover:border-rose-500/30 text-slate-500 hover:text-rose-400 transition-colors"
                    title="Delete workflow"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="max-w-md mx-auto my-16 text-center space-y-4 p-8 rounded-2xl bg-slate-900/40 border border-slate-800">
          <Database className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-semibold text-white">No Workflows Recorded Yet</h3>
          <p className="text-xs text-slate-400">
            Submit your first natural language data intelligence request in the Pipeline Studio to generate a dynamic DAG.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 text-xs font-bold hover:bg-cyan-400 transition-colors"
          >
            Launch Pipeline Studio
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      )}
    </div>
  );
}
