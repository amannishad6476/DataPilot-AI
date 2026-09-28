from typing import List, Optional, Literal, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RunWorkflowRequest(BaseModel):
    execution_mode: Literal["demo", "real", "n8n"] = Field(
        "demo",
        description="Mode of execution: 'demo' uses high-fidelity realistic data with simulated network latencies; 'real' connects to live public permitted search APIs/pages; 'n8n' dispatches to n8n webhook."
    )
    target_url: Optional[str] = Field(None, description="Optional override URL for real source collection")
    n8n_webhook_url: Optional[str] = Field(None, description="Optional external n8n webhook URL to trigger")


class StepExecutionStatus(BaseModel):
    step_id: str
    step_name: str
    step_type: str
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    progress_percent: int = 0
    message: str = "Awaiting execution"
    records_produced: int = 0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


class TimelineEvent(BaseModel):
    id: str
    timestamp: str
    step_id: Optional[str] = None
    level: Literal["info", "warning", "error", "success"] = "info"
    stage: str
    message: str
    details: Optional[Dict[str, Any]] = None


class WorkflowRunStatus(BaseModel):
    run_id: str
    workflow_id: str
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    execution_mode: str = "demo"
    total_records: int = 0
    valid_records: int = 0
    duplicate_records: int = 0
    progress_percent: int = 0
    current_step_id: Optional[str] = None
    step_statuses: List[StepExecutionStatus] = []
    execution_timeline: List[TimelineEvent] = []
    quality_summary: Optional[Dict[str, Any]] = None
    source_health_summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class RunComparisonResponse(BaseModel):
    run_a_id: str
    run_b_id: str
    run_a_mode: str
    run_b_mode: str
    run_a_status: str
    run_b_status: str
    run_a_date: Optional[str] = None
    run_b_date: Optional[str] = None
    total_records_delta: int
    valid_records_delta: int
    duplicate_records_delta: int
    average_confidence_a: float
    average_confidence_b: float
    confidence_delta: float
    new_records_count: int
    common_records_count: int
    removed_records_count: int
    summary: str


class SourceHealthItem(BaseModel):
    connector_id: str
    name: str
    source_type: str
    status: Literal["HEALTHY", "DEGRADED", "UNAVAILABLE", "UNTESTED"]
    total_requests: int
    success_count: int
    error_count: int
    avg_latency_ms: float
    last_attempt_at: Optional[str] = None
    last_status_code: Optional[int] = None
    details: str


class SourceHealthReport(BaseModel):
    timestamp: str
    overall_status: str
    connectors: List[SourceHealthItem]
