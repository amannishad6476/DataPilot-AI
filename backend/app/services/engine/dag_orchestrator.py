import asyncio
import time
import uuid
import logging
from enum import Enum
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Callable, Awaitable
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class NodeState(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "completed"       # mapped to 'completed' for UI compatibility
    FAILED = "failed"
    RETRYING = "retrying"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"


class WorkflowNode:
    def __init__(self, step_spec: Dict[str, Any]):
        self.id: str = step_spec["id"]
        self.name: str = step_spec.get("name", self.id)
        self.type: str = step_spec.get("type", "transform")
        self.action: str = step_spec.get("action", "process")
        self.depends_on: List[str] = list(step_spec.get("depends_on", []))
        self.target_fields: List[str] = list(step_spec.get("target_fields", []))
        self.status: NodeState = NodeState.PENDING
        self.progress_percent: int = 0
        self.message: str = "Awaiting execution"
        self.records_produced: int = 0
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.error: Optional[str] = None
        self.retry_count: int = 0
        self.max_retries: int = 2
        self.timeout_sec: float = float(step_spec.get("timeout_sec", 30.0))
        self.duration_ms: float = 0.0

    def to_status_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.id,
            "step_name": self.name,
            "step_type": self.type,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "message": self.message,
            "records_produced": self.records_produced,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error": self.error,
            "retry_count": self.retry_count,
            "duration_ms": self.duration_ms
        }


class DagOrchestrator:
    """
    Production Dependency-Aware DAG Workflow Orchestrator.
    - Resolves dependency hierarchy (depends_on).
    - Safely executes independent sibling nodes in parallel using asyncio.gather.
    - Supports node states: PENDING, QUEUED, RUNNING, SUCCEEDED, FAILED, RETRYING, SKIPPED, CANCELLED.
    - Isolates failures: failed nodes do not invalidate independent branches.
    """

    def __init__(self, steps_spec: List[Dict[str, Any]]):
        self.nodes: Dict[str, WorkflowNode] = {
            s["id"]: WorkflowNode(s) for s in steps_spec
        }
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        for node in self.nodes.values():
            if node.status in [NodeState.PENDING, NodeState.QUEUED]:
                node.status = NodeState.CANCELLED
                node.message = "Cancelled by user"

    def get_execution_waves(self) -> List[List[WorkflowNode]]:
        """
        Organizes nodes into parallel execution waves using topological leveling.
        Nodes in the same wave have no dependencies on each other and can be executed concurrently.
        """
        resolved: Set[str] = set()
        waves: List[List[WorkflowNode]] = []
        remaining = dict(self.nodes)

        while remaining:
            # Find all nodes whose dependencies are already resolved
            ready_wave = [
                node for node in remaining.values()
                if all(dep in resolved for dep in node.depends_on)
            ]

            if not ready_wave:
                # Cyclic or disconnected dependency fallback: take first remaining
                logger.warning("No clean ready nodes; cycle or unknown dependency encountered. Taking first node.")
                ready_wave = [next(iter(remaining.values()))]

            waves.append(ready_wave)
            for node in ready_wave:
                resolved.add(node.id)
                del remaining[node.id]

        return waves

    async def execute_wave(
        self,
        wave: List[WorkflowNode],
        node_executor_fn: Callable[[WorkflowNode], Awaitable[Any]],
        on_node_update: Optional[Callable[[WorkflowNode], None]] = None
    ) -> None:
        """Executes independent nodes in a wave concurrently."""
        tasks = []
        for node in wave:
            if self.cancelled:
                node.status = NodeState.CANCELLED
                node.message = "Execution cancelled"
                continue

            # Check if any dependency failed
            dep_failed = any(
                self.nodes[dep].status in [NodeState.FAILED, NodeState.SKIPPED, NodeState.CANCELLED]
                for dep in node.depends_on if dep in self.nodes
            )
            if dep_failed:
                node.status = NodeState.SKIPPED
                node.message = "Skipped due to upstream dependency failure"
                if on_node_update:
                    on_node_update(node)
                continue

            tasks.append(self._run_single_node(node, node_executor_fn, on_node_update))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_single_node(
        self,
        node: WorkflowNode,
        node_executor_fn: Callable[[WorkflowNode], Awaitable[Any]],
        on_node_update: Optional[Callable[[WorkflowNode], None]] = None
    ) -> None:
        node.status = NodeState.RUNNING
        node.started_at = datetime.now(timezone.utc).isoformat()
        node.progress_percent = 50
        node.message = f"Executing {node.name}..."
        if on_node_update:
            on_node_update(node)

        t0 = time.perf_counter()
        attempt = 0
        backoff = 0.5

        while attempt <= node.max_retries:
            try:
                # Execute with timeout
                await asyncio.wait_for(node_executor_fn(node), timeout=node.timeout_sec)
                node.status = NodeState.SUCCEEDED
                node.progress_percent = 100
                node.message = f"Completed {node.name} successfully"
                node.completed_at = datetime.now(timezone.utc).isoformat()
                node.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                if on_node_update:
                    on_node_update(node)
                return
            except Exception as e:
                attempt += 1
                node.retry_count = attempt
                if attempt <= node.max_retries and not self.cancelled:
                    node.status = NodeState.RETRYING
                    node.message = f"Retry {attempt}/{node.max_retries} after error: {e}"
                    if on_node_update:
                        on_node_update(node)
                    await asyncio.sleep(backoff)
                    backoff *= 2
                else:
                    node.status = NodeState.FAILED
                    node.error = str(e)
                    node.message = f"Failed: {e}"
                    node.completed_at = datetime.now(timezone.utc).isoformat()
                    node.duration_ms = round((time.perf_counter() - t0) * 1000, 2)
                    if on_node_update:
                        on_node_update(node)
                    return
