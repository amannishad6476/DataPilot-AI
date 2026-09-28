import { Node, Edge, MarkerType } from '@xyflow/react';
import { WorkflowStepPlan, StepExecutionStatus } from './types';

export interface WorkflowNodeData extends Record<string, unknown> {
  step: WorkflowStepPlan;
  status?: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  message?: string;
  records_produced?: number;
  progress_percent?: number;
  isSelected?: boolean;
}

export function computeWorkflowGraph(
  steps: WorkflowStepPlan[],
  stepStatuses: StepExecutionStatus[] = [],
  selectedStepId: string | null = null
): { nodes: Node<WorkflowNodeData>[]; edges: Edge[] } {
  const statusMap = new Map<string, StepExecutionStatus>();
  stepStatuses.forEach((s) => statusMap.set(s.step_id, s));

  // 1. Calculate DAG topological levels
  const stepMap = new Map<string, WorkflowStepPlan>();
  steps.forEach((s) => stepMap.set(s.id, s));

  const levels = new Map<string, number>();

  function getLevel(stepId: string, visited = new Set<string>()): number {
    if (visited.has(stepId)) return 0;
    visited.add(stepId);

    if (levels.has(stepId)) return levels.get(stepId)!;

    const step = stepMap.get(stepId);
    if (!step || !step.depends_on || step.depends_on.length === 0) {
      levels.set(stepId, 0);
      return 0;
    }

    let maxDepLevel = 0;
    for (const depId of step.depends_on) {
      maxDepLevel = Math.max(maxDepLevel, getLevel(depId, new Set(visited)) + 1);
    }

    levels.set(stepId, maxDepLevel);
    return maxDepLevel;
  }

  steps.forEach((s) => getLevel(s.id));

  // 2. Group nodes by level to position cleanly
  const levelGroups = new Map<number, WorkflowStepPlan[]>();
  steps.forEach((step) => {
    const lvl = levels.get(step.id) || 0;
    if (!levelGroups.has(lvl)) levelGroups.set(lvl, []);
    levelGroups.get(lvl)!.push(step);
  });

  const nodes: Node<WorkflowNodeData>[] = [];
  const X_SPACING = 360;
  const Y_SPACING = 170;

  levelGroups.forEach((groupSteps, lvl) => {
    const totalInLevel = groupSteps.length;
    const startY = -((totalInLevel - 1) * Y_SPACING) / 2 + 150;

    groupSteps.forEach((step, idx) => {
      const statusInfo = statusMap.get(step.id);
      nodes.push({
        id: step.id,
        type: 'customStep',
        position: {
          x: lvl * X_SPACING + 50,
          y: startY + idx * Y_SPACING,
        },
        data: {
          step,
          status: statusInfo?.status || 'pending',
          message: statusInfo?.message,
          records_produced: statusInfo?.records_produced || 0,
          progress_percent: statusInfo?.progress_percent || 0,
          isSelected: selectedStepId === step.id,
        },
      });
    });
  });

  // 3. Construct Edges
  const edges: Edge[] = [];
  steps.forEach((step) => {
    const targetStatus = statusMap.get(step.id)?.status;
    const isTargetRunning = targetStatus === 'running';
    const isTargetCompleted = targetStatus === 'completed';

    (step.depends_on || []).forEach((depId) => {
      const edgeId = `e-${depId}-${step.id}`;
      const sourceStatus = statusMap.get(depId)?.status;
      const isAnimated = isTargetRunning || (sourceStatus === 'completed' && targetStatus === 'pending');

      let strokeColor = '#334155'; // default slate-700
      if (isTargetCompleted) strokeColor = '#10b981'; // emerald-500
      else if (isTargetRunning) strokeColor = '#3b82f6'; // blue-500

      edges.push({
        id: edgeId,
        source: depId,
        target: step.id,
        animated: isAnimated,
        style: {
          stroke: strokeColor,
          strokeWidth: isTargetRunning ? 2.5 : 2,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: strokeColor,
          width: 16,
          height: 16,
        },
      });
    });
  });

  return { nodes, edges };
}
