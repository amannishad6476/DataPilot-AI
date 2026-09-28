import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.workflow import Workflow, WorkflowRun
from app.schemas.execution import (
    RunWorkflowRequest,
    WorkflowRunStatus,
    StepExecutionStatus,
)
from app.services.engine.demo_executor import demo_executor
from app.services.engine.real_executor import real_executor

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
    db: Session = Depends(get_db)
):
    """
    Initiates execution of a planned workflow in background.
    Supports 'demo' (mock high-fidelity pipeline), 'real' (live permitted sources connector), and 'n8n' (webhook pipeline).
    """
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    run = WorkflowRun(
        workflow_id=workflow_id,
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


@router.get("/runs/{run_id}", response_model=WorkflowRunStatus)
def get_run_status(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Query live execution status, step progression, and metric counters."""
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found")
    return run_to_status(run)
