from typing import List, Optional, Literal
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
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
