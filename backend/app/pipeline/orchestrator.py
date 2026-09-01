"""Workflow orchestrator (SRS §12).

Bid Submitted -> OCR -> Extract -> Govt Verification -> Cross-Check -> Rules
-> Score/Risk -> AI Recommendation -> Save -> Dashboard.
Each stage updates bid.pipeline_status (polled by the UI) and writes an
audit event. A stage failure marks the bid ERROR instead of crashing.
"""
import time

from app.audit import log_event
from app.db import SessionLocal
from app.models import (
    Bid,
    Bidder,
    ComplianceResult,
    Document,
    DynamicRule,
    ExtractedField,
    GovtRecord,
    Recommendation,
    Requirement,
    RiskAssessment,
    Tender,
)
from app.pipeline.classify import classify_doc
from app.pipeline.crosscheck import crosscheck
from app.pipeline.extract import extract_fields
from app.pipeline.ocr import extract_text
from app.pipeline.recommend import recommend
from app.pipeline.codegen import run_generated
from app.pipeline.rule_forge import evaluate_dynamic
from app.pipeline.rules import evaluate, filter_ruleset, load_ruleset
from app.pipeline.scoring import score
from app.pipeline.verify import verify_identifiers

# Small pause between stages so the live UI can show each step; harmless in tests.
STAGE_DELAY = 0.6


def _stage(db, bid, status):
    bid.pipeline_status = status
    db.commit()
    log_event(db, "system", f"PIPELINE_{status}", f"bid:{bid.id}")
    time.sleep(STAGE_DELAY)


def run_pipeline(bid_id: int):
    db = SessionLocal()
    try:
        bid = db.get(Bid, bid_id)
        bidder = db.get(Bidder, bid.bidder_id)
        tender = db.get(Tender, bid.tender_id)
        docs = db.query(Document).filter_by(bid_id=bid.id).all()

        # --- OCR + classification ---
        _stage(db, bid, "OCR")
        texts = {}
        for doc in docs:
            res = extract_text(doc.file_path)
            doc.ocr_method = res["method"]
            doc.ocr_confidence = res["confidence"]
            if not res["text"]:
                doc.status = "UNREADABLE"
                log_event(db, "system", "DOC_UNREADABLE", f"document:{doc.id}", doc.filename)
                continue
            doc.doc_type = classify_doc(res["text"])
            doc.status = "PROCESSED"
            texts[doc.id] = res["text"]
        db.commit()

        # --- Field extraction ---
        _stage(db, bid, "EXTRACT")
        extracted_by_doc: dict[str, list] = {}
        for doc in docs:
            if doc.id not in texts:
                continue
            fields = extract_fields(texts[doc.id], doc.doc_type)
            for fld in fields:
                db.add(ExtractedField(document_id=doc.id, **fld))
            extracted_by_doc.setdefault(doc.doc_type, []).extend(fields)
        db.commit()

        # --- Government verification ---
        _stage(db, bid, "GOVT_VERIFY")
        registered = {"gstin": bidder.gstin, "pan": bidder.pan,
                      "udyam": bidder.udyam, "epfo_code": bidder.epfo_code}
        govt_records = verify_identifiers(registered)
        for rec in govt_records:
            db.add(GovtRecord(bid_id=bid.id, source=rec["source"], identifier=rec["identifier"],
                              status=rec["status"], payload=rec["payload"], mock=int(rec["mock"])))
            log_event(db, "system", "SOURCE_QUERIED", f"bid:{bid.id}",
                      f"{rec['source']}:{rec['identifier']} -> {rec['status']}")
        db.commit()

        # --- Cross-check ---
        _stage(db, bid, "CROSSCHECK")
        checks = crosscheck(extracted_by_doc, registered, govt_records)

        # --- Rules ---
        _stage(db, bid, "RULES")
        ruleset_name = (tender.ruleset_version or "security_tender_v1@v1").split("@")[0]
        approved_keys = {
            r.rule_key
            for r in db.query(Requirement).filter_by(tender_id=tender.id, approved=1).all()
            if r.rule_key
        }
        ruleset = filter_ruleset(load_ruleset(ruleset_name), approved_keys)
        results = evaluate(ruleset, checks, list(extracted_by_doc.keys()))

        # AI-drafted (officer-approved) dynamic rules for tender-specific clauses
        doc_texts = {doc.filename: texts[doc.id] for doc in docs if doc.id in texts}
        dyn_rules = db.query(DynamicRule).filter_by(tender_id=tender.id, approved=1).all()
        req_texts = {r.id: r.text for r in db.query(Requirement)
                     .filter_by(tender_id=tender.id).all()}
        # facts: verified outcomes so far — drafted rules reason over these,
        # e.g. MSE (Udyam-verified) bidders are EMD-exempt per MSE Order 2012
        facts = {"results": {r["requirement_key"]: r["status"] for r in results},
                 "bidder": {"legal_name": bidder.legal_name, "pan": bidder.pan,
                            "gstin": bidder.gstin, "udyam": bidder.udyam}}
        for dr in dyn_rules:
            rule_dict = {"rule_type": dr.rule_type, "keywords": dr.keywords,
                         "threshold": dr.threshold, "unit": dr.unit,
                         "comparator": dr.comparator, "critical": bool(dr.critical),
                         "exemptions": dr.exemptions or []}
            try:
                # primary path: the rule's own generated code, sandboxed
                verdict = run_generated(dr.generated_code, doc_texts, facts)
                log_event(db, "system", "GENERATED_CODE_EXECUTED",
                          f"bid:{bid.id}", f"R-DYN-{dr.id} via generated check()")
            except Exception as exc:
                # safety net: deterministic built-in executor
                verdict = evaluate_dynamic(rule_dict, doc_texts, facts)
                log_event(db, "system", "CODE_EXEC_FALLBACK",
                          f"bid:{bid.id}", f"R-DYN-{dr.id}: {exc}")
            results.append({
                "requirement_key": f"custom_{dr.id}",
                "requirement_text": req_texts.get(dr.requirement_id, "Tender-specific clause"),
                "status": verdict["status"],
                "reason": verdict["reason"],
                "rule_id": f"R-DYN-{dr.id}",
                "rule_version": dr.version,
                "critical": bool(dr.critical),
                "weight": dr.weight,
                "evidence": {**verdict["evidence"],
                             **({"legal_basis": dr.legal_basis} if dr.legal_basis else {})},
            })

        for r in results:
            db.add(ComplianceResult(
                bid_id=bid.id, requirement_key=r["requirement_key"],
                requirement_text=r["requirement_text"], status=r["status"],
                reason=r["reason"], rule_id=r["rule_id"], rule_version=r["rule_version"],
                evidence=r["evidence"], critical=int(r["critical"]),
            ))
        db.commit()

        # --- Scoring ---
        _stage(db, bid, "SCORING")
        assessment = score(results)
        db.add(RiskAssessment(bid_id=bid.id, score=assessment["score"],
                              risk=assessment["risk"], factors=assessment["factors"]))
        db.commit()

        # --- Recommendation ---
        _stage(db, bid, "RECOMMEND")
        rec = recommend(bidder.legal_name, results, assessment, doc_texts)
        db.add(Recommendation(bid_id=bid.id, text=rec["text"], model=rec["model"],
                              grounded_refs=rec["grounded_refs"]))
        db.commit()

        bid.pipeline_status = "DONE"
        db.commit()
        log_event(db, "system", "PIPELINE_DONE", f"bid:{bid.id}",
                  f"score={assessment['score']} risk={assessment['risk']}")
    except Exception as e:  # keep the demo alive; surface the error in UI + audit
        db.rollback()
        bid = db.get(Bid, bid_id)
        if bid:
            bid.pipeline_status = "ERROR"
            db.commit()
        log_event(db, "system", "PIPELINE_ERROR", f"bid:{bid_id}", str(e))
    finally:
        db.close()
