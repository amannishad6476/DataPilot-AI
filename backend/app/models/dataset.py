import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class DatasetRecord(Base):
    __tablename__ = "dataset_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    workflow_id = Column(String(36), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    data = Column(JSON, default=dict)
    is_valid = Column(Boolean, default=True)
    confidence_score = Column(Float, default=1.0)
    confidence_level = Column(String(20), default="HIGH")  # HIGH, MEDIUM, LOW
    evidence_status = Column(String(20), default="AVAILABLE")  # AVAILABLE, PARTIAL, MISSING
    field_validations = Column(JSON, default=dict)  # field_name -> "VALID" | "INVALID" | "MISSING" | "NEEDS_REVIEW"
    field_transformations = Column(JSON, default=dict)  # field_name -> [list of applied transforms]
    validation_errors = Column(JSON, default=list)
    deduplicated_with = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    run = relationship("WorkflowRun", back_populates="records")
    evidence_items = relationship("EvidenceRecord", back_populates="record", cascade="all, delete-orphan")


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    record_id = Column(String(36), ForeignKey("dataset_records.id", ondelete="CASCADE"), nullable=False)
    field_name = Column(String(100), nullable=False)
    source_url = Column(Text, nullable=False)
    snippet = Column(Text, nullable=False)
    confidence = Column(Float, default=0.95)
    collected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    record = relationship("DatasetRecord", back_populates="evidence_items")
