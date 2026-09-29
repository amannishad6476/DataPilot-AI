from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models.audit import AuditLog
from app.core.security import get_current_user, require_role, Role, UserContext
from pydantic import BaseModel
from datetime import datetime


class AuditLogItem(BaseModel):
    id: str
    tenant_id: str
    user_id: str
    event_type: str
    resource_type: str
    resource_id: Optional[str] = None
    action: str
    status: str
    ip_address: Optional[str] = None
    details: dict
    timestamp: datetime


router = APIRouter(prefix="/audit", tags=["Audit & Compliance"])


@router.get("", response_model=List[AuditLogItem])
def list_audit_logs(
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    status: Optional[str] = Query(None, description="Filter by status (SUCCESS, FAILED, BLOCKED)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    user: UserContext = Depends(require_role(Role.ADMIN))
):
    """Retrieve compliance and security audit logs."""
    query = db.query(AuditLog).filter(AuditLog.tenant_id == user.tenant_id)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if status:
        query = query.filter(AuditLog.status == status)

    logs = query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
    return logs
