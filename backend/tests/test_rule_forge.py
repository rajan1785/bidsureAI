import os

from app.pipeline.rule_forge import draft_rule, evaluate_dynamic
from app.pipeline.tender_extract import extract_custom_clauses

os.environ.pop("GEMINI_API_KEY", None)

PROFILE_TEXT = """SHAKTI FACILITY SERVICES PRIVATE LIMITED
Company Profile & Tender Declarations
Average Annual Turnover  Rs. 6.20 Crores (last three years)
Work Experience  8 years similar security services; certificates enclosed
Earnest Money Deposit  Demand Draft for Rs. 6,55,000 enclosed
Wages Compliance  Rates comply with notified minimum wages
"""


def test_draft_threshold_rule_from_numeric_clause():
    d = draft_rule("Minimum average annual turnover of Rs 2 crore in last three years")
    assert d["rule_type"] == "THRESHOLD"
    assert d["threshold"] == 20_000_000
    assert "turnover" in d["keywords"]


def test_draft_presence_rule_from_certificate_clause():
    d = draft_rule("Bidder must submit work experience certificates for similar services")
    assert d["rule_type"] == "DOC_PRESENCE"
    assert "experience" in d["keywords"]


def test_draft_declaration_rule_otherwise():
    d = draft_rule("Quoted rates must not be below the government-notified minimum wages")
    assert d["rule_type"] == "DECLARATION"
    assert "wages" in d["keywords"]


def test_threshold_executor_pass_and_fail():
    rule = {"rule_type": "THRESHOLD", "keywords": ["turnover"], "threshold": 20_000_000,
            "unit": "crore", "comparator": ">=", "critical": False}
    ok = evaluate_dynamic(rule, {"profile.pdf": PROFILE_TEXT})
    assert ok["status"] == "Compliant"
    assert ok["evidence"]["value"] == 62_000_000
    strict = {**rule, "threshold": 100_000_000}
    fail = evaluate_dynamic(strict, {"profile.pdf": PROFILE_TEXT})
    assert fail["status"] == "Non-Compliant"


def test_missing_evidence_never_silently_passes():
    rule = {"rule_type": "THRESHOLD", "keywords": ["turnover"], "threshold": 20_000_000,
            "unit": "crore", "comparator": ">=", "critical": False}
    out = evaluate_dynamic(rule, {"gst.pdf": "GST Registration Certificate 07AAECS1234F1Z5"})
    assert out["status"] == "Review Required"


def test_presence_and_declaration_executors():
    presence = {"rule_type": "DOC_PRESENCE", "keywords": ["earnest", "money", "deposit"],
                "threshold": None, "unit": "", "comparator": ">=", "critical": False}
    assert evaluate_dynamic(presence, {"profile.pdf": PROFILE_TEXT})["status"] == "Compliant"
    assert evaluate_dynamic(presence, {"x.pdf": "unrelated"})["status"] == "Review Required"

    decl = {"rule_type": "DECLARATION", "keywords": ["wages"], "threshold": None,
            "unit": "", "comparator": ">=", "critical": False}
    assert evaluate_dynamic(decl, {"profile.pdf": PROFILE_TEXT})["status"] == "Compliant"


def test_custom_clauses_found_in_tender_style_text():
    text = """Earnest Money Deposit (EMD) Rs.6,55,000/- in form of Demand Draft.
    Work Experience Certificate to be submitted with Technical Bid.
    L1 decided on criteria of average maximum turnover of the firm.
    Rates shall not be less than basic minimum wages laid down by Government."""
    reqs = extract_custom_clauses(text)
    assert len(reqs) == 4
    assert all(r["rule_key"] == "" for r in reqs)
    assert any("Earnest Money" in r["text"] for r in reqs)


def test_rulebook_grounding():
    from app.pipeline.rule_forge import match_rulebook
    emd = match_rulebook("Earnest Money Deposit (EMD) must be submitted (Rs.6,55,000/-)")
    assert emd and emd["provision"] == "Rule 170"
    exp = match_rulebook("Bidder must submit work experience certificates for similar services")
    assert exp and exp["provision"] == "Rule 173"
    wages = match_rulebook("Quoted rates must not be below the government-notified minimum wages")
    assert wages and wages["source"] == "Minimum Wages Act 1948"
    assert match_rulebook("bidder must own a purple elephant") is None


def test_drafted_rule_carries_legal_basis():
    d = draft_rule("Earnest Money Deposit (EMD) must be submitted as specified in the tender")
    assert d["legal_basis"]["source"] == "General Financial Rules 2017"
