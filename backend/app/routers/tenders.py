import shutil
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit import log_event
from app.auth.dependencies import get_current_user, require_role
from app.db import UPLOADS_DIR, get_db, resolve_upload
from pathlib import Path

from app.models import (Bid, ComplianceResult, Document, DynamicRule,
                        ExtractedField, GovtRecord, OfficerDecision,
                        Recommendation, Requirement, RiskAssessment, Tender, User)
from app.pipeline.ocr import extract_text
from app.pipeline.codegen import generate_code
from app.pipeline.rule_forge import draft_rule
from app.pipeline.tender_extract import _clean, extract_requirements, extract_tender_meta, gem_condition_flags, KEYWORD_REQUIREMENTS

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.post("", dependencies=[Depends(require_role("officer", "admin"))])
def create_tender(
    title: str = Form(""),
    organization: str = Form(""),
    ref_no: str = Form(""),
    deadline: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        deadline_dt = datetime.fromisoformat(deadline.replace("Z", "+00:00"))
        if deadline_dt.tzinfo is None:
            deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
        deadline_dt = deadline_dt.astimezone(timezone.utc)
    except ValueError:
        raise HTTPException(422, "Invalid bid deadline")
    if deadline_dt <= datetime.now(timezone.utc):
        raise HTTPException(422, "Bid deadline must be in the future")
    tender = Tender(
        title=title,
        org_name=organization,
        ref_no=ref_no,
        status="EXTRACTING",
        organization_id=current_user.organization_id,
        created_by=current_user.id,
        deadline=deadline_dt.isoformat(),
    )
    db.add(tender)
    db.commit()

    dest = UPLOADS_DIR / f"tender_{tender.id}_{file.filename}"
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    tender.file_path = str(dest)

    ocr = extract_text(str(dest))
    if not ocr["text"].strip():
        db.delete(tender)
        db.commit()
        dest.unlink(missing_ok=True)
        raise HTTPException(
            400,
            "Could not read any text from this document. Upload a PDF, DOCX or TXT "
            "tender with a text layer (scanned images need Tesseract installed).",
        )
    tender.extracted_text = ocr["text"]
    tender.ocr_method = ocr["method"]
    tender.ocr_confidence = ocr["confidence"]
    meta = extract_tender_meta(ocr["text"])
    tender.title = title.strip() or meta["title"]
    tender.org_name = organization.strip() or meta["organization"]
    tender.ref_no = ref_no.strip() or meta["ref_no"]
    tender_flags = gem_condition_flags(ocr["text"])
    reqs = extract_requirements(ocr["text"])
    drafted = 0
    for r in reqs:
        req = Requirement(tender_id=tender.id, text=r["text"], type=r["type"],
                          priority=r["priority"], rule_key=r["rule_key"])
        db.add(req)
        db.flush()
        if not r["rule_key"]:
            # no built-in rule covers this clause -> forge drafts one
            d = draft_rule(r["text"], tender_flags)
            dr = DynamicRule(tender_id=tender.id, requirement_id=req.id,
                             rule_type=d["rule_type"], keywords=d["keywords"],
                             threshold=d["threshold"], unit=d["unit"],
                             comparator=d["comparator"],
                             legal_basis=d.get("legal_basis"),
                             exemptions=d.get("exemptions") or [])
            db.add(dr)
            db.flush()
            dr.generated_code = generate_code(d, f"R-DYN-{dr.id}", r["text"])
            drafted += 1
    tender.status = "REVIEW"
    db.commit()
    if drafted:
        log_event(db, "system", "DYNAMIC_RULES_DRAFTED", f"tender:{tender.id}",
                  f"{drafted} rule(s) drafted for tender-specific clauses")
    log_event(db, "officer", "TENDER_CREATED", f"tender:{tender.id}", tender.title)
    log_event(db, "system", "REQUIREMENTS_EXTRACTED", f"tender:{tender.id}",
              f"{len(reqs)} candidate requirements (ocr={ocr['method']})")
    return _get_tender_internal(tender.id, db, current_user)


@router.get("", dependencies=[Depends(get_current_user)])
def list_tenders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "officer":
        tenders = db.query(Tender).filter_by(organization_id=current_user.organization_id).all()
    else:
        # Bidder sees only approved tenders that are still open for submissions.
        tenders = [t for t in db.query(Tender).filter_by(status="APPROVED").all()
                   if not t.deadline or datetime.fromisoformat(t.deadline.replace("Z", "+00:00")) > datetime.now(timezone.utc)]
    return [_tender_dict(t, db) for t in tenders]


def _get_tender_internal(tender_id: int, db: Session, current_user: User) -> dict:
    """Internal helper to get tender dict with auth checks."""
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "tender not found")
    # Officer: must be same org
    if current_user.role == "officer" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    # Bidder: must be APPROVED
    if current_user.role == "bidder" and t.status != "APPROVED":
        raise HTTPException(403, "Tender not open for bidding")
    return _tender_dict(t, db)


@router.get("/{tender_id}", dependencies=[Depends(get_current_user)])
def get_tender(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _get_tender_internal(tender_id, db, current_user)


@router.delete("/{tender_id}", dependencies=[Depends(require_role("officer", "admin"))])
def delete_tender(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a tender and everything under it: requirements, drafted rules,
    bids, uploaded documents (rows AND files), results, decisions."""
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "tender not found")
    if current_user.role != "admin" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    title = t.title
    tender_organization_id = t.organization_id
    bids = db.query(Bid).filter_by(tender_id=tender_id).all()
    removed_files = 0
    for bid in bids:
        docs = db.query(Document).filter_by(bid_id=bid.id).all()
        for doc in docs:
            db.query(ExtractedField).filter_by(document_id=doc.id).delete()
            try:
                Path(doc.file_path).unlink(missing_ok=True)
                removed_files += 1
            except OSError:
                pass
            db.delete(doc)
        for model in (GovtRecord, ComplianceResult, RiskAssessment,
                      Recommendation, OfficerDecision):
            db.query(model).filter_by(bid_id=bid.id).delete()
        db.delete(bid)
    db.query(DynamicRule).filter_by(tender_id=tender_id).delete()
    db.query(Requirement).filter_by(tender_id=tender_id).delete()
    if t.file_path:
        try:
            Path(t.file_path).unlink(missing_ok=True)
            removed_files += 1
        except OSError:
            pass
    db.delete(t)
    db.commit()
    log_event(db, "officer", "TENDER_DELETED", f"tender:{tender_id}",
              f"{title} ({len(bids)} bid(s), {removed_files} file(s) removed)",
              organization_id=tender_organization_id)
    return {"ok": True, "deleted_bids": len(bids), "deleted_files": removed_files}


@router.get("/{tender_id}/extracted-text", dependencies=[Depends(get_current_user)])
def tender_extracted_text(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Raw text the system read from the tender document, as inspectable JSON —
    so anyone can match what the AI saw against the real document."""
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "tender not found")
    if current_user.role == "officer" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    if current_user.role == "bidder" and t.status != "APPROVED":
        raise HTTPException(403, "Tender not open for bidding")
    return {
        "tender_id": t.id,
        "title": t.title,
        "ref_no": t.ref_no,
        "read_via": t.ocr_method,
        "read_confidence": t.ocr_confidence,
        "characters": len(t.extracted_text or ""),
        "lines": [" ".join(l.split()) for l in _clean(t.extracted_text or "").splitlines()
                  if l.strip()],
    }


@router.get("/{tender_id}/file", dependencies=[Depends(get_current_user)])
def tender_file(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t or not t.file_path:
        raise HTTPException(404, "tender document not found")
    if current_user.role == "officer" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    if current_user.role == "bidder" and t.status != "APPROVED":
        raise HTTPException(403, "Tender not open for bidding")
    path = resolve_upload(t.file_path)
    if not path:
        raise HTTPException(404, "tender document is missing on this server")
    return FileResponse(path, filename=path.name,
                        content_disposition_type="inline")


class ReqAdd(BaseModel):
    text: str
    type: str = "TENDER_SPECIFIC"
    priority: str = "MANDATORY"


@router.post("/{tender_id}/requirements", dependencies=[Depends(require_role("officer", "admin"))])
def add_requirement(tender_id: int, body: ReqAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "tender not found")
    if current_user.role != "admin" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    text = body.text.strip()
    if len(text) < 10:
        raise HTTPException(422, "requirement text too short")
    # link to a built-in rule when the text clearly matches one
    low = text.lower()
    rule_key = next((rk for kws, _, _, rk in KEYWORD_REQUIREMENTS
                     if any(k in low for k in kws)), "")
    already_approved = 1 if t.status == "APPROVED" else 0
    req = Requirement(tender_id=tender_id, text=text, type=body.type,
                      priority=body.priority, rule_key=rule_key,
                      approved=already_approved)
    db.add(req)
    db.flush()
    if not rule_key:
        d = draft_rule(text, gem_condition_flags(t.extracted_text or ""))
        dr = DynamicRule(tender_id=tender_id, requirement_id=req.id,
                         rule_type=d["rule_type"], keywords=d["keywords"],
                         threshold=d["threshold"], unit=d["unit"],
                         comparator=d["comparator"], legal_basis=d.get("legal_basis"),
                         exemptions=d.get("exemptions") or [],
                         approved=already_approved)
        db.add(dr)
        db.flush()
        dr.generated_code = generate_code(d, f"R-DYN-{dr.id}", text)
    db.commit()
    log_event(db, "officer", "REQUIREMENT_ADDED", f"requirement:{req.id}", text[:80])
    return _tender_dict(t, db)


class ReqUpdate(BaseModel):
    text: str | None = None
    type: str | None = None
    priority: str | None = None


@router.put("/{tender_id}/requirements/{req_id}", dependencies=[Depends(require_role("officer", "admin"))])
def update_requirement(tender_id: int, req_id: int, body: ReqUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Requirement, req_id)
    if not r or r.tender_id != tender_id:
        raise HTTPException(404, "requirement not found")
    t = db.get(Tender, tender_id)
    if current_user.role != "admin" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(r, k, v)
    db.commit()
    log_event(db, "officer", "REQUIREMENT_EDITED", f"requirement:{req_id}")
    return {"ok": True}


@router.delete("/{tender_id}/requirements/{req_id}", dependencies=[Depends(require_role("officer", "admin"))])
def delete_requirement(tender_id: int, req_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    r = db.get(Requirement, req_id)
    if not r or r.tender_id != tender_id:
        raise HTTPException(404, "requirement not found")
    t = db.get(Tender, tender_id)
    if current_user.role != "admin" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    tender_organization_id = t.organization_id
    for dr in db.query(DynamicRule).filter_by(requirement_id=req_id).all():
        db.delete(dr)
    db.delete(r)
    db.commit()
    log_event(db, "officer", "REQUIREMENT_DELETED", f"requirement:{req_id}",
              organization_id=tender_organization_id)
    return {"ok": True}


@router.post("/{tender_id}/approve", dependencies=[Depends(require_role("officer", "admin"))])
def approve_tender(tender_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "tender not found")
    if current_user.role != "admin" and t.organization_id != current_user.organization_id:
        raise HTTPException(403, "Not your organization's tender")
    for r in db.query(Requirement).filter_by(tender_id=tender_id).all():
        r.approved = 1
    for dr in db.query(DynamicRule).filter_by(tender_id=tender_id).all():
        dr.approved = 1
    t.status = "APPROVED"
    t.ruleset_version = "security_tender_v1@v1"
    db.commit()
    log_event(db, "officer", "REQUIREMENTS_APPROVED", f"tender:{tender_id}",
              f"ruleset {t.ruleset_version}")
    return _tender_dict(t, db)


def _tender_dict(t: Tender, db: Session):
    reqs = db.query(Requirement).filter_by(tender_id=t.id).all()
    dyn = {d.requirement_id: d for d in db.query(DynamicRule).filter_by(tender_id=t.id).all()}
    def _dyn(r):
        d = dyn.get(r.id)
        if not d:
            return None
        return {"id": d.id, "rule_type": d.rule_type, "keywords": d.keywords,
                "threshold": d.threshold, "unit": d.unit, "comparator": d.comparator,
                "version": d.version, "approved": bool(d.approved),
                "legal_basis": d.legal_basis, "generated_code": d.generated_code,
                "exemptions": d.exemptions or []}
    return {
        "id": t.id, "title": t.title, "organization": t.org_name, "ref_no": t.ref_no,
        "status": t.status, "ruleset_version": t.ruleset_version, "created_at": t.created_at,
        "deadline": t.deadline or "",
        "requirements": [
            {"id": r.id, "text": r.text, "type": r.type, "priority": r.priority,
             "rule_key": r.rule_key, "approved": bool(r.approved),
             "dynamic_rule": _dyn(r)}
            for r in reqs
        ],
    }
