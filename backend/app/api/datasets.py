import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import DatasetRecord
from app.models.workflow import WorkflowRun
from app.schemas.dataset import DatasetResponse, EvidenceItem
from app.services.storage.dataset_service import dataset_service
from app.core.security import get_current_user, UserContext

router = APIRouter(tags=["Datasets"])


@router.get("/runs/{run_id}/dataset", response_model=DatasetResponse)
def get_run_dataset(
    run_id: str,
    search: Optional[str] = Query(None, description="Search term across all columns"),
    valid_filter: Optional[str] = Query("all", pattern="^(all|valid|invalid)$", description="Filter records by validity"),
    confidence_filter: Optional[str] = Query(None, description="Filter by confidence level: all, HIGH, MEDIUM, LOW"),
    evidence_filter: Optional[str] = Query(None, description="Filter by evidence presence: all, AVAILABLE, MISSING"),
    sort_by: Optional[str] = Query(None, description="Field name or metric to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sorting direction"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Records per page"),
    db: Session = Depends(get_db),
    user: UserContext = Depends(get_current_user)
):
    """
    Retrieve structured records produced by a run, with search, validity filtering,
    dynamic sorting, confidence filtering, and full evidence linkages.
    """
    run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"WorkflowRun {run_id} not found")
    if user.tenant_id != "*" and run.tenant_id != user.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to dataset outside tenant")

    try:
        return dataset_service.get_dataset(
            db=db,
            run_id=run_id,
            search=search,
            valid_filter=valid_filter,
            confidence_filter=confidence_filter,
            evidence_filter=evidence_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=page_size
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))



@router.get("/runs/{run_id}/export/csv")
def export_dataset_csv(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Export dataset as RFC-compliant CSV with header row and quality metadata using memory-efficient streaming."""
    from fastapi.responses import StreamingResponse
    try:
        # Validate existence
        from app.models.workflow import WorkflowRun
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"WorkflowRun {run_id} not found")

        filename = f"datapilot_dataset_{run_id[:8]}.csv"
        return StreamingResponse(
            dataset_service.stream_csv(db, run_id),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/runs/{run_id}/export/json")
def export_dataset_json(
    run_id: str,
    db: Session = Depends(get_db)
):
    """Export dataset as structured JSON stream array with field values and quality scores."""
    from fastapi.responses import StreamingResponse
    try:
        from app.models.workflow import WorkflowRun
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"WorkflowRun {run_id} not found")

        filename = f"datapilot_dataset_{run_id[:8]}.json"
        return StreamingResponse(
            dataset_service.stream_json(db, run_id),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/records/{record_id}/evidence", response_model=List[EvidenceItem])
def get_record_evidence(
    record_id: str,
    db: Session = Depends(get_db)
):
    """Retrieve full audit trail and evidence citations for a specific record."""
    record = db.query(DatasetRecord).filter(DatasetRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")

    return [
        EvidenceItem(
            id=e.id,
            field_name=e.field_name,
            source_url=e.source_url,
            snippet=e.snippet,
            confidence=e.confidence,
            collected_at=e.collected_at
        )
        for e in record.evidence_items
    ]
