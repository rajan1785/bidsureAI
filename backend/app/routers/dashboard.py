from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_role
from app.db import get_db
from app.models import Bid, Bidder, ComplianceResult, OfficerDecision, RiskAssessment, Tender, User

router = APIRouter(tags=["dashboard"])


@router.get("/tenders/{tender_id}/comparison", dependencies=[Depends(require_role("officer", "admin"))])
def comparison(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tender = db.get(Tender, tender_id)
    if not tender:
        raise HTTPException(404, "tender not found")
    # Admin accounts are cross-organization. Officers remain restricted to
    # their own organization's procurement data.
    if current_user.role != "admin" and tender.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    rows = []
    bids = db.query(Bid).filter_by(tender_id=tender_id).order_by(Bid.id).all()
    canonical = {}
    for bid in bids:
        prior = canonical.get(bid.bidder_id)
        if prior is None or (bid.pipeline_status == "DONE" and prior.pipeline_status != "DONE"):
            canonical[bid.bidder_id] = bid
    for bid in canonical.values():
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
