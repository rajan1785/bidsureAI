from sqlalchemy.orm import Session

from app.models import AuditEvent, Bid, Bidder, Document, Requirement, Tender


def entity_organization_id(db: Session, entity: str) -> int | None:
    """Resolve an audit entity to its owning organization when it still exists."""
    try:
        kind, raw_id = entity.split(":", 1)
        entity_id = int(raw_id)
    except (ValueError, AttributeError):
        return None

    if kind == "tender":
        tender = db.get(Tender, entity_id)
        return tender.organization_id if tender else None
    if kind == "bid":
        bid = db.get(Bid, entity_id)
        tender = db.get(Tender, bid.tender_id) if bid else None
        return tender.organization_id if tender else None
    if kind == "document":
        document = db.get(Document, entity_id)
        bid = db.get(Bid, document.bid_id) if document else None
        tender = db.get(Tender, bid.tender_id) if bid else None
        return tender.organization_id if tender else None
    if kind == "requirement":
        requirement = db.get(Requirement, entity_id)
        tender = db.get(Tender, requirement.tender_id) if requirement else None
        return tender.organization_id if tender else None
    if kind == "bidder":
        bidder = db.get(Bidder, entity_id)
        return bidder.organization_id if bidder else None
    return None


def log_event(db: Session, actor: str, action: str, entity: str, details: str = "",
              organization_id: int | None = None):
    org_id = organization_id if organization_id is not None else entity_organization_id(db, entity)
    ev = AuditEvent(actor=actor, action=action, entity=entity, details=details,
                    organization_id=org_id)
    db.add(ev)
    db.commit()
    return ev
