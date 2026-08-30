from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AuditEvent

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_events(limit: int = 200, db: Session = Depends(get_db)):
    events = (db.query(AuditEvent).order_by(AuditEvent.id.desc()).limit(limit).all())
    return [
        {"id": e.id, "actor": e.actor, "action": e.action, "entity": e.entity,
         "details": e.details, "timestamp": e.timestamp}
        for e in events
    ]
