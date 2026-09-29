import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.core.logging import get_logger

logger = get_logger("datapilot.audit")


def record_audit_event(
    db: Session,
    event_type: str,
    resource_type: str,
    action: str,
    resource_id: Optional[str] = None,
    status: str = "SUCCESS",
    tenant_id: str = "tenant_default",
    user_id: str = "usr_local_owner",
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Optional[AuditLog]:
    """Persists an audit event to the database and emits an audit log."""
    try:
        log_entry = AuditLog(
            tenant_id=tenant_id,
            user_id=user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            ip_address=ip_address,
            details=details or {}
        )
        db.add(log_entry)
        db.commit()
        logger.info(
            f"AUDIT_EVENT [{event_type}] resource={resource_type}:{resource_id} action={action} status={status} user={user_id}"
        )
        return log_entry
    except Exception as e:
        logger.error(f"Failed to record audit event {event_type}: {e}")
        try:
            db.rollback()
        except Exception:
            pass
        return None
