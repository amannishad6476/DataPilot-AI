import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prompt = Column(Text, nullable=False)
    goal = Column(Text, nullable=False)
    domain = Column(String(100), default="general")
    entities = Column(JSON, default=list)
    fields_spec = Column(JSON, default=list)
    sources_spec = Column(JSON, default=list)
    steps_spec = Column(JSON, default=list)
    validation_rules = Column(JSON, default=list)
    deduplication_strategy = Column(Text, default="fuzzy_entity_matching")
    output_format = Column(String(50), default="table")
    reasoning = Column(JSON, default=list)
    tenant_id = Column(String(50), default="tenant_default", index=True)
    user_id = Column(String(50), default="usr_local_owner", index=True)
    project_id = Column(String(50), default="proj_default", index=True)
    workflow_version = Column(Integer, default=1)
    planner_version = Column(String(30), default="2.0.0")
    policy_status = Column(String(30), default="APPROVED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    runs = relationship("WorkflowRun", back_populates="workflow", cascade="all, delete-orphan", order_by="desc(WorkflowRun.started_at)")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(50), default="tenant_default", index=True)
    user_id = Column(String(50), default="usr_local_owner", index=True)
    status = Column(String(30), default="pending", index=True)  # pending, running, completed, failed, cancelled
    execution_mode = Column(String(20), default="demo")  # demo, real
    total_records = Column(Integer, default=0)
    valid_records = Column(Integer, default=0)
    duplicate_records = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    step_statuses = Column(JSON, default=list)
    quality_summary = Column(JSON, default=dict)
    execution_timeline = Column(JSON, default=list)
    source_health_summary = Column(JSON, default=dict)
    node_metrics = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("Workflow", back_populates="runs")
    records = relationship("DatasetRecord", back_populates="run", cascade="all, delete-orphan")
