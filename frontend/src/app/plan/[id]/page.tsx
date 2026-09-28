'use client';

import React, { useEffect, useState, use } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowLeft,
  Play,
  Layers,
  ShieldCheck,
  GitMerge,
  Globe,
  Database,
  Loader2,
  AlertCircle,
  Sparkles,
} from 'lucide-react';
import { api } from '@/lib/api';
import { WorkflowResponse } from '@/lib/types';
import { WorkflowGraph } from '@/components/workflow/WorkflowGraph';

export default function WorkflowPlanPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter();
  const resolvedParams = use(params);
  const workflowId = resolvedParams.id;

  const [workflow, setWorkflow] = useState<WorkflowResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executionMode, setExecutionMode] = useState<'demo' | 'real'>('demo');
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    async function loadWorkflow() {
      try {
        const wf = await api.getWorkflow(workflowId);
        setWorkflow(wf);
      } catch (err: any) {
        setError(err.message || 'Failed to load workflow');
      } finally {
        setLoading(false);
      }
    }
    loadWorkflow();
  }, [workflowId]);

  const handleRunWorkflow = async () => {
    if (isRunning) return;
    setIsRunning(true);
    try {
      const runStatus = await api.runWorkflow(workflowId, executionMode);
      router.push(`/execution/${runStatus.run_id}`);
    } catch (err: any) {
      alert(`Execution failed to start: ${err.message}`);
      setIsRunning(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <Loader2 className="w-8 h-8 animate-spin text-cyan-400" />
        <p className="text-sm text-slate-400 font-mono">Loading DAG Workflow Architecture...</p>
      </div>
    );
  }

  if (error || !workflow) {
    return (
      <div className="max-w-xl mx-auto my-12 p-6 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-center space-y-4">
        <AlertCircle className="w-10 h-10 text-rose-400 mx-auto" />
        <h2 className="text-lg font-bold text-white">Workflow Not Found</h2>
        <p className="text-xs text-rose-200">{error || 'Unable to retrieve workflow details.'}</p>
        <Link
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800 text-xs font-semibold text-white hover:bg-slate-700"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Pipeline Studio
        </Link>
      </div>
    );
  }

  const { plan } = workflow;

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Top Navigation & Action Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div className="space-y-1.5">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-cyan-400 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Studio</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Dynamic Workflow Architecture
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              {plan.domain.replace(/_/g, ' ')}
            </span>
          </div>
          <p className="text-xs text-slate-400 max-w-3xl line-clamp-1 italic">
            &ldquo;{workflow.prompt}&rdquo;
          </p>
        </div>

        {/* Execution Mode & Run CTA */}
        <div className="flex items-center gap-3">
          <div className="flex items-center bg-slate-900 border border-slate-800 p-1 rounded-xl text-xs">
            <button
              onClick={() => setExecutionMode('demo')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                executionMode === 'demo'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Demo Sandbox
            </button>
            <button
              onClick={() => setExecutionMode('real')}
              className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
                executionMode === 'real'
                  ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Live Engine
            </button>
          </div>

          <button
            onClick={handleRunWorkflow}
            disabled={isRunning}
            className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/25 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Launching...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-slate-950" />
                <span>Run Workflow</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* React Flow Interactive Graph */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span className="font-semibold uppercase tracking-wider text-slate-300">
            Pipeline DAG Visualization (Generated by LLM Planner)
          </span>
          <span>{plan.steps.length} Nodes &bull; Click node to inspect details</span>
        </div>
        <WorkflowGraph steps={plan.steps} height="520px" />
      </div>

      {/* Metadata Grids */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
        {/* Inferred Fields */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
            <Database className="w-4 h-4 text-cyan-400" />
            <span>Extracted Field Schema ({plan.fields.length})</span>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {plan.fields.map((f) => (
              <div
                key={f.name}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs"
              >
                <div>
                  <span className="font-mono text-slate-200">{f.name}</span>
                  {f.description && (
                    <p className="text-[10px] text-slate-500">{f.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                    {f.type}
                  </span>
                  {f.required && (
                    <span className="text-[10px] text-rose-400 font-bold">*</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Validation Rules */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-3">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Validation Checks ({plan.validation_rules.length})</span>
          </div>

          <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
            {plan.validation_rules.map((rule, idx) => (
              <div
                key={idx}
                className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-emerald-400 text-[11px] font-semibold">
                    {rule.field}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 font-mono">
                    {rule.rule_type}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-tight">
                  {rule.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Deduplication & Sources */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              <GitMerge className="w-4 h-4 text-rose-400" />
              <span>Deduplication Strategy</span>
            </div>
            <p className="text-xs text-slate-300 bg-slate-950/80 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed font-sans">
              {plan.deduplication_strategy}
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              <Globe className="w-4 h-4 text-indigo-400" />
              <span>Permitted Public Sources ({plan.sources.length})</span>
            </div>
            <div className="space-y-1.5">
              {plan.sources.map((s) => (
                <div
                  key={s.id}
                  className="p-2 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs flex justify-between items-center"
                >
                  <span className="text-slate-300 font-medium">{s.name}</span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 font-mono">
                    {s.type}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
