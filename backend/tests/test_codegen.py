"""Generated code must compile, run sandboxed, and agree with the built-in
executors on the full verdict matrix."""
import pytest

from app.pipeline.codegen import generate_code, run_generated
from app.pipeline.rule_forge import evaluate_dynamic

PROFILE = {"company_profile.pdf": """Company Profile & Tender Declarations
Average Annual Turnover  Rs. 6.20 Crores (last three years)
Work Experience  8 years similar security services; certificates enclosed
Earnest Money Deposit  Demand Draft for Rs. 6,55,000 enclosed
Wages Compliance  Rates comply with notified minimum wages
"""}
UNRELATED = {"gst.pdf": "GST Registration Certificate 07AAECS1234F1Z5"}

RULES = [
    {"rule_type": "THRESHOLD", "keywords": ["turnover"], "threshold": 20_000_000.0,
     "unit": "crore", "comparator": ">=", "critical": False, "legal_basis": None},
    {"rule_type": "THRESHOLD", "keywords": ["turnover"], "threshold": 100_000_000.0,
     "unit": "crore", "comparator": ">=", "critical": False, "legal_basis": None},
    {"rule_type": "DOC_PRESENCE", "keywords": ["earnest", "money", "deposit"],
     "threshold": None, "unit": "", "comparator": ">=", "critical": False,
     "legal_basis": {"source": "General Financial Rules 2017", "provision": "Rule 170",
                     "title": "Bid Security"}},
    {"rule_type": "DECLARATION", "keywords": ["wages"], "threshold": None,
     "unit": "", "comparator": ">=", "critical": False, "legal_basis": None},
]


@pytest.mark.parametrize("rule", RULES)
@pytest.mark.parametrize("docs", [PROFILE, UNRELATED])
def test_generated_code_matches_builtin_executor(rule, docs):
    code = generate_code(rule, "R-DYN-TEST", "test clause")
    generated = run_generated(code, docs)
    builtin = evaluate_dynamic(rule, docs)
    assert generated["status"] == builtin["status"]
    assert generated["evidence"].keys() == builtin["evidence"].keys()


def test_generated_code_is_sandboxed():
    evil = "def check(doc_texts):\n    return open('/etc/passwd').read()"
    with pytest.raises(Exception):
        run_generated(evil, PROFILE)
    evil2 = "import os\ndef check(doc_texts):\n    return {}"
    with pytest.raises(Exception):
        run_generated(evil2, PROFILE)


def test_generated_code_carries_clause_and_legal_basis():
    code = generate_code(RULES[2], "R-DYN-7", "EMD must be submitted")
    assert "R-DYN-7" in code
    assert "General Financial Rules 2017, Rule 170" in code
    assert "EMD must be submitted" in code
    assert "def check(doc_texts):" in code
