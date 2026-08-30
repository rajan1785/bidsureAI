"""Deterministic compliance rules engine (FR-R01..05).

Statuses: Compliant | Review Required | Non-Compliant | Not Applicable |
Verification Unavailable. Missing mandatory evidence can never be Compliant
(FR-R05); an unavailable source never silently passes (FR-G04).
"""
from pathlib import Path

import yaml

RULESETS_DIR = Path(__file__).parents[1] / "rulesets"

COMPLIANT = "Compliant"
REVIEW = "Review Required"
NON_COMPLIANT = "Non-Compliant"
NOT_APPLICABLE = "Not Applicable"
UNAVAILABLE = "Verification Unavailable"


def load_ruleset(name: str = "security_tender_v1") -> dict:
    return yaml.safe_load((RULESETS_DIR / f"{name}.yaml").read_text())


def filter_ruleset(ruleset: dict, approved_rule_keys: set[str]) -> dict:
    """Keep only rules whose requirement the officer approved (FR-T05/T06).

    An empty key set means the tender has no rule-linked approved requirements
    (legacy data); fall back to the full ruleset rather than evaluating nothing.
    """
    if not approved_rule_keys:
        return ruleset
    return {
        **ruleset,
        "rules": [r for r in ruleset["rules"] if r["requirement_key"] in approved_rule_keys],
    }


def evaluate(ruleset: dict, checks: list[dict], docs_present: list[str]) -> list[dict]:
    """checks: output of crosscheck(). docs_present: doc types uploaded.

    Returns one result per rule:
    {requirement_key, requirement_text, status, reason, rule_id, rule_version,
     critical, weight, evidence}
    """
    version = ruleset.get("version", "v1")
    by_check = {c["check"]: c for c in checks}
    results = []

    for rule in ruleset["rules"]:
        check = by_check.get(rule["check"])
        evidence = dict(check) if check else {}
        if rule.get("legal_basis"):
            evidence["legal_basis"] = rule["legal_basis"]
        base = {
            "requirement_key": rule["requirement_key"],
            "requirement_text": rule["text"],
            "rule_id": rule["id"],
            "rule_version": version,
            "critical": bool(rule.get("critical")),
            "weight": rule.get("weight", 1),
            "evidence": evidence,
        }

        mandatory_doc = rule.get("mandatory_doc")
        optional = rule.get("optional", False)

        # Missing mandatory document -> Non-Compliant (FR-R05)
        if mandatory_doc and mandatory_doc not in docs_present:
            if optional:
                results.append({**base, "status": NOT_APPLICABLE,
                                "reason": f"Optional document {mandatory_doc} not submitted"})
            else:
                results.append({**base, "status": NON_COMPLIANT,
                                "reason": f"Mandatory document {mandatory_doc} was not submitted"})
            continue

        if check is None:
            results.append({**base, "status": UNAVAILABLE,
                            "reason": "No verification data produced for this requirement"})
            continue

        outcome = check["outcome"]

        if rule["check"] == "local_content":
            if outcome == "MISSING":
                results.append({**base, "status": NOT_APPLICABLE,
                                "reason": "No local content declaration submitted; requirement treated as not applicable for prototype"})
            else:
                pct = int(check["doc_value"])
                threshold = rule.get("threshold", 50)
                if pct >= threshold:
                    results.append({**base, "status": COMPLIANT,
                                    "reason": f"Declared local content {pct}% meets threshold {threshold}%"})
                else:
                    results.append({**base, "status": NON_COMPLIANT,
                                    "reason": f"Declared local content {pct}% is below threshold {threshold}%"})
            continue

        if rule["check"] == "blacklist":
            if outcome == "HIT":
                results.append({**base, "status": NON_COMPLIANT, "reason": check["note"]})
            elif outcome == "SOURCE_UNAVAILABLE":
                results.append({**base, "status": UNAVAILABLE, "reason": check["note"]})
            else:
                results.append({**base, "status": COMPLIANT, "reason": check["note"]})
            continue

        mapping = {
            "MATCH": (COMPLIANT, check["note"] or "Document value matches government record"),
            "MISMATCH": (REVIEW, f"Discrepancy found: {check['note']}"),
            "EXPIRED": (REVIEW, f"Validity issue: {check['note']}"),
            "MISSING": (NON_COMPLIANT if not optional else NOT_APPLICABLE,
                        f"Required evidence missing: {check['note']}"),
            "SOURCE_UNAVAILABLE": (UNAVAILABLE, check["note"]),
            "HIT": (NON_COMPLIANT, check["note"]),
        }
        status, reason = mapping[outcome]
        results.append({**base, "status": status, "reason": reason})

    return results
