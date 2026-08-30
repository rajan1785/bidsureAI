import hashlib
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit import log_event
from app.db import UPLOADS_DIR, get_db
from app.models import (
    Bid,
    Bidder,
    ComplianceResult,
    Document,
    ExtractedField,
    GovtRecord,
    OfficerDecision,
    Recommendation,
    RiskAssessment,
)
from app.pipeline.orchestrator import run_pipeline

router = APIRouter(prefix="/bids", tags=["bids"])


class BidIn(BaseModel):
    tender_id: int
    bidder_id: int


@router.post("")
def create_bid(body: BidIn, db: Session = Depends(get_db)):
    bid = Bid(tender_id=body.tender_id, bidder_id=body.bidder_id)
    db.add(bid)
    db.commit()
    log_event(db, "bidder", "BID_CREATED", f"bid:{bid.id}")
    return {"id": bid.id, "pipeline_status": bid.pipeline_status}


@router.post("/{bid_id}/documents")
def upload_document(bid_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    dest = UPLOADS_DIR / f"bid_{bid_id}_{file.filename}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    doc = Document(bid_id=bid_id, filename=file.filename, file_path=str(dest), sha256=sha)
    db.add(doc)
    db.commit()
    log_event(db, "bidder", "DOCUMENT_UPLOADED", f"document:{doc.id}",
              f"{file.filename} sha256={sha[:12]}")
    return {"id": doc.id, "filename": doc.filename, "status": doc.status}


@router.post("/{bid_id}/submit")
def submit_bid(bid_id: int, background: BackgroundTasks, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    if not db.query(Document).filter_by(bid_id=bid_id).count():
        raise HTTPException(400, "no documents uploaded")
    bid.submitted_at = datetime.now(timezone.utc).isoformat()
    bid.pipeline_status = "QUEUED"
    db.commit()
    log_event(db, "bidder", "BID_SUBMITTED", f"bid:{bid_id}")
    background.add_task(run_pipeline, bid_id)
    return {"id": bid_id, "pipeline_status": "QUEUED"}


@router.get("/documents/{doc_id}/file")
def document_file(doc_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    return FileResponse(doc.file_path, filename=doc.filename)


@router.get("/{bid_id}/status")
def bid_status(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    return {"id": bid_id, "pipeline_status": bid.pipeline_status}


class DecisionIn(BaseModel):
    decision: str  # Qualified | Disqualified | Seek Clarification
    remarks: str = ""


@router.post("/{bid_id}/decision")
def record_decision(bid_id: int, body: DecisionIn, db: Session = Depends(get_db)):
    if body.decision not in ("Qualified", "Disqualified", "Seek Clarification"):
        raise HTTPException(400, "invalid decision")
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    d = OfficerDecision(bid_id=bid_id, decision=body.decision, remarks=body.remarks)
    db.add(d)
    db.commit()
    log_event(db, "officer", "DECISION_RECORDED", f"bid:{bid_id}",
              f"{body.decision}: {body.remarks}")
    return {"ok": True, "decision": body.decision}


@router.get("/{bid_id}")
def bid_detail(bid_id: int, db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    bidder = db.get(Bidder, bid.bidder_id)
    docs = db.query(Document).filter_by(bid_id=bid_id).all()
    results = db.query(ComplianceResult).filter_by(bid_id=bid_id).all()
    risk = db.query(RiskAssessment).filter_by(bid_id=bid_id).first()
    rec = db.query(Recommendation).filter_by(bid_id=bid_id).first()
    decision = (db.query(OfficerDecision).filter_by(bid_id=bid_id)
                .order_by(OfficerDecision.id.desc()).first())
    govt = db.query(GovtRecord).filter_by(bid_id=bid_id).all()

    return {
        "id": bid.id,
        "tender_id": bid.tender_id,
        "pipeline_status": bid.pipeline_status,
        "submitted_at": bid.submitted_at,
        "bidder": {"id": bidder.id, "legal_name": bidder.legal_name, "pan": bidder.pan,
                   "gstin": bidder.gstin, "udyam": bidder.udyam, "epfo_code": bidder.epfo_code},
        "documents": [
            {"id": d.id, "filename": d.filename, "doc_type": d.doc_type, "status": d.status,
             "ocr_method": d.ocr_method, "ocr_confidence": d.ocr_confidence, "sha256": d.sha256,
             "fields": [
                 {"field": f.field, "value": f.value, "confidence": f.confidence,
                  "evidence_location": f.evidence_location}
                 for f in db.query(ExtractedField).filter_by(document_id=d.id).all()
             ]}
            for d in docs
        ],
        "govt_records": [
            {"source": g.source, "identifier": g.identifier, "status": g.status,
             "payload": g.payload, "retrieved_at": g.retrieved_at, "mock": bool(g.mock)}
            for g in govt
        ],
        "results": [
            {"requirement_key": r.requirement_key, "requirement_text": r.requirement_text,
             "status": r.status, "reason": r.reason, "rule_id": r.rule_id,
             "rule_version": r.rule_version, "evidence": r.evidence, "critical": bool(r.critical)}
            for r in results
        ],
        "risk": ({"score": risk.score, "risk": risk.risk, "factors": risk.factors}
                 if risk else None),
        "recommendation": ({"text": rec.text, "model": rec.model,
                            "grounded_refs": rec.grounded_refs} if rec else None),
        "decision": ({"decision": decision.decision, "remarks": decision.remarks,
                      "officer": decision.officer, "timestamp": decision.timestamp}
                     if decision else None),
    }
