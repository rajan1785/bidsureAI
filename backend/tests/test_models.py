from app.audit import log_event
from app.models import Bid, Bidder, ComplianceResult, Tender


def test_model_round_trip(db):
    t = Tender(title="Security Services Tender", organization="University of Delhi")
    b = Bidder(legal_name="Shakti Facility Services Pvt Ltd", pan="AAECS1234F")
    db.add_all([t, b])
    db.commit()

    bid = Bid(tender_id=t.id, bidder_id=b.id)
    db.add(bid)
    db.commit()

    cr = ComplianceResult(
        bid_id=bid.id,
        requirement_key="gst_active",
        status="Compliant",
        reason="GSTIN matches and is Active",
        rule_id="R-GST-01",
        rule_version="v1",
        evidence={"doc_value": "07AAECS1234F1Z5"},
    )
    db.add(cr)
    db.commit()

    fetched = db.query(ComplianceResult).filter_by(bid_id=bid.id).one()
    assert fetched.status == "Compliant"
    assert fetched.evidence["doc_value"] == "07AAECS1234F1Z5"


def test_audit_log(db):
    ev = log_event(db, "system", "PIPELINE_STARTED", "bid:1", "demo")
    assert ev.id is not None
    assert ev.timestamp
