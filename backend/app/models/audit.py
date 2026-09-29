import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, Text
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(50), default="tenant_default", index=True)
    user_id = Column(String(50), default="usr_local_owner", index=True)
    event_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    status = Column(String(20), default="SUCCESS")  # SUCCESS, FAILED, BLOCKED
    ip_address = Column(String(45), nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
