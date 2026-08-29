"""Configurable compliance score and risk (FR-S01..04, SRS §9).

Score = Σ(weight × value) / Σ(weight) × 100
Compliant = 1, Review Required = 0.5, Non-Compliant = 0.
Not Applicable excluded. Verification Unavailable follows the explicit
policy value 0.5 (counts like Review — never a silent pass).
Score/risk is decision support only; qualification is the officer's call.
"""
from app.pipeline.rules import COMPLIANT, NON_COMPLIANT, NOT_APPLICABLE, REVIEW, UNAVAILABLE

STATUS_VALUE = {COMPLIANT: 1.0, REVIEW: 0.5, UNAVAILABLE: 0.5, NON_COMPLIANT: 0.0}


def score(results: list[dict]) -> dict:
    applicable = [r for r in results if r["status"] != NOT_APPLICABLE]
    total_w = sum(r["weight"] for r in applicable)
    pts = sum(r["weight"] * STATUS_VALUE[r["status"]] for r in applicable)
    pct = round(pts / total_w * 100, 1) if total_w else 0.0

    critical_fail = [r for r in applicable if r["critical"] and r["status"] == NON_COMPLIANT]
    reviews = [r for r in applicable if r["status"] in (REVIEW, UNAVAILABLE)]
    non_critical_fail = [r for r in applicable if not r["critical"] and r["status"] == NON_COMPLIANT]

    if critical_fail:
        risk = "High"
    elif non_critical_fail or len(reviews) >= 2:
        risk = "Medium"
    elif reviews:
        risk = "Medium" if any(r["critical"] for r in reviews) else "Low"
    else:
        risk = "Low"

    factors = (
        [f"CRITICAL FAILURE: {r['requirement_key']} — {r['reason']}" for r in critical_fail]
        + [f"Non-compliant: {r['requirement_key']} — {r['reason']}" for r in non_critical_fail]
        + [f"Needs review: {r['requirement_key']} — {r['reason']}" for r in reviews]
    ) or ["All applicable requirements compliant"]

    return {"score": pct, "risk": risk, "factors": factors}
