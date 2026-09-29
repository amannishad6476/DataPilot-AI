import pytest
import asyncio
from app.services.engine.dag_orchestrator import DagOrchestrator, NodeState, WorkflowNode


@pytest.mark.asyncio
async def test_topological_waves():
    # step_1 -> step_2a, step_2b -> step_3
    steps = [
        {"id": "step_1", "name": "Input", "depends_on": []},
        {"id": "step_2a", "name": "Branch A", "depends_on": ["step_1"]},
        {"id": "step_2b", "name": "Branch B", "depends_on": ["step_1"]},
        {"id": "step_3", "name": "Merge", "depends_on": ["step_2a", "step_2b"]},
    ]
    orchestrator = DagOrchestrator(steps)
    waves = orchestrator.get_execution_waves()

    assert len(waves) == 3
    # Wave 0: step_1
    assert [n.id for n in waves[0]] == ["step_1"]
    # Wave 1: step_2a and step_2b in parallel
    wave_1_ids = {n.id for n in waves[1]}
    assert wave_1_ids == {"step_2a", "step_2b"}
    # Wave 2: step_3
    assert [n.id for n in waves[2]] == ["step_3"]


@pytest.mark.asyncio
async def test_wave_execution_parallelism():
    steps = [
        {"id": "step_a", "name": "Task A", "depends_on": []},
        {"id": "step_b", "name": "Task B", "depends_on": []},
    ]
    orchestrator = DagOrchestrator(steps)
    waves = orchestrator.get_execution_waves()
    assert len(waves) == 1

    executed = []

    async def mock_runner(node: WorkflowNode):
        await asyncio.sleep(0.05)
        executed.append(node.id)

    await orchestrator.execute_wave(waves[0], mock_runner)

    assert set(executed) == {"step_a", "step_b"}
    assert orchestrator.nodes["step_a"].status == NodeState.SUCCEEDED
    assert orchestrator.nodes["step_b"].status == NodeState.SUCCEEDED


@pytest.mark.asyncio
async def test_dependency_failure_cascade():
    steps = [
        {"id": "step_fail", "name": "Failing Task", "depends_on": []},
        {"id": "step_downstream", "name": "Downstream Task", "depends_on": ["step_fail"]},
    ]
    orchestrator = DagOrchestrator(steps)
    waves = orchestrator.get_execution_waves()

    async def fail_runner(node: WorkflowNode):
        if node.id == "step_fail":
            raise RuntimeError("Database connection crashed")

    # Run wave 0 (failing step)
    await orchestrator.execute_wave(waves[0], fail_runner)
    assert orchestrator.nodes["step_fail"].status == NodeState.FAILED

    # Run wave 1 (downstream step should be skipped)
    await orchestrator.execute_wave(waves[1], fail_runner)
    assert orchestrator.nodes["step_downstream"].status == NodeState.SKIPPED
    assert "upstream dependency failure" in orchestrator.nodes["step_downstream"].message
