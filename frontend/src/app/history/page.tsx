'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  History,
  Layers,
  Table2,
  Play,
  RotateCcw,
  Trash2,
  Loader2,
  Clock,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Database,
  GitCompare,
  CheckSquare,
  Square,
  TrendingUp,
  TrendingDown,
  X,
  ShieldCheck,
  Filter,
} from 'lucide-react';
import { api } from '@/lib/api';
import { WorkflowResponse, WorkflowRunStatus, RunComparisonResponse } from '@/lib/types';

export default function HistoryPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'workflows' | 'runs'>('runs');
  const [workflows, setWorkflows] = useState<WorkflowResponse[]>([]);
  const [runs, setRuns] = useState<WorkflowRunStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [rerunningId, setRerunningId] = useState<string | null>(null);

  // Run comparison state
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>([]);
  const [comparing, setComparing] = useState(false);
  const [comparisonResult, setComparisonResult] = useState<RunComparisonResponse | null>(null);
  const [comparisonModalOpen, setComparisonModalOpen] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);

  // Search filter
  const [searchFilter, setSearchFilter] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [wfData, runsData] = await Promise.all([
        api.listWorkflows().catch(() => []),
        api.listRuns().catch(() => []),
      ]);
      setWorkflows(wfData);
      setRuns(runsData);
    } catch (err) {
      console.error('Failed to load history data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRerunWorkflow = async (workflowId: string) => {
    setRerunningId(workflowId);
    try {
      const runStatus = await api.runWorkflow(workflowId, 'demo');
      router.push(`/execution/${runStatus.run_id}`);
    } catch (err: any) {
      alert(`Rerun failed: ${err.message}`);
      setRerunningId(null);
    }
  };

  const handleRerunRun = async (runId: string) => {
    setRerunningId(runId);
    try {
      const newRun = await api.rerunWorkflow(runId);
      router.push(`/execution/${newRun.run_id}`);
    } catch (err: any) {
      alert(`Re-run failed: ${err.message}`);
      setRerunningId(null);
    }
  };

  const handleDeleteWorkflow = async (workflowId: string) => {
    if (!confirm('Are you sure you want to delete this workflow and all its execution runs?')) return;
    try {
      await api.deleteWorkflow(workflowId);
      setWorkflows((prev) => prev.filter((w) => w.id !== workflowId));
      setRuns((prev) => prev.filter((r) => r.workflow_id !== workflowId));
    } catch (err: any) {
      alert(`Delete failed: ${err.message}`);
    }
  };

  const toggleSelectRun = (runId: string) => {
    setSelectedRunIds((prev) => {
      if (prev.includes(runId)) {
        return prev.filter((id) => id !== runId);
      }
      if (prev.length >= 2) {
        return [prev[1], runId]; // Keep latest two selections
      }
      return [...prev, runId];
    });
  };

  const handleCompareRuns = async () => {
    if (selectedRunIds.length !== 2) return;
    setComparing(true);
    setComparisonError(null);
    try {
      const res = await api.compareRuns(selectedRunIds[0], selectedRunIds[1]);
      setComparisonResult(res);
      setComparisonModalOpen(true);
    } catch (err: any) {
      setComparisonError(err.message || 'Failed to compare runs');
      alert(`Comparison error: ${err.message}`);
    } finally {
      setComparing(false);
    }
  };

  const filteredRuns = runs.filter((r) => {
    if (!searchFilter.trim()) return true;
    const term = searchFilter.toLowerCase();
    const wf = workflows.find((w) => w.id === r.workflow_id);
    return (
      r.run_id.toLowerCase().includes(term) ||
      r.execution_mode.toLowerCase().includes(term) ||
      r.status.toLowerCase().includes(term) ||
      (wf && wf.prompt.toLowerCase().includes(term))
    );
  });

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <History className="w-6 h-6 text-indigo-400" />
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Execution Runs & Historical Archive
            </h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Re-run workflows, track confidence analytics across runs, and compare execution runs side-by-side.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-semibold text-xs transition-colors self-start sm:self-auto shadow-lg shadow-cyan-950/20"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>New Pipeline</span>
          </Link>
        </div>
      </div>

      {/* Tabs & Filter Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center p-1 rounded-xl bg-slate-900/80 border border-slate-800 self-start">
          <button
            onClick={() => setActiveTab('runs')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === 'runs'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Clock className="w-3.5 h-3.5" />
            <span>All Execution Runs ({runs.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('workflows')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-2 ${
              activeTab === 'workflows'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Workflow Blueprints ({workflows.length})</span>
          </button>
        </div>

        {activeTab === 'runs' && (
          <div className="flex items-center gap-3">
            <input
              type="text"
              placeholder="Filter by Run ID, mode, or prompt..."
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              className="px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 w-64"
            />
            {selectedRunIds.length === 2 && (
              <button
                onClick={handleCompareRuns}
                disabled={comparing}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs transition-all shadow-md animate-pulse"
              >
                {comparing ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitCompare className="w-3.5 h-3.5" />}
                <span>Compare 2 Selected Runs</span>
              </button>
            )}
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center min-h-[40vh] space-y-4">
          <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
          <p className="text-sm text-slate-400 font-mono">Loading history & audit logs...</p>
        </div>
      ) : activeTab === 'runs' ? (
        /* Runs View */
        filteredRuns.length > 0 ? (
          <div className="space-y-3">
            {selectedRunIds.length > 0 && (
              <div className="p-3 rounded-xl bg-slate-900/90 border border-indigo-500/30 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-slate-300">
                  <GitCompare className="w-4 h-4 text-indigo-400" />
                  <span>
                    Selected <strong>{selectedRunIds.length}/2</strong> runs for side-by-side comparison.
                    {selectedRunIds.length === 1 && ' Select one more completed run to compare.'}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {selectedRunIds.length === 2 && (
                    <button
                      onClick={handleCompareRuns}
                      disabled={comparing}
                      className="px-3 py-1 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold flex items-center gap-1.5 transition-colors"
                    >
                      {comparing ? <Loader2 className="w-3 h-3 animate-spin" /> : <GitCompare className="w-3 h-3" />}
                      Launch Comparison
                    </button>
                  )}
                  <button
                    onClick={() => setSelectedRunIds([])}
                    className="px-2 py-1 text-slate-400 hover:text-white"
                  >
                    Clear Selection
                  </button>
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-3">
              {filteredRuns.map((run) => {
                const wf = workflows.find((w) => w.id === run.workflow_id);
                const isSelected = selectedRunIds.includes(run.run_id);
                const isCompleted = run.status === 'completed';
                const isFailed = run.status === 'failed';
                const isCancelled = run.status === 'cancelled';
                const isRunning = run.status === 'running' || run.status === 'pending';

                return (
                  <div
                    key={run.run_id}
                    className={`p-4 rounded-xl border transition-all ${
                      isSelected
                        ? 'bg-slate-900 border-indigo-500/80 shadow-indigo-950/20 shadow-lg'
                        : 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700/80'
                    } flex flex-col md:flex-row items-start md:items-center justify-between gap-4`}
                  >
                    {/* Select Checkbox + Run Info */}
                    <div className="flex items-start gap-3 flex-1 min-w-0">
                      <button
                        onClick={() => toggleSelectRun(run.run_id)}
                        className="mt-1 text-slate-400 hover:text-indigo-400 transition-colors"
                        title={isSelected ? 'Deselect run' : 'Select run for comparison'}
                      >
                        {isSelected ? (
                          <CheckSquare className="w-4 h-4 text-indigo-400" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-600" />
                        )}
                      </button>

                      <div className="space-y-1.5 flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap text-xs">
                          {/* Run ID */}
                          <span className="font-mono text-slate-300 font-semibold">
                            #{run.run_id.slice(0, 8)}
                          </span>

                          {/* Status Badge */}
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold flex items-center gap-1 ${
                              isCompleted
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : isRunning
                                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse'
                                : isCancelled
                                ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {isCompleted && <CheckCircle2 className="w-2.5 h-2.5" />}
                            {isFailed && <XCircle className="w-2.5 h-2.5" />}
                            {run.status.toUpperCase()}
                          </span>

                          {/* Mode Badge */}
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-slate-800 text-cyan-300 border border-slate-700">
                            {run.execution_mode} MODE
                          </span>

                          {/* Timestamp */}
                          <span className="text-[11px] text-slate-500 font-mono flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {run.started_at ? new Date(run.started_at).toLocaleString([], {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit',
                              second: '2-digit'
                            }) : 'N/A'}
                          </span>
                        </div>

                        {/* Associated Prompt */}
                        {wf && (
                          <p className="text-xs text-slate-300 font-medium line-clamp-1">
                            &ldquo;{wf.prompt}&rdquo;
                          </p>
                        )}

                        {/* Metrics Bar */}
                        <div className="flex items-center gap-4 text-xs font-mono text-slate-400 flex-wrap">
                          <span>
                            Total: <strong className="text-white">{run.total_records}</strong>
                          </span>
                          <span>&bull;</span>
                          <span>
                            Valid: <strong className="text-emerald-400">{run.valid_records}</strong>
                          </span>
                          <span>&bull;</span>
                          <span>
                            Merged: <strong className="text-rose-400">{run.duplicate_records}</strong>
                          </span>
                          {run.quality_summary && (
                            <>
                              <span>&bull;</span>
                              <span>
                                Quality:{' '}
                                <strong className="text-cyan-300">
                                  {Math.round(run.quality_summary.average_confidence * 100)}%
                                </strong>
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2 flex-shrink-0 w-full md:w-auto justify-end border-t md:border-t-0 pt-2 md:pt-0 border-slate-800">
                      {isCompleted && (
                        <Link
                          href={`/dataset/${run.run_id}`}
                          className="px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-emerald-400 hover:text-emerald-300 transition-colors flex items-center gap-1.5"
                        >
                          <Table2 className="w-3.5 h-3.5" />
                          <span>Dataset</span>
                        </Link>
                      )}

                      <Link
                        href={`/execution/${run.run_id}`}
                        className="px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-slate-300 hover:text-white transition-colors flex items-center gap-1.5"
                      >
                        <Layers className="w-3.5 h-3.5 text-cyan-400" />
                        <span>Timeline</span>
                      </Link>

                      <button
                        onClick={() => handleRerunRun(run.run_id)}
                        disabled={rerunningId === run.run_id}
                        className="px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                        title="Re-run this pipeline with a fresh instance"
                      >
                        {rerunningId === run.run_id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <RotateCcw className="w-3.5 h-3.5" />
                        )}
                        <span>Re-run</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="max-w-md mx-auto my-16 text-center space-y-4 p-8 rounded-2xl bg-slate-900/40 border border-slate-800">
            <Clock className="w-12 h-12 text-slate-600 mx-auto" />
            <h3 className="text-base font-semibold text-white">No Execution Runs Found</h3>
            <p className="text-xs text-slate-400">
              Run any planned workflow to track execution metrics, timeline logs, and data quality analytics.
            </p>
          </div>
        )
      ) : (
        /* Workflows View */
        workflows.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {workflows.map((wf) => {
              const hasRuns = wf.run_count > 0 && wf.latest_run_id;
              const isCompleted = wf.latest_status === 'completed';

              return (
                <div
                  key={wf.id}
                  className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700/80 transition-all shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-6"
                >
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
                      <span>{wf.run_count} Execution Run(s)</span>
                    </div>
                  </div>

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
                      onClick={() => handleRerunWorkflow(wf.id)}
                      disabled={rerunningId === wf.id}
                      className="px-3 py-2 rounded-xl bg-slate-950 hover:bg-slate-850 border border-slate-800 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {rerunningId === wf.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Play className="w-3.5 h-3.5 fill-current" />
                      )}
                      <span>Execute</span>
                    </button>

                    <button
                      onClick={() => handleDeleteWorkflow(wf.id)}
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
        )
      )}

      {/* Side-by-Side Run Comparison Modal */}
      {comparisonModalOpen && comparisonResult && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl p-6 space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <GitCompare className="w-6 h-6 text-cyan-400" />
                <div>
                  <h3 className="text-lg font-bold text-white">Execution Run Comparison</h3>
                  <p className="text-xs text-slate-400">
                    Side-by-side delta, entity drift, and confidence variance analysis.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setComparisonModalOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* AI Summary Banner */}
            <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs text-indigo-200 leading-relaxed font-mono">
              <strong className="text-cyan-400 uppercase tracking-wide block mb-1">
                Comparative Intelligence Summary:
              </strong>
              {comparisonResult.summary}
            </div>

            {/* Side-by-side run cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
              {/* Run A */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <span className="text-slate-400 font-bold">RUN A (Baseline)</span>
                  <span className="text-cyan-400">#{comparisonResult.run_a_id.slice(0, 8)}</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Mode:</span>
                    <span className="text-slate-200 uppercase">{comparisonResult.run_a_mode}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Status:</span>
                    <span className="text-emerald-400 uppercase">{comparisonResult.run_a_status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Avg Confidence:</span>
                    <span className="text-cyan-300 font-bold">{comparisonResult.average_confidence_a}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Started:</span>
                    <span className="text-slate-400">
                      {comparisonResult.run_a_date ? new Date(comparisonResult.run_a_date).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Run B */}
              <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <span className="text-slate-400 font-bold">RUN B (Comparison Target)</span>
                  <span className="text-indigo-400">#{comparisonResult.run_b_id.slice(0, 8)}</span>
                </div>
                <div className="space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Mode:</span>
                    <span className="text-slate-200 uppercase">{comparisonResult.run_b_mode}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Status:</span>
                    <span className="text-emerald-400 uppercase">{comparisonResult.run_b_status}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Avg Confidence:</span>
                    <span className="text-indigo-300 font-bold">{comparisonResult.average_confidence_b}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Started:</span>
                    <span className="text-slate-400">
                      {comparisonResult.run_b_date ? new Date(comparisonResult.run_b_date).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Differential Analytics Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">
                  Total Records Delta
                </span>
                <div className="flex items-center gap-1.5">
                  {comparisonResult.total_records_delta >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-rose-400" />
                  )}
                  <span
                    className={`text-lg font-bold font-mono ${
                      comparisonResult.total_records_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {comparisonResult.total_records_delta > 0 ? `+${comparisonResult.total_records_delta}` : comparisonResult.total_records_delta}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">
                  Valid Records Delta
                </span>
                <div className="flex items-center gap-1.5">
                  {comparisonResult.valid_records_delta >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-rose-400" />
                  )}
                  <span
                    className={`text-lg font-bold font-mono ${
                      comparisonResult.valid_records_delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                    }`}
                  >
                    {comparisonResult.valid_records_delta > 0 ? `+${comparisonResult.valid_records_delta}` : comparisonResult.valid_records_delta}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">
                  Confidence Shift
                </span>
                <div className="flex items-center gap-1.5">
                  {comparisonResult.confidence_delta >= 0 ? (
                    <TrendingUp className="w-4 h-4 text-cyan-400" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-amber-400" />
                  )}
                  <span
                    className={`text-lg font-bold font-mono ${
                      comparisonResult.confidence_delta >= 0 ? 'text-cyan-400' : 'text-amber-400'
                    }`}
                  >
                    {comparisonResult.confidence_delta > 0 ? `+${comparisonResult.confidence_delta}` : comparisonResult.confidence_delta}
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                <span className="text-[11px] text-slate-500 uppercase tracking-wider block">
                  Deduplication Delta
                </span>
                <span className="text-lg font-bold font-mono text-rose-400">
                  {comparisonResult.duplicate_records_delta > 0 ? `+${comparisonResult.duplicate_records_delta}` : comparisonResult.duplicate_records_delta}
                </span>
              </div>
            </div>

            {/* Entity Drift Breakdown */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800 space-y-3">
              <span className="text-xs font-bold text-white uppercase tracking-wider block">
                Entity Drift & Persistence Analysis
              </span>
              <div className="grid grid-cols-3 gap-3 text-center text-xs font-mono">
                <div className="p-3 rounded-lg bg-emerald-950/30 border border-emerald-500/20">
                  <span className="text-emerald-400 text-lg font-bold block">
                    {comparisonResult.new_records_count}
                  </span>
                  <span className="text-slate-400 text-[11px]">New In Run B</span>
                </div>
                <div className="p-3 rounded-lg bg-blue-950/30 border border-blue-500/20">
                  <span className="text-blue-400 text-lg font-bold block">
                    {comparisonResult.common_records_count}
                  </span>
                  <span className="text-slate-400 text-[11px]">Persistent Entities</span>
                </div>
                <div className="p-3 rounded-lg bg-rose-950/30 border border-rose-500/20">
                  <span className="text-rose-400 text-lg font-bold block">
                    {comparisonResult.removed_records_count}
                  </span>
                  <span className="text-slate-400 text-[11px]">Removed / Absent</span>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2 border-t border-slate-800">
              <button
                onClick={() => setComparisonModalOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
