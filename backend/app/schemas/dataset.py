from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas.planner import FieldSpec


class EvidenceItem(BaseModel):
    id: str
    field_name: str
    source_url: str
    snippet: str
    confidence: float = 0.95
    collected_at: datetime


class RecordItem(BaseModel):
    id: str
    data: Dict[str, Any]
    is_valid: bool = True
    confidence_score: float = 1.0
    validation_errors: List[str] = Field(default_factory=list)
    deduplicated_with: Optional[str] = None
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    created_at: datetime


class DatasetResponse(BaseModel):
    run_id: str
    workflow_id: str
    prompt: str
    goal: str
    execution_mode: str
    total_records: int
    valid_records: int
    duplicate_records: int
    fields: List[FieldSpec]
    records: List[RecordItem]
    page: int = 1
    page_size: int = 50
    total_pages: int = 1
