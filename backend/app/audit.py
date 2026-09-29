import time
from sqlalchemy.orm import Session
from app.db.models import AuditLog

def log_audit(db: Session, user_id: int, action: str, target: str = None, detail: str = None):
    """
    Helper to record an audit action in the database.
    """
    ts = int(time.time() * 1000)
    audit_entry = AuditLog(
        ts=ts,
        user_id=user_id,
        action=action,
        target=target,
        detail=detail
    )
    db.add(audit_entry)
    db.commit()
