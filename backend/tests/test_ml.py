"""Trained classifier, semantic rulebook matching, and RAG retrieval."""
from app.pipeline.classify import classify_doc, classify_doc_ml
from app.pipeline.recommend import _retrieve_evidence
from app.pipeline.rule_forge import match_rulebook

GST_TEXT = """Government of India Form GST REG-06
Goods and Services Tax Registration Certificate
Registration Number (GSTIN): 07AAECS1234F1Z5
Legal Name: SHAKTI FACILITY SERVICES PRIVATE LIMITED"""

PROFILE_TEXT = """SHAKTI FACILITY SERVICES PRIVATE LIMITED
Company Profile & Tender Declarations
Average Annual Turnover: Rs. 6.20 Crores
Earnest Money Deposit: Demand Draft for Rs. 6,55,000 enclosed"""

INVOICE_TEXT = """TAX INVOICE
Invoice No: INV-4521
Total Amount: Rs. 45000
Thank you for your business"""


def test_trained_model_classifies_with_confidence():
    label, conf = classify_doc_ml(GST_TEXT)
    assert label == "GST_CERT"
    assert conf > 0.5
    label, conf = classify_doc_ml(PROFILE_TEXT)
    assert label == "COMPANY_PROFILE"


def test_model_first_pipeline_still_correct():
    assert classify_doc(GST_TEXT) == "GST_CERT"
    assert classify_doc(INVOICE_TEXT) == "OTHER"


def test_semantic_rulebook_match_without_keywords():
    # phrased with none of the provision's keyword strings present
    lb = match_rulebook(
        "the successful vendor shall furnish a guarantee from a scheduled bank "
        "valid till two months after the contract obligations end")
    assert lb is not None
    assert lb["matched_via"] == "semantic"
    assert "GeM GTC" in lb["source"]


def test_semantic_match_rejects_unrelated_clause():
    assert match_rulebook("the office canteen shall serve tea at 4 pm") is None


def test_rag_retrieves_relevant_chunk():
    results = [{"requirement_key": "custom_1", "status": "Review Required",
                "requirement_text": "Earnest Money Deposit (EMD) must be submitted",
                "reason": "x", "rule_id": "R-DYN-1", "critical": False}]
    doc_texts = {"profile.pdf": PROFILE_TEXT, "invoice.pdf": INVOICE_TEXT}
    lines = _retrieve_evidence(results, doc_texts)
    assert lines and "profile.pdf" in " ".join(lines)
    assert "Earnest Money" in " ".join(lines) or "Demand Draft" in " ".join(lines)
