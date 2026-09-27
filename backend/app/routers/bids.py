import hashlib
import shutil
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit import log_event
from app.auth.dependencies import get_current_user, require_role
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
    Tender,
    User,
)
from app.pipeline.orchestrator import run_pipeline

router = APIRouter(prefix="/bids", tags=["bids"])


def _tender_is_open(tender: Tender) -> bool:
    if tender.status != "APPROVED":
        return False
    if not tender.deadline:
        return True  # legacy tenders remain available
    deadline = datetime.fromisoformat(tender.deadline.replace("Z", "+00:00"))
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) < deadline


def _reopen_for_edit(bid: Bid, db: Session, current_user: User) -> None:
    """Reset verification if a submitted application is edited before close."""
    tender = db.get(Tender, bid.tender_id)
    if not tender or not _tender_is_open(tender):
        raise HTTPException(409, "This tender is closed; applications can no longer be edited")
    if not bid.submitted_at:
        if bid.pipeline_status != "DRAFT":
            raise HTTPException(409, "This application cannot be edited while verification is running")
        return
    if bid.pipeline_status not in ("DONE", "ERROR"):
        raise HTTPException(409, "Please wait for verification to finish before editing this application")

    for model in (GovtRecord, ComplianceResult, RiskAssessment, Recommendation, OfficerDecision):
        db.query(model).filter_by(bid_id=bid.id).delete(synchronize_session=False)
    for document in db.query(Document).filter_by(bid_id=bid.id).all():
        db.query(ExtractedField).filter_by(document_id=document.id).delete(synchronize_session=False)
        document.status = "UPLOADED"
        document.doc_type = "OTHER"
        document.ocr_method = ""
        document.ocr_confidence = 0
    bid.submitted_at = ""
    bid.pipeline_status = "DRAFT"
    log_event(db, current_user.role, "BID_REOPENED_FOR_EDIT", f"bid:{bid.id}",
              "Bidder edited application before tender deadline; verification and prior decision reset")


class BidIn(BaseModel):
    tender_id: int
    bidder_id: int


@router.post("", dependencies=[Depends(require_role("bidder"))])
def create_bid(body: BidIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verify bidder belongs to current user
    bidder = db.get(Bidder, body.bidder_id)
    if not bidder or bidder.user_id != current_user.id:
        raise HTTPException(403, "Not your bidder profile")
    # Verify tender is APPROVED
    tender = db.get(Tender, body.tender_id)
    if not tender or not _tender_is_open(tender):
        raise HTTPException(400, "Tender not open for bidding")
    # A bidder has one application per tender. Return it so retries and a
    # refreshed browser do not create another application.
    existing = db.query(Bid).filter_by(tender_id=body.tender_id, bidder_id=body.bidder_id).first()
    if existing:
        return {"id": existing.id, "pipeline_status": existing.pipeline_status, "existing": True}
    bid = Bid(tender_id=body.tender_id, bidder_id=body.bidder_id, created_by=current_user.id)
    db.add(bid)
    db.commit()
    log_event(db, "bidder", "BID_CREATED", f"bid:{bid.id}")
    return {"id": bid.id, "pipeline_status": bid.pipeline_status}


@router.get("/mine", dependencies=[Depends(require_role("bidder"))])
def my_bids(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Applications for the signed-in bidder, including draft applications."""
    bids = db.query(Bid).filter_by(created_by=current_user.id).order_by(Bid.id.desc()).all()
    # Older seed runs or pre-fix data may already contain duplicate rows.
    # Expose one canonical application per tender and bidder.
    canonical = {}
    for bid in bids:
        key = (bid.tender_id, bid.bidder_id)
        prior = canonical.get(key)
        if prior is None or (bid.pipeline_status == "DONE" and prior.pipeline_status != "DONE"):
            canonical[key] = bid
    bids = sorted(canonical.values(), key=lambda b: b.id, reverse=True)
    return [{"id": b.id, "tender_id": b.tender_id,
             "tender_title": db.get(Tender, b.tender_id).title,
             "deadline": db.get(Tender, b.tender_id).deadline or "",
             "pipeline_status": b.pipeline_status, "submitted_at": b.submitted_at,
             "documents": [{"id": d.id, "filename": d.filename}
                           for d in db.query(Document).filter_by(bid_id=b.id).all()]}
            for b in bids]


@router.post("/{bid_id}/documents", dependencies=[Depends(require_role("bidder"))])
def upload_document(bid_id: int, file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    if bid.created_by != current_user.id:
        raise HTTPException(403, "Not your bid")
    tender = db.get(Tender, bid.tender_id)
    if not tender or not _tender_is_open(tender):
        raise HTTPException(409, "This tender is closed; applications can no longer be edited")
    if not file.filename or Path(file.filename).suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx"}:
        raise HTTPException(400, "Unsupported document type")
    _reopen_for_edit(bid, db, current_user)
    safe_name = Path(file.filename).name
    dest = UPLOADS_DIR / f"bid_{bid_id}_{uuid4().hex}_{safe_name}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    sha = hashlib.sha256(dest.read_bytes()).hexdigest()
    doc = Document(bid_id=bid_id, filename=safe_name, file_path=str(dest), sha256=sha)
    db.add(doc)
    db.commit()
    log_event(db, "bidder", "DOCUMENT_UPLOADED", f"document:{doc.id}",
              f"{file.filename} sha256={sha[:12]}")
    return {"id": doc.id, "filename": doc.filename, "status": doc.status}


@router.delete("/{bid_id}/documents/{doc_id}", dependencies=[Depends(require_role("bidder"))])
def delete_bid_document(bid_id: int, doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    doc = db.get(Document, doc_id)
    if not bid or not doc or doc.bid_id != bid_id:
        raise HTTPException(404, "bid document not found")
    if bid.created_by != current_user.id:
        raise HTTPException(403, "Not your bid")
    tender = db.get(Tender, bid.tender_id)
    if not tender or not _tender_is_open(tender):
        raise HTTPException(409, "This tender is closed; applications can no longer be edited")
    _reopen_for_edit(bid, db, current_user)
    db.query(ExtractedField).filter_by(document_id=doc.id).delete(synchronize_session=False)
    try:
        Path(doc.file_path).unlink(missing_ok=True)
    except OSError:
        pass
    db.delete(doc)
    db.commit()
    log_event(db, "bidder", "DOCUMENT_REMOVED", f"document:{doc_id}",
              f"Removed from bid:{bid_id}", organization_id=tender.organization_id)
    return {"ok": True}


@router.post("/{bid_id}/submit", dependencies=[Depends(require_role("bidder"))])
def submit_bid(bid_id: int, background: BackgroundTasks, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    if bid.created_by != current_user.id:
        raise HTTPException(403, "Not your bid")
    if bid.pipeline_status != "DRAFT" or bid.submitted_at:
        raise HTTPException(409, "Bid is already submitted or currently being verified")
    if not db.query(Document).filter_by(bid_id=bid_id).count():
        raise HTTPException(400, "no documents uploaded")
    tender = db.get(Tender, bid.tender_id)
    if not tender or not _tender_is_open(tender):
        raise HTTPException(409, "Tender is no longer open for bidding")
    bid.submitted_at = datetime.now(timezone.utc).isoformat()
    bid.pipeline_status = "QUEUED"
    db.commit()
    log_event(db, "bidder", "BID_SUBMITTED", f"bid:{bid_id}")
    background.add_task(run_pipeline, bid_id)
    return {"id": bid_id, "pipeline_status": "QUEUED"}


@router.delete("/{bid_id}", dependencies=[Depends(require_role("officer", "admin"))])
def delete_bid(bid_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Remove one bid and its stored processing data while keeping an audit event."""
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    tender = db.get(Tender, bid.tender_id)
    if current_user.role != "admin" and tender.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    if bid.pipeline_status not in ("DRAFT", "DONE", "ERROR", "WITHDRAWN"):
        raise HTTPException(409, "Wait for bid verification to finish before deleting it")

    bidder_name = db.get(Bidder, bid.bidder_id).legal_name
    tender_organization_id = tender.organization_id
    removed_files = 0
    for doc in db.query(Document).filter_by(bid_id=bid_id).all():
        db.query(ExtractedField).filter_by(document_id=doc.id).delete(synchronize_session=False)
        try:
            Path(doc.file_path).unlink(missing_ok=True)
            removed_files += 1
        except OSError:
            pass
        db.delete(doc)
    for model in (GovtRecord, ComplianceResult, RiskAssessment, Recommendation, OfficerDecision):
        db.query(model).filter_by(bid_id=bid_id).delete(synchronize_session=False)
    db.delete(bid)
    db.commit()
    log_event(db, current_user.role, "BID_DELETED", f"bid:{bid_id}",
              f"{bidder_name}; {removed_files} uploaded document(s) removed",
              organization_id=tender_organization_id)
    return {"ok": True, "deleted_files": removed_files}


@router.get("/documents/{doc_id}/file", dependencies=[Depends(get_current_user)])
def document_file(doc_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(404, "document not found")
    bid = db.get(Bid, doc.bid_id)
    if current_user.role == "bidder" and bid.created_by != current_user.id:
        raise HTTPException(403, "Not your document")
    if current_user.role == "officer":
        tender = db.get(Tender, bid.tender_id)
        if tender.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not your organization's tender")
    return FileResponse(doc.file_path, filename=doc.filename,
                        content_disposition_type="inline")


@router.get("/{bid_id}/status", dependencies=[Depends(get_current_user)])
def bid_status(bid_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    if current_user.role == "bidder" and bid.created_by != current_user.id:
        raise HTTPException(403, "Not your bid")
    if current_user.role == "officer":
        tender = db.get(Tender, bid.tender_id)
        if tender.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not your organization's tender")
    return {"id": bid_id, "pipeline_status": bid.pipeline_status}


class DecisionIn(BaseModel):
    decision: str  # Qualified | Disqualified | Seek Clarification
    remarks: str = ""


@router.post("/{bid_id}/decision", dependencies=[Depends(require_role("officer", "admin"))])
def record_decision(bid_id: int, body: DecisionIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.decision not in ("Qualified", "Disqualified", "Seek Clarification"):
        raise HTTPException(400, "invalid decision")
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    tender = db.get(Tender, bid.tender_id)
    if current_user.role != "admin" and tender.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    d = OfficerDecision(bid_id=bid_id, decision=body.decision, remarks=body.remarks, officer=current_user.email)
    db.add(d)
    db.commit()
    log_event(db, "officer", "DECISION_RECORDED", f"bid:{bid_id}",
              f"{body.decision}: {body.remarks}")
    return {"ok": True, "decision": body.decision}


@router.get("/{bid_id}", dependencies=[Depends(get_current_user)])
def bid_detail(bid_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bid = db.get(Bid, bid_id)
    if not bid:
        raise HTTPException(404, "bid not found")
    if current_user.role == "bidder" and bid.created_by != current_user.id:
        raise HTTPException(403, "Not your bid")
    if current_user.role == "officer":
        tender = db.get(Tender, bid.tender_id)
        if tender.organization_id != current_user.organization_id:
            raise HTTPException(403, "Not your organization's tender")
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
