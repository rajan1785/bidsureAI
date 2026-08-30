import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit import log_event
from app.db import UPLOADS_DIR, get_db
from app.models import DynamicRule, Requirement, Tender
from app.pipeline.ocr import extract_text
from app.pipeline.codegen import generate_code
from app.pipeline.rule_forge import draft_rule
from app.pipeline.tender_extract import extract_requirements

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.post("")
def create_tender(
    title: str = Form(...),
    organization: str = Form(""),
    ref_no: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    tender = Tender(title=title, organization=organization, ref_no=ref_no, status="EXTRACTING")
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
    reqs = extract_requirements(ocr["text"])
    drafted = 0
    for r in reqs:
        req = Requirement(tender_id=tender.id, text=r["text"], type=r["type"],
                          priority=r["priority"], rule_key=r["rule_key"])
        db.add(req)
        db.flush()
        if not r["rule_key"]:
            # no built-in rule covers this clause -> forge drafts one
            d = draft_rule(r["text"])
            dr = DynamicRule(tender_id=tender.id, requirement_id=req.id,
                             rule_type=d["rule_type"], keywords=d["keywords"],
                             threshold=d["threshold"], unit=d["unit"],
                             comparator=d["comparator"],
                             legal_basis=d.get("legal_basis"))
            db.add(dr)
            db.flush()
            dr.generated_code = generate_code(d, f"R-DYN-{dr.id}", r["text"])
            drafted += 1
    tender.status = "REVIEW"
    db.commit()
    if drafted:
        log_event(db, "system", "DYNAMIC_RULES_DRAFTED", f"tender:{tender.id}",
                  f"{drafted} rule(s) drafted for tender-specific clauses")
    log_event(db, "officer", "TENDER_CREATED", f"tender:{tender.id}", title)
    log_event(db, "system", "REQUIREMENTS_EXTRACTED", f"tender:{tender.id}",
              f"{len(reqs)} candidate requirements (ocr={ocr['method']})")
    return get_tender(tender.id, db)


@router.get("")
def list_tenders(db: Session = Depends(get_db)):
    return [_tender_dict(t, db) for t in db.query(Tender).all()]


@router.get("/{tender_id}")
def get_tender(tender_id: int, db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "tender not found")
    return _tender_dict(t, db)


class ReqUpdate(BaseModel):
    text: str | None = None
    type: str | None = None
    priority: str | None = None


@router.put("/{tender_id}/requirements/{req_id}")
def update_requirement(tender_id: int, req_id: int, body: ReqUpdate, db: Session = Depends(get_db)):
    r = db.get(Requirement, req_id)
    if not r or r.tender_id != tender_id:
        raise HTTPException(404, "requirement not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(r, k, v)
    db.commit()
    log_event(db, "officer", "REQUIREMENT_EDITED", f"requirement:{req_id}")
    return {"ok": True}


@router.delete("/{tender_id}/requirements/{req_id}")
def delete_requirement(tender_id: int, req_id: int, db: Session = Depends(get_db)):
    r = db.get(Requirement, req_id)
    if not r or r.tender_id != tender_id:
        raise HTTPException(404, "requirement not found")
    for dr in db.query(DynamicRule).filter_by(requirement_id=req_id).all():
        db.delete(dr)
    db.delete(r)
    db.commit()
    log_event(db, "officer", "REQUIREMENT_DELETED", f"requirement:{req_id}")
    return {"ok": True}


@router.post("/{tender_id}/approve")
def approve_tender(tender_id: int, db: Session = Depends(get_db)):
    t = db.get(Tender, tender_id)
    if not t:
        raise HTTPException(404, "tender not found")
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
                "legal_basis": d.legal_basis, "generated_code": d.generated_code}
    return {
        "id": t.id, "title": t.title, "organization": t.organization, "ref_no": t.ref_no,
        "status": t.status, "ruleset_version": t.ruleset_version, "created_at": t.created_at,
        "requirements": [
            {"id": r.id, "text": r.text, "type": r.type, "priority": r.priority,
             "rule_key": r.rule_key, "approved": bool(r.approved),
             "dynamic_rule": _dyn(r)}
            for r in reqs
        ],
    }
