'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ArrowLeft,
  ArrowRight,
  Database,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  Sparkles,
  GitMerge,
  ShieldCheck,
  Table2,
} from 'lucide-react';
import { api } from '@/lib/api';
import { WorkflowResponse, WorkflowRunStatus } from '@/lib/types';
import { WorkflowGraph } from '@/components/workflow/WorkflowGraph';

export default function ExecutionPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const resolvedParams = use(params);
  const runId = resolvedParams.id;

  const [runStatus, setRunStatus] = useState<WorkflowRunStatus | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let intervalId: NodeJS.Timeout;

    async function pollStatus() {
      try {
        const status = await api.getRunStatus(runId);
        setRunStatus(status);

        if (!workflow && status.workflow_id) {
          const wf = await api.getWorkflow(status.workflow_id);
          setWorkflow(wf);
        }

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(intervalId);
        }
      } catch (err: any) {
        setError(err.message || 'Error tracking execution');
      } finally {
        setLoading(false);
      }
    }

    pollStatus();
    intervalId = setInterval(pollStatus, 700);

    return () => clearInterval(intervalId);
  }, [runId, workflow]);

  if (loading && !runStatus) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <p className="text-sm text-slate-400 font-mono">Initializing pipeline execution engine...</p>
      </div>
    );
  }

  if (error || !runStatus) {
    return (
      <div className="max-w-xl mx-auto my-12 p-6 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Execution Error</h2>
        <p className="text-xs text-rose-200">{error || 'Could not fetch run details.'}</p>
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

  const isCompleted = runStatus.status === 'completed';
  const isFailed = runStatus.status === 'failed';
  const isRunning = runStatus.status === 'running' || runStatus.status === 'pending';

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
            {workflow && (
              <Link href={`/plan/${workflow.id}`} className="hover:text-cyan-400 transition-colors">
                Workflow
              </Link>
            )}
            <span>/</span>
            <span className="text-slate-200 font-mono">Run: {runId.slice(0, 8)}...</span>
          </div>

          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Live Pipeline Execution
            </h1>
            <span
              className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold flex items-center gap-1.5 ${
                isCompleted
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : isFailed
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  : 'bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse'
              }`}
            >
              {isRunning && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {isCompleted && <CheckCircle2 className="w-3.5 h-3.5" />}
              {isFailed && <AlertCircle className="w-3.5 h-3.5" />}
              {runStatus.status.toUpperCase()}
            </span>

            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-slate-900 text-slate-300 border border-slate-800 uppercase">
              {runStatus.execution_mode} Engine
            </span>
          </div>

          {runStatus.error_message && (
            <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/30 text-xs text-amber-300 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0" />
              <span>{runStatus.error_message}</span>
            </div>
          )}

          {workflow && (
            <p className="text-xs text-slate-400 max-w-2xl truncate italic">
              &ldquo;{workflow.prompt}&rdquo;
            </p>
          )}
        </div>

        {/* Action Button */}
        {isCompleted && (
          <Link
            href={`/dataset/${runId}`}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-400 hover:to-indigo-400 text-slate-950 font-bold text-sm shadow-xl shadow-cyan-500/25 active:scale-95 transition-all"
          >
            <Table2 className="w-4 h-4" />
            <span>Open Dataset Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        )}
      </div>

      {/* Progress Bar & KPI Cards */}
      <div className="space-y-4">
        {/* Progress Bar */}
        <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-300 uppercase tracking-wider">
              Execution Progress
            </span>
            <span className="font-mono text-cyan-400 font-bold">
              {runStatus.progress_percent}%
            </span>
          </div>

          <div className="w-full bg-slate-950 h-3 rounded-full overflow-hidden border border-slate-800">
            <div
              className={`h-full transition-all duration-300 rounded-full ${
                isCompleted
                  ? 'bg-emerald-500'
                  : isFailed
                  ? 'bg-rose-500'
                  : 'bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500 animate-pulse'
              }`}
              style={{ width: `${runStatus.progress_percent}%` }}
            />
          </div>
        </div>

        {/* KPI Counter Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
              Total Records
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-white">
                {runStatus.total_records}
              </span>
              <span className="text-xs text-slate-500">extracted</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-emerald-400 font-medium">
              Valid Records
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-emerald-400">
                {runStatus.valid_records}
              </span>
              <span className="text-xs text-slate-500">RFC verified</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-rose-400 font-medium">
              Duplicates Eliminated
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-2xl font-bold font-mono text-rose-400">
                {runStatus.duplicate_records}
              </span>
              <span className="text-xs text-slate-500">fuzzy merged</span>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-1">
            <span className="text-[11px] uppercase tracking-wider text-cyan-400 font-medium">
              Pipeline Mode
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-sm font-bold font-mono text-cyan-300 uppercase">
                {runStatus.execution_mode}
              </span>
              <span className="text-xs text-slate-500">engine</span>
            </div>
          </div>
        </div>
      </div>

      {/* Live React Flow DAG with active state */}
      {workflow && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="font-semibold uppercase tracking-wider text-slate-300">
              Live Pipeline DAG (Updating in Real-Time)
            </span>
            <span>Click any node to see intermediate records and logs</span>
          </div>
          <WorkflowGraph
            steps={workflow.plan.steps}
            stepStatuses={runStatus.step_statuses}
            height="500px"
          />
        </div>
      )}

      {/* Audit Log Stream */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Engine Execution Log & Traceability Stream
        </h3>

        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {runStatus.step_statuses.map((step) => (
            <div
              key={step.step_id}
              className={`p-3 rounded-xl border text-xs flex items-center justify-between transition-colors ${
                step.status === 'completed'
                  ? 'bg-slate-950/80 border-emerald-500/20'
                  : step.status === 'running'
                  ? 'bg-blue-950/20 border-blue-500/30 animate-pulse'
                  : step.status === 'failed'
                  ? 'bg-rose-950/30 border-rose-500/30'
                  : 'bg-slate-950/40 border-slate-800/80 text-slate-500'
              }`}
            >
              <div className="flex items-center gap-3">
                {step.status === 'completed' && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                )}
                {step.status === 'running' && (
                  <Loader2 className="w-4 h-4 text-blue-400 animate-spin flex-shrink-0" />
                )}
                {step.status === 'pending' && (
                  <Clock className="w-4 h-4 text-slate-600 flex-shrink-0" />
                )}
                {step.status === 'failed' && (
                  <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
                )}

                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">{step.step_name}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-900 text-slate-400 border border-slate-800">
                      {step.step_type}
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                    {step.message}
                  </p>
                </div>
              </div>

              {step.records_produced > 0 && (
                <span className="font-mono text-[11px] text-emerald-400 font-semibold px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20">
                  +{step.records_produced} records
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
