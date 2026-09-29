'use client';

import React, { useMemo, useState, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  NodeTypes,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { WorkflowStepPlan, StepExecutionStatus } from '@/lib/types';
import { computeWorkflowGraph } from '@/lib/graph-layout';
import { CustomStepNode } from './CustomStepNode';
import { StepInspectorDrawer } from './StepInspectorDrawer';

interface WorkflowGraphProps {
  steps: WorkflowStepPlan[];
  stepStatuses?: StepExecutionStatus[];
  height?: string | number;
}

const nodeTypes: NodeTypes = {
  customStep: CustomStepNode as any,
};

const EMPTY_STATUSES: StepExecutionStatus[] = [];

export function WorkflowGraph({ steps, stepStatuses = EMPTY_STATUSES, height = '560px' }: WorkflowGraphProps) {
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  // Compute graph geometry
  const { nodes, edges } = useMemo(() => {
    return computeWorkflowGraph(steps, stepStatuses || EMPTY_STATUSES, selectedStepId);
  }, [steps, stepStatuses, selectedStepId]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedStepId(node.id);
  }, []);

  const selectedStep = useMemo(() => {
    if (!selectedStepId) return null;
    return steps.find((s) => s.id === selectedStepId) || null;
  }, [selectedStepId, steps]);

  const selectedStatus = useMemo(() => {
    if (!selectedStepId) return null;
    return (stepStatuses || EMPTY_STATUSES).find((s) => s.step_id === selectedStepId) || null;
  }, [selectedStepId, stepStatuses]);

  return (
    <div className="relative w-full rounded-2xl border border-slate-800 bg-slate-950 overflow-hidden shadow-2xl" style={{ height }}>
      {/* Visual Canvas Header */}
      <div className="absolute top-4 left-4 z-10 flex items-center gap-3 bg-slate-900/90 backdrop-blur-md px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs shadow-lg">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
        <span className="font-semibold text-slate-200">Interactive DAG Graph</span>
        <span className="text-slate-500">|</span>
        <span className="text-slate-400 font-mono">{steps.length} Steps</span>
        <span className="text-slate-500">|</span>
        <span className="text-slate-400">Click any node to inspect parameters</span>
      </div>

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={1.5}
        className="bg-slate-950"
      >
        <Background color="#1e293b" gap={24} size={1} />
        <Controls className="!bg-slate-900 !border-slate-800 !text-slate-300" />
        <MiniMap
          nodeColor="#3b82f6"
          maskColor="rgba(15, 23, 42, 0.7)"
          className="!bg-slate-900/90 !border-slate-800 !rounded-lg overflow-hidden hidden sm:block"
        />
      </ReactFlow>

      {/* Slide-over Inspector */}
      {selectedStep && (
        <StepInspectorDrawer
          step={selectedStep}
          statusInfo={selectedStatus}
          onClose={() => setSelectedStepId(null)}
        />
      )}
    </div>
  );
}
