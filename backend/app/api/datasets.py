import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import DatasetRecord
from app.schemas.dataset import DatasetResponse, EvidenceItem
from app.services.storage.dataset_service import dataset_service

router = APIRouter(tags=["Datasets"])


@router.get("/runs/{run_id}/dataset", response_model=DatasetResponse)
def get_run_dataset(
    run_id: str,
    search: Optional[str] = Query(None, description="Search term across all columns"),
    valid_filter: Optional[str] = Query("all", pattern="^(all|valid|invalid)$", description="Filter records by validity"),
    sort_by: Optional[str] = Query(None, description="Field name or metric to sort by"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sorting direction"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Records per page"),
    db: Session = Depends(get_db)
):
    """
    Retrieve structured records produced by a run, with search, validity filtering,
    dynamic sorting, and full evidence linkages.
    """
    try:
        return dataset_service.get_dataset(
            db=db,
            run_id=run_id,
            search=search,
            valid_filter=valid_filter,
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
    """Export dataset as RFC-compliant CSV with header row and quality metadata."""
    try:
        csv_content = dataset_service.export_csv(db, run_id)
        filename = f"datapilot_dataset_{run_id[:8]}.csv"
        return Response(
            content=csv_content,
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
    """Export dataset as structured JSON array with field values and quality scores."""
    try:
        json_data = dataset_service.export_json(db, run_id)
        filename = f"datapilot_dataset_{run_id[:8]}.json"
        return Response(
            content=json.dumps(json_data, indent=2),
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
