from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit import entity_organization_id
from app.auth.dependencies import get_current_user, require_role
from app.db import get_db
from app.models import AuditEvent, User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", dependencies=[Depends(require_role("officer", "admin", "auditor"))])
def list_events(limit: int = Query(default=200, ge=1, le=1000), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    query = db.query(AuditEvent).order_by(AuditEvent.id.desc())
    if current_user.role == "admin":
        events = query.limit(limit).all()
    else:
        candidates = query.filter(or_(
            AuditEvent.organization_id == current_user.organization_id,
            AuditEvent.organization_id.is_(None),
        )).all()
        events = []
        for event in candidates:
            org_id = event.organization_id or entity_organization_id(db, event.entity)
            if org_id == current_user.organization_id:
                events.append(event)
                if len(events) >= limit:
                    break
    return [
        {"id": e.id, "actor": e.actor, "action": e.action, "entity": e.entity,
         "details": e.details, "timestamp": e.timestamp}
        for e in events
    ]
