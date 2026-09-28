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
    confidence_level: str = "HIGH"  # HIGH, MEDIUM, LOW
    evidence_status: str = "AVAILABLE"  # AVAILABLE, PARTIAL, MISSING
    field_validations: Dict[str, str] = Field(default_factory=dict)
    field_transformations: Dict[str, List[str]] = Field(default_factory=dict)
    validation_errors: List[str] = Field(default_factory=list)
    deduplicated_with: Optional[str] = None
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    created_at: datetime


class DataQualitySummary(BaseModel):
    total_evaluated: int
    valid_count: int
    valid_rate_percent: float
    field_completion_rates: Dict[str, float]
    confidence_breakdown: Dict[str, int]  # HIGH, MEDIUM, LOW
    average_confidence: float
    evidence_coverage_percent: float
    deduplication_reduction_percent: float
    issues_found: List[str] = Field(default_factory=list)


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
    quality_summary: Optional[DataQualitySummary] = None
    page: int = 1
    page_size: int = 50
    total_pages: int = 1
