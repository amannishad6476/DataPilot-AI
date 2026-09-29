import asyncio
import logging
import uuid
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db, SessionLocal
from app.models.workflow import Workflow, WorkflowRun
from app.models.dataset import DatasetRecord
from app.schemas.execution import (
    RunWorkflowRequest,
    WorkflowRunStatus,
    StepExecutionStatus,
    TimelineEvent,
    RunComparisonResponse,
    SourceHealthReport,
)
from app.schemas.dataset import DataQualitySummary
from app.services.engine.demo_executor import demo_executor
from app.services.engine.real_executor import real_executor
from app.services.connectors.registry import connector_registry
from app.core.security import get_current_user, require_role, Role, UserContext
from app.core.audit import record_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Execution"])



def run_to_status(run: WorkflowRun) -> WorkflowRunStatus:
    raw_step_statuses = run.step_statuses or []
    step_models = [StepExecutionStatus(**s) for s in raw_step_statuses]

    total_steps = len(step_models)
    completed_steps = sum(1 for s in step_models if s.status == "completed")
    running_step = next((s for s in step_models if s.status == "running"), None)

    progress_percent = 0
    if run.status == "completed":
        progress_percent = 100
    elif total_steps > 0:
        progress_percent = int((completed_steps / total_steps) * 100)
        if running_step and progress_percent < 95:
            progress_percent += int(100 / (total_steps * 2))

    timeline_models = [TimelineEvent(**t) for t in (run.execution_timeline or [])]

    return WorkflowRunStatus(
        run_id=run.id,
        workflow_id=run.workflow_id,
        status=run.status,
        execution_mode=run.execution_mode,
        total_records=run.total_records,
        valid_records=run.valid_records,
        duplicate_records=run.duplicate_records,
        progress_percent=min(100, progress_percent),
        current_step_id=running_step.step_id if running_step else None,
        step_statuses=step_models,
        execution_timeline=timeline_models,
        quality_summary=run.quality_summary or None,
        source_health_summary=run.source_health_summary or None,
        error_message=run.error_message,
        started_at=run.started_at,
        completed_at=run.completed_at
    )


async def execute_in_background(
    workflow_id: str,
    run_id: str,
    mode: str,
    target_url: Optional[str] = None,
    n8n_webhook_url: Optional[str] = None
):
    """Background runner with isolated DB session."""
    db = SessionLocal()
    try:
        wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not wf or not run:
            logger.error(f"Cannot execute run {run_id}: Workflow or Run missing in DB")
            return

        if mode in ["real", "n8n"]:
            await real_executor.execute(
                wf, run, db, target_url=target_url, n8n_webhook_url=n8n_webhook_url
            )
        else:
            await demo_executor.execute(wf, run, db)
    except Exception as e:
        logger.error(f"Run {run_id} execution failed: {e}", exc_info=True)
        try:
            run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
            if run:
                run.status = "failed"
                run.error_message = str(e)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@router.post("/workflows/{workflow_id}/run", response_model=WorkflowRunStatus, status_code=status.HTTP_202_ACCEPTED)
async def start_workflow_run(
    workflow_id: str,
    req: RunWorkflowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """
    Initiates execution of a planned workflow in background.
    Supports 'demo' (mock high-fidelity pipeline), 'real' (live permitted sources connector), and 'n8n' (webhook pipeline).
    """
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    if user.tenant_id != "*" and wf.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to workflow outside tenant")

    run = WorkflowRun(
        workflow_id=workflow_id,
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        execution_mode=req.execution_mode,
        status="pending",
        total_records=0,
        valid_records=0,
        duplicate_records=0,
        step_statuses=[]
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    record_audit_event(
        db,
        event_type="RUN_STARTED",
        resource_type="workflow_run",
        resource_id=run.id,
        action="start_run",
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        details={"mode": req.execution_mode, "workflow_id": workflow_id}
    )

    # Schedule asynchronous execution
    background_tasks.add_task(
        execute_in_background,
        workflow_id,
        run.id,
        req.execution_mode,
        req.target_url,
        req.n8n_webhook_url
    )

    return run_to_status(run)


@router.get("/runs/compare", response_model=RunComparisonResponse)
def compare_runs(
    run_a: str = Query(..., description="Baseline Run ID"),
    run_b: str = Query(..., description="Target Run ID to compare against"),
    db: Session = Depends(get_db)
):
    """
    Compare two execution runs side-by-side to highlight data drift,
    new entities discovered, confidence score variance, and deduplication efficiency.
    """
    obj_a = db.query(WorkflowRun).filter(WorkflowRun.id == run_a).first()
    obj_b = db.query(WorkflowRun).filter(WorkflowRun.id == run_b).first()

    if not obj_a:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Baseline run {run_a} not found")
    if not obj_b:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Comparison run {run_b} not found")

    recs_a = db.query(DatasetRecord).filter(DatasetRecord.run_id == run_a).all()
    recs_b = db.query(DatasetRecord).filter(DatasetRecord.run_id == run_b).all()

    avg_a = round(sum(r.confidence_score for r in recs_a) / max(1, len(recs_a)), 2) if recs_a else 0.0
    avg_b = round(sum(r.confidence_score for r in recs_b) / max(1, len(recs_b)), 2) if recs_b else 0.0

    def extract_entity_key(r: DatasetRecord) -> str:
        for k in ["company_name", "title", "name", "website", "apply_link"]:
            if r.data.get(k):
                return str(r.data.get(k)).strip().lower()
        return r.id

    keys_a = {extract_entity_key(r) for r in recs_a}
    keys_b = {extract_entity_key(r) for r in recs_b}

    common_keys = keys_a.intersection(keys_b)
    new_keys = keys_b - keys_a
    removed_keys = keys_a - keys_b

    summary = (
        f"Compared Run A ({obj_a.execution_mode}, {len(recs_a)} records) against "
        f"Run B ({obj_b.execution_mode}, {len(recs_b)} records). "
        f"Found {len(new_keys)} new entities in Run B, {len(common_keys)} persistent entities, "
        f"and {len(removed_keys)} entities absent in Run B. "
        f"Confidence shifted by {round(avg_b - avg_a, 2):+}."
    )

    return RunComparisonResponse(
        run_a_id=obj_a.id,
        run_b_id=obj_b.id,
        run_a_mode=obj_a.execution_mode,
        run_b_mode=obj_b.execution_mode,
        run_a_status=obj_a.status,
        run_b_status=obj_b.status,
        run_a_date=obj_a.started_at.isoformat() if obj_a.started_at else None,
        run_b_date=obj_b.started_at.isoformat() if obj_b.started_at else None,
        total_records_delta=obj_b.total_records - obj_a.total_records,
        valid_records_delta=obj_b.valid_records - obj_a.valid_records,
        duplicate_records_delta=obj_b.duplicate_records - obj_a.duplicate_records,
        average_confidence_a=avg_a,
        average_confidence_b=avg_b,
        confidence_delta=round(avg_b - avg_a, 2),
        new_records_count=len(new_keys),
        common_records_count=len(common_keys),
        removed_records_count=len(removed_keys),
        summary=summary
    )


@router.get("/connectors/health", response_model=SourceHealthReport)
def get_connectors_health():
    """Returns actual operational metrics and health status for registered connectors."""
    return SourceHealthReport(**connector_registry.get_health_report())


@router.get("/runs", response_model=List[WorkflowRunStatus])
def list_all_runs(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Retrieve all historical execution runs across workflows within the user tenant."""
    query = db.query(WorkflowRun)
    if user.tenant_id != "*":
        query = query.filter(WorkflowRun.tenant_id == user.tenant_id)
    runs = query.order_by(desc(WorkflowRun.started_at)).offset(skip).limit(limit).all()
    return [run_to_status(r) for r in runs]


@router.get("/runs/{run_id}", response_model=WorkflowRunStatus)
def get_run_status(
    run_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Query live execution status, step progression, and metric counters."""
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    if user.tenant_id != "*" and run.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to run outside tenant")
    return run_to_status(run)


@router.post("/runs/{run_id}/rerun", response_model=WorkflowRunStatus, status_code=status.HTTP_202_ACCEPTED)
async def rerun_workflow(
    run_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """
    Reruns an existing workflow execution by spawning a NEW run instance with fresh ID.
    Preserves historical runs while capturing updated live metrics.
    """
    prior_run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not prior_run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original run not found to rerun")
    if user.tenant_id != "*" and prior_run.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to run outside tenant")

    workflow = db.query(Workflow).filter(Workflow.id == prior_run.workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated workflow not found")

    new_run = WorkflowRun(
        workflow_id=workflow.id,
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        execution_mode=prior_run.execution_mode,
        status="pending",
        total_records=0,
        valid_records=0,
        duplicate_records=0,
        step_statuses=[]
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)

    record_audit_event(
        db,
        event_type="RUN_RERUN",
        resource_type="workflow_run",
        resource_id=new_run.id,
        action="rerun",
        tenant_id=user.tenant_id,
        user_id=user.user_id,
        details={"prior_run_id": run_id, "workflow_id": workflow.id}
    )

    background_tasks.add_task(
        execute_in_background,
        workflow.id,
        new_run.id,
        new_run.execution_mode
    )

    return run_to_status(new_run)


@router.post("/runs/{run_id}/cancel", response_model=WorkflowRunStatus)
def cancel_workflow_run(
    run_id: str,
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """Gracefully cancel an ongoing or queued workflow execution."""
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    if user.tenant_id != "*" and run.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to run outside tenant")

    if run.status in ["completed", "failed", "cancelled"]:
        return run_to_status(run)

    run.status = "cancelled"
    timeline = list(run.execution_timeline or [])
    timeline.append({
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "step_id": None,
        "stage": "cancellation",
        "level": "warning",
        "message": "Execution halted by user request.",
        "details": {"action": "manual_cancellation"}
    })
    run.execution_timeline = timeline
    db.commit()
    db.refresh(run)

    record_audit_event(
        db,
        event_type="RUN_CANCELLED",
        resource_type="workflow_run",
        resource_id=run.id,
        action="cancel",
        tenant_id=user.tenant_id,
        user_id=user.user_id
    )

    return run_to_status(run)



@router.get("/runs/{run_id}/timeline", response_model=List[TimelineEvent])
def get_run_timeline(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve full audit stream of execution timeline events."""
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    raw_events = run.execution_timeline or []
    return [TimelineEvent(**ev) for ev in raw_events]


@router.get("/runs/{run_id}/quality", response_model=DataQualitySummary)
def get_run_quality_summary(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve detailed Data Quality Summary for an executed run."""
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")

    if run.quality_summary:
        return DataQualitySummary(**run.quality_summary)

    # Compute on the fly if not cached
    records = db.query(DatasetRecord).filter(DatasetRecord.run_id == run_id).all()
    total_eval = len(records)
    valid_cnt = sum(1 for r in records if r.is_valid)
    conf_breakdown = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    issues = []
    for r in records:
        lvl = r.confidence_level or ("HIGH" if r.confidence_score >= 0.85 else "MEDIUM" if r.confidence_score >= 0.70 else "LOW")
        conf_breakdown[lvl] = conf_breakdown.get(lvl, 0) + 1
        for err in (r.validation_errors or []):
            if err not in issues:
                issues.append(err)

    return DataQualitySummary(
        total_evaluated=total_eval,
        valid_count=valid_cnt,
        valid_rate_percent=round((valid_cnt / max(1, total_eval)) * 100, 1),
        field_completion_rates={},
        confidence_breakdown=conf_breakdown,
        average_confidence=round(sum(r.confidence_score for r in records) / max(1, total_eval), 2) if records else 1.0,
        evidence_coverage_percent=100.0 if records else 0.0,
        deduplication_reduction_percent=round((run.duplicate_records / max(1, total_eval + run.duplicate_records)) * 100, 1),
        issues_found=issues
    )
