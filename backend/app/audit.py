from sqlalchemy.orm import Session

from app.models import AuditEvent


def log_event(db: Session, actor: str, action: str, entity: str, details: str = ""):
    ev = AuditEvent(actor=actor, action=action, entity=entity, details=details)
    db.add(ev)
    db.commit()
    return ev
