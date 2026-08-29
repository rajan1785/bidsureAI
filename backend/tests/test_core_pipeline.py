"""Core correctness matrix: Bidders A (pass), B (review), C (fail) + guardrails."""
from datetime import date

from app.pipeline.crosscheck import crosscheck
from app.pipeline.rules import (
    COMPLIANT,
    NON_COMPLIANT,
    NOT_APPLICABLE,
    REVIEW,
    UNAVAILABLE,
    evaluate,
    load_ruleset,
)
from app.pipeline.scoring import score

TODAY = date(2026, 8, 30)
RULESET = load_ruleset()


def f(field, value):
    return {"field": field, "value": value, "confidence": 0.95, "evidence_location": "chars 0-1"}


def govt(source, fetch="SUCCESS", **payload):
    return {"source": source, "identifier": "x", "status": fetch, "payload": payload, "mock": True}


# ---------- Bidder A: everything clean ----------
A_EXTRACTED = {
    "GST_CERT": [f("gstin", "07AAECS1234F1Z5")],
    "PAN_CARD": [f("pan", "AAECS1234F")],
    "UDYAM_CERT": [f("udyam", "UDYAM-DL-01-0012345")],
    "EPFO_REG": [f("epfo_code", "DLCPM0012345000"), f("valid_until", "31/03/2027")],
    "PSARA_LICENSE": [f("license_no", "PSARA/DL/2023/04412"), f("valid_until", "31/12/2026")],
}
A_REGISTERED = {"gstin": "07AAECS1234F1Z5", "pan": "AAECS1234F",
                "udyam": "UDYAM-DL-01-0012345", "epfo_code": "DLCPM0012345000"}
A_GOVT = [
    govt("GST", **{"status": "Active"}),
    govt("PAN", **{"status": "Valid"}),
    govt("UDYAM", **{"status": "Active"}),
    govt("EPFO", **{"status": "Active", "valid_until": "2027-03-31"}),
    {"source": "BLACKLIST", "identifier": "AAECS1234F", "status": "SUCCESS",
     "payload": {"records": [], "clean": True}, "mock": True},
]


def _eval(extracted, registered, govt_records):
    checks = crosscheck(extracted, registered, govt_records, today=TODAY)
    results = evaluate(RULESET, checks, list(extracted.keys()))
    return results, score(results)


def test_bidder_a_all_compliant_low_risk():
    results, s = _eval(A_EXTRACTED, A_REGISTERED, A_GOVT)
    statuses = {r["requirement_key"]: r["status"] for r in results}
    assert statuses["gst_active"] == COMPLIANT
    assert statuses["pan_valid"] == COMPLIANT
    assert statuses["udyam_valid"] == COMPLIANT
    assert statuses["epfo_valid"] == COMPLIANT
    assert statuses["psara_license"] == COMPLIANT
    assert statuses["not_blacklisted"] == COMPLIANT
    assert statuses["local_content"] == NOT_APPLICABLE
    assert s["score"] >= 90
    assert s["risk"] == "Low"


# ---------- Bidder B: GSTIN mismatch + expired EPFO ----------
B_EXTRACTED = {
    "GST_CERT": [f("gstin", "07AAFCN5678K1Z3")],  # cert shows wrong last char
    "PAN_CARD": [f("pan", "AAFCN5678K")],
    "UDYAM_CERT": [f("udyam", "UDYAM-DL-02-0023456")],
    "EPFO_REG": [f("epfo_code", "DLCPM0023456000"), f("valid_until", "31/03/2026")],
    "PSARA_LICENSE": [f("license_no", "PSARA/DL/2022/01199"), f("valid_until", "30/06/2027")],
}
B_REGISTERED = {"gstin": "07AAFCN5678K1Z9", "pan": "AAFCN5678K",
                "udyam": "UDYAM-DL-02-0023456", "epfo_code": "DLCPM0023456000"}
B_GOVT = [
    govt("GST", **{"status": "Active"}),
    govt("PAN", **{"status": "Valid"}),
    govt("UDYAM", **{"status": "Active"}),
    govt("EPFO", **{"status": "Active", "valid_until": "2026-03-31"}),
    {"source": "BLACKLIST", "identifier": "AAFCN5678K", "status": "SUCCESS",
     "payload": {"records": [], "clean": True}, "mock": True},
]


def test_bidder_b_review_medium_risk():
    results, s = _eval(B_EXTRACTED, B_REGISTERED, B_GOVT)
    statuses = {r["requirement_key"]: r["status"] for r in results}
    assert statuses["gst_active"] == REVIEW  # mismatch -> review, not compliant
    assert statuses["epfo_valid"] == REVIEW  # expired -> review
    assert statuses["pan_valid"] == COMPLIANT
    assert 50 <= s["score"] <= 85
    assert s["risk"] == "Medium"


# ---------- Bidder C: missing mandatory PSARA + blacklist hit ----------
C_EXTRACTED = {
    "GST_CERT": [f("gstin", "07AAKCA9012M1Z7")],
    "PAN_CARD": [f("pan", "AAKCA9012M")],
    "UDYAM_CERT": [f("udyam", "UDYAM-DL-03-0034567")],
    "EPFO_REG": [f("epfo_code", "DLCPM0034567000"), f("valid_until", "31/03/2027")],
    # no PSARA_LICENSE submitted
}
C_REGISTERED = {"gstin": "07AAKCA9012M1Z7", "pan": "AAKCA9012M",
                "udyam": "UDYAM-DL-03-0034567", "epfo_code": "DLCPM0034567000"}
C_GOVT = [
    govt("GST", **{"status": "Active"}),
    govt("PAN", **{"status": "Valid"}),
    govt("UDYAM", **{"status": "Active"}),
    govt("EPFO", **{"status": "Active", "valid_until": "2027-03-31"}),
    {"source": "BLACKLIST", "identifier": "AAKCA9012M", "status": "SUCCESS",
     "payload": {"records": [{"authority": "GeM", "status": "Active",
                              "debarment_end": "2027-10-31"}], "clean": False}, "mock": True},
]


def test_bidder_c_non_compliant_high_risk():
    results, s = _eval(C_EXTRACTED, C_REGISTERED, C_GOVT)
    statuses = {r["requirement_key"]: r["status"] for r in results}
    assert statuses["psara_license"] == NON_COMPLIANT  # FR-R05: missing mandatory doc
    assert statuses["not_blacklisted"] == NON_COMPLIANT
    assert s["risk"] == "High"
    assert s["score"] < 75


# ---------- Guardrails ----------
def test_missing_mandatory_never_compliant():
    results, _ = _eval(C_EXTRACTED, C_REGISTERED, C_GOVT)
    psara = next(r for r in results if r["requirement_key"] == "psara_license")
    assert psara["status"] != COMPLIANT
    assert "not submitted" in psara["reason"]


def test_unavailable_source_never_silently_passes():
    govt_down = [g for g in A_GOVT if g["source"] != "GST"] + [govt("GST", fetch="UNAVAILABLE")]
    results, s = _eval(A_EXTRACTED, A_REGISTERED, govt_down)
    gst = next(r for r in results if r["requirement_key"] == "gst_active")
    assert gst["status"] == UNAVAILABLE
    assert s["score"] < 100  # cannot be a full pass


def test_every_result_has_rule_id_version_and_reason():
    results, _ = _eval(A_EXTRACTED, A_REGISTERED, A_GOVT)
    for r in results:
        assert r["rule_id"] and r["rule_version"] == "v1" and r["reason"]
