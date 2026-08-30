from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bid, Bidder, ComplianceResult, OfficerDecision, RiskAssessment

router = APIRouter(tags=["dashboard"])


@router.get("/tenders/{tender_id}/comparison")
def comparison(tender_id: int, db: Session = Depends(get_db)):
    rows = []
    for bid in db.query(Bid).filter_by(tender_id=tender_id).all():
        bidder = db.get(Bidder, bid.bidder_id)
        risk = db.query(RiskAssessment).filter_by(bid_id=bid.id).first()
        results = db.query(ComplianceResult).filter_by(bid_id=bid.id).all()
        decision = (db.query(OfficerDecision).filter_by(bid_id=bid.id)
                    .order_by(OfficerDecision.id.desc()).first())
        counts = {}
        for r in results:
            counts[r.status] = counts.get(r.status, 0) + 1
        rows.append({
            "bid_id": bid.id,
            "bidder": bidder.legal_name,
            "pipeline_status": bid.pipeline_status,
            "score": risk.score if risk else None,
            "risk": risk.risk if risk else None,
            "status_counts": counts,
            "issues": [r.requirement_key for r in results
                       if r.status in ("Non-Compliant", "Review Required")],
            "decision": decision.decision if decision else None,
        })
    rows.sort(key=lambda r: (r["score"] is None, -(r["score"] or 0)))
    return rows
