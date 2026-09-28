import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.workflow import Workflow, WorkflowRun
from app.schemas.planner import (
    PlannerRequest,
    WorkflowResponse,
    PlannerOutput,
    FieldSpec,
    SourceSpec,
    WorkflowStepPlan,
    ValidationRuleSpec,
)
from app.schemas.execution import WorkflowRunStatus
from app.services.planner.planner_service import planner_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def workflow_to_response(wf: Workflow) -> WorkflowResponse:
    plan = PlannerOutput(
        goal=wf.goal,
        domain=wf.domain,
        target_record_count=len(wf.steps_spec),
        entities=wf.entities or [],
        fields=[FieldSpec(**f) for f in (wf.fields_spec or [])],
        sources=[SourceSpec(**s) for s in (wf.sources_spec or [])],
        steps=[WorkflowStepPlan(**st) for st in (wf.steps_spec or [])],
        validation_rules=[ValidationRuleSpec(**r) for r in (wf.validation_rules or [])],
        deduplication_strategy=wf.deduplication_strategy or "",
        deduplication_keys=[],
        reasoning=getattr(wf, 'reasoning', []) or [],
        output_format=wf.output_format or "table"
    )

    latest_run = wf.runs[0] if wf.runs else None

    return WorkflowResponse(
        id=wf.id,
        prompt=wf.prompt,
        plan=plan,
        created_at=wf.created_at,
        run_count=len(wf.runs),
        latest_run_id=latest_run.id if latest_run else None,
        latest_status=latest_run.status if latest_run else None
    )


@router.post("/plan", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def generate_workflow_plan(
    req: PlannerRequest,
    db: Session = Depends(get_db)
):
    """
    Takes natural language prompt and generates a structured, validated workflow plan DAG.
    Saves workflow to history and returns the full plan for visual preview.
    """
    try:
        wf = await planner_service.create_and_save_workflow(
            prompt=req.prompt,
            target_count=req.target_record_count or 30,
            db=db
        )
        return workflow_to_response(wf)
    except Exception as e:
        logger.error(f"Error generating workflow plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate workflow plan: {str(e)}"
        )


@router.get("", response_model=List[WorkflowResponse])
def list_workflows(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List historical workflows with latest execution status."""
    workflows = db.query(Workflow).order_by(desc(Workflow.created_at)).offset(skip).limit(limit).all()
    return [workflow_to_response(wf) for wf in workflows]


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve details and DAG plan of a specific workflow."""
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return workflow_to_response(wf)


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workflow(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Delete a workflow and its associated runs/datasets."""
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    db.delete(wf)
    db.commit()
    return None


@router.get("/{workflow_id}/runs", response_model=List[WorkflowRunStatus])
def list_workflow_runs(
    workflow_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve all historical execution runs for a specific workflow."""
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    from app.api.execution import run_to_status
    runs = db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).order_by(desc(WorkflowRun.started_at)).all()
    return [run_to_status(r) for r in runs]
