'use client';

import React from 'react';
import { X, ArrowRight, Clock, Database, Layers, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { WorkflowStepPlan, StepExecutionStatus } from '@/lib/types';

interface StepInspectorDrawerProps {
  step: WorkflowStepPlan | null;
  statusInfo?: StepExecutionStatus | null;
  onClose: () => void;
}

export function StepInspectorDrawer({ step, statusInfo, onClose }: StepInspectorDrawerProps) {
  if (!step) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-slate-900 border-l border-slate-800 shadow-2xl z-40 p-6 flex flex-col justify-between overflow-y-auto">
      <div>
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              {step.type.replace('_', ' ')}
            </span>
            <span className="text-xs text-slate-500 font-mono">
              ID: {step.id}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Title */}
        <div className="mt-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
            {step.name}
          </h2>
          <p className="mt-2 text-sm text-slate-300 leading-relaxed">
            {step.description}
          </p>
        </div>

        {/* Live Status if available */}
        {statusInfo && (
          <div className="mt-5 p-3 rounded-xl bg-slate-950 border border-slate-800">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Execution Status
              </span>
              <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                statusInfo.status === 'completed'
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : statusInfo.status === 'running'
                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  : statusInfo.status === 'failed'
                  ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {statusInfo.status}
              </span>
            </div>
            <p className="text-xs text-slate-300 font-mono">
              {statusInfo.message}
            </p>
            {statusInfo.records_produced > 0 && (
              <p className="mt-2 text-xs font-semibold text-emerald-400">
                ✓ {statusInfo.records_produced} records processed in this stage
              </p>
            )}
          </div>
        )}

        {/* Technical Metadata */}
        <div className="mt-6 space-y-4">
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Engine Action
            </h4>
            <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs text-cyan-300">
              {step.action}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Upstream Dependencies
            </h4>
            {step.depends_on && step.depends_on.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {step.depends_on.map((dep) => (
                  <span
                    key={dep}
                    className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300"
                  >
                    <ArrowRight className="w-3 h-3 text-indigo-400" />
                    {dep}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-xs text-slate-500 italic">None (Root entry node)</span>
            )}
          </div>

          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Target Field Attributes
            </h4>
            {step.target_fields && step.target_fields.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {step.target_fields.map((f) => (
                  <span
                    key={f}
                    className="px-2 py-1 rounded bg-indigo-500/10 border border-indigo-500/20 text-xs font-mono text-indigo-300"
                  >
                    {f}
                  </span>
                ))}
              </div>
            ) : (
              <span className="text-xs text-slate-500 italic">Pipeline control / coordination</span>
            )}
          </div>

          <div className="flex items-center gap-2 pt-2 text-xs text-slate-400">
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Estimated runtime: ~{step.estimated_duration_sec}s</span>
          </div>
        </div>
      </div>

      <div className="pt-4 border-t border-slate-800">
        <button
          onClick={onClose}
          className="w-full py-2 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-colors"
        >
          Close Inspector
        </button>
      </div>
    </div>
  );
}
