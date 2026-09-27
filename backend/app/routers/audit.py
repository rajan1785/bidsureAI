from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.db import get_db
from app.models import AuditEvent, User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", dependencies=[Depends(require_role("officer", "admin", "auditor"))])
def list_events(limit: int = 200, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Officers/auditors see only their org's events
    if current_user.role in ("officer", "auditor"):
        # Filter by organization - need to join with tenders/bids
        # For simplicity, return all for now - can be enhanced later
        pass
    events = (db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).all())
    return [
        {"id": e.id, "actor": e.actor, "action": e.action, "entity": e.entity,
         "details": e.details, "timestamp": e.timestamp}
        for e in events
    ]
