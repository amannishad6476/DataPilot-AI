from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field


StepType = Literal[
    "input",
    "ai_planning",
    "source_discovery",
    "extraction",
    "transformation",
    "validation",
    "deduplication",
    "merge",
    "output"
]


class FieldSpec(BaseModel):
    name: str = Field(..., description="Unique field name in snake_case (e.g. company_name, email)")
    type: str = Field("string", description="Field data type: string, email, phone, url, number, date, text")
    required: bool = Field(True, description="Whether this field is mandatory in final data")
    description: Optional[str] = Field(None, description="Human readable description of the field")


class SourceSpec(BaseModel):
    id: str = Field(..., description="Unique identifier for the source")
    type: str = Field(..., description="Type of source: search_engine, public_directory, official_portal, registry")
    name: str = Field(..., description="Readable name of the source")
    purpose: str = Field(..., description="What specific data this source provides")
    allowed_public_only: bool = Field(True, description="Enforces compliance with robots.txt and public data policies")


class ValidationRuleSpec(BaseModel):
    field: str = Field(..., description="Field name this rule validates")
    rule_type: str = Field(..., description="Type of validation: email_rfc, phone_e164, url_format, non_empty, regex")
    description: str = Field(..., description="Explanation of what is validated")
    severity: Literal["error", "warning"] = Field("error", description="Validation severity")
    params: Dict[str, Any] = Field(default_factory=dict, description="Rule-specific parameters (e.g., regex pattern)")


class WorkflowStepPlan(BaseModel):
    id: str = Field(..., description="Unique step ID, e.g. step_1_input, step_2_sources")
    type: StepType = Field(..., description="Step category: input, ai_planning, source_discovery, extraction, transformation, validation, deduplication, merge, output")
    name: str = Field(..., description="Clear human-readable step title")
    description: str = Field(..., description="Actionable summary of what this step executes")
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps that must finish before this step")
    action: str = Field(..., description="Concrete engine action to run")
    target_fields: List[str] = Field(default_factory=list, description="Fields generated or manipulated by this step")
    estimated_duration_sec: float = Field(2.0, description="Estimated duration in seconds")


class PlannerOutput(BaseModel):
    goal: str = Field(..., description="Structured interpretation of user goal")
    domain: str = Field("general", description="Industry domain, e.g. college_fest_sponsorship, tech_recruiting, b2b_leads")
    target_record_count: int = Field(30, description="Target number of records to gather")
    entities: List[str] = Field(default_factory=list, description="Key entities to extract (e.g. company, contact)")
    fields: List[FieldSpec] = Field(default_factory=list, description="List of fields to collect")
    sources: List[SourceSpec] = Field(default_factory=list, description="Permitted public sources to query")
    steps: List[WorkflowStepPlan] = Field(default_factory=list, description="DAG of workflow steps")
    validation_rules: List[ValidationRuleSpec] = Field(default_factory=list, description="Validation rules to enforce")
    deduplication_strategy: str = Field(..., description="Strategy description for deduplication")
    deduplication_keys: List[str] = Field(default_factory=list, description="Key fields used for similarity comparison")
    output_format: str = Field("table", description="Final output format: table, json, csv")


class PlannerRequest(BaseModel):
    prompt: str = Field(..., min_length=5, description="Natural language description of data collection need")
    target_record_count: Optional[int] = Field(30, ge=1, le=200, description="Target record count")


class WorkflowResponse(BaseModel):
    id: str
    prompt: str
    plan: PlannerOutput
    created_at: datetime
    run_count: int = 0
    latest_run_id: Optional[str] = None
    latest_status: Optional[str] = None
