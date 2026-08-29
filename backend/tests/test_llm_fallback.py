import os

from app.pipeline.recommend import recommend
from app.pipeline.tender_extract import extract_requirements

os.environ.pop("GEMINI_API_KEY", None)

TENDER_SNIPPET = """
The bidder must possess GST registration and PAN. The agency must hold a valid
licence under PSARA Act 2005. EPF and ESI registration mandatory. The bidder
should not be blacklisted by any government department.
"""


def test_requirement_extraction_fallback_offline():
    reqs = extract_requirements(TENDER_SNIPPET)
    keys = {r["rule_key"] for r in reqs}
    assert {"gst_active", "pan_valid", "psara_license", "epfo_valid", "not_blacklisted"} <= keys
    assert all(r["text"] for r in reqs)


def test_recommendation_fallback_offline():
    results = [
        {"requirement_key": "gst_active", "requirement_text": "GST", "status": "Compliant",
         "reason": "match", "rule_id": "R-GST-01", "critical": True},
        {"requirement_key": "psara_license", "requirement_text": "PSARA licence",
         "status": "Non-Compliant", "reason": "Mandatory document PSARA_LICENSE was not submitted",
         "rule_id": "R-PSARA-01", "critical": True},
    ]
    rec = recommend("Apex Guarding Co", results, {"score": 40.0, "risk": "High"})
    assert "High" in rec["text"]
    assert "Procurement Officer" in rec["text"]
    assert rec["grounded_refs"] == ["R-GST-01", "R-PSARA-01"]
