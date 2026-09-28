'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps, Node } from '@xyflow/react';
import {
  Terminal,
  Cpu,
  Globe,
  Database,
  RefreshCw,
  ShieldCheck,
  GitMerge,
  Layers,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
} from 'lucide-react';
import { WorkflowNodeData } from '@/lib/graph-layout';
import { StepType, WorkflowStepPlan } from '@/lib/types';

export type CustomStepNodeType = Node<WorkflowNodeData, 'customStep'>;

const STEP_ICONS: Record<StepType, React.ElementType> = {
  input: Terminal,
  ai_planning: Cpu,
  source_discovery: Globe,
  extraction: Database,
  transformation: RefreshCw,
  validation: ShieldCheck,
  deduplication: GitMerge,
  merge: Layers,
  output: CheckCircle2,
};

const STEP_COLORS: Record<StepType, { bg: string; border: string; badge: string; icon: string }> = {
  input: {
    bg: 'from-blue-950/40 to-slate-900/80',
    border: 'border-blue-500/30 hover:border-blue-500',
    badge: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    icon: 'text-blue-400',
  },
  ai_planning: {
    bg: 'from-purple-950/40 to-slate-900/80',
    border: 'border-purple-500/30 hover:border-purple-500',
    badge: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    icon: 'text-purple-400',
  },
  source_discovery: {
    bg: 'from-cyan-950/40 to-slate-900/80',
    border: 'border-cyan-500/30 hover:border-cyan-500',
    badge: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
    icon: 'text-cyan-400',
  },
  extraction: {
    bg: 'from-amber-950/40 to-slate-900/80',
    border: 'border-amber-500/30 hover:border-amber-500',
    badge: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    icon: 'text-amber-400',
  },
  transformation: {
    bg: 'from-teal-950/40 to-slate-900/80',
    border: 'border-teal-500/30 hover:border-teal-500',
    badge: 'bg-teal-500/10 text-teal-400 border-teal-500/20',
    icon: 'text-teal-400',
  },
  validation: {
    bg: 'from-emerald-950/40 to-slate-900/80',
    border: 'border-emerald-500/30 hover:border-emerald-500',
    badge: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    icon: 'text-emerald-400',
  },
  deduplication: {
    bg: 'from-rose-950/40 to-slate-900/80',
    border: 'border-rose-500/30 hover:border-rose-500',
    badge: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    icon: 'text-rose-400',
  },
  merge: {
    bg: 'from-indigo-950/40 to-slate-900/80',
    border: 'border-indigo-500/30 hover:border-indigo-500',
    badge: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
    icon: 'text-indigo-400',
  },
  output: {
    bg: 'from-violet-950/40 to-slate-900/80',
    border: 'border-violet-500/30 hover:border-violet-500',
    badge: 'bg-violet-500/10 text-violet-400 border-violet-500/20',
    icon: 'text-violet-400',
  },
};

export const CustomStepNode = memo(({ data }: NodeProps<CustomStepNodeType>) => {
  const step = data.step as WorkflowStepPlan;
  const status = data.status || 'pending';
  const records_produced = data.records_produced || 0;
  const isSelected = data.isSelected;

  const colors = STEP_COLORS[step.type as StepType] || STEP_COLORS.extraction;
  const Icon = STEP_ICONS[step.type as StepType] || Database;

  const isRunning = status === 'running';
  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';

  return (
    <div
      className={`relative w-72 rounded-xl border bg-gradient-to-b ${colors.bg} p-4 shadow-xl backdrop-blur-md transition-all duration-200 ${
        isSelected
          ? 'ring-2 ring-cyan-400 border-cyan-400 shadow-cyan-500/20'
          : isRunning
          ? 'ring-2 ring-blue-500 border-blue-400 shadow-blue-500/20 animate-pulse'
          : isCompleted
          ? 'border-emerald-500/50 shadow-emerald-500/10'
          : colors.border
      }`}
    >
      {/* Target handle on left */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 !bg-slate-700 !border-2 !border-slate-400 rounded-full hover:!bg-cyan-400 transition-colors"
      />

      {/* Header: Icon + Category Badge + Live Status */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 rounded-lg bg-slate-900/80 border border-slate-700/50 ${colors.icon}`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className={`text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full border ${colors.badge}`}>
            {step.type.replace('_', ' ')}
          </span>
        </div>

        {/* Status Indicator */}
        <div>
          {isRunning && (
            <span className="flex items-center gap-1 text-[11px] font-semibold text-blue-400">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Running
            </span>
          )}
          {isCompleted && (
            <span className="flex items-center gap-1 text-[11px] font-semibold text-emerald-400">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Done
            </span>
          )}
          {isFailed && (
            <span className="flex items-center gap-1 text-[11px] font-semibold text-rose-400">
              <AlertCircle className="w-3.5 h-3.5" />
              Failed
            </span>
          )}
          {status === 'pending' && (
            <span className="flex items-center gap-1 text-[11px] text-slate-400 font-mono">
              <Clock className="w-3 h-3 text-slate-500" />
              Pending
            </span>
          )}
        </div>
      </div>

      {/* Step Title */}
      <h3 className="text-sm font-semibold text-white tracking-tight mb-1 truncate">
        {step.name}
      </h3>

      {/* Description */}
      <p className="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">
        {step.description}
      </p>

      {/* Footer Info: Action name & records count */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
        <span className="font-mono text-slate-400 truncate max-w-[140px]" title={step.action}>
          {step.action}
        </span>

        {records_produced > 0 && (
          <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-mono font-medium border border-emerald-500/20">
            {records_produced} records
          </span>
        )}
      </div>

      {/* Source handle on right */}
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 !bg-slate-700 !border-2 !border-slate-400 rounded-full hover:!bg-cyan-400 transition-colors"
      />
    </div>
  );
});

CustomStepNode.displayName = 'CustomStepNode';
