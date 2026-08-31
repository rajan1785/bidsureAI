"""Rule forge: drafts new rules for tender clauses no built-in rule covers.

Drafting is AI-assisted (LLM when available) with a deterministic clause-parser
fallback, so it works offline. Drafted rules NEVER run on their own: the officer
approves them on the requirement-review screen first, and execution is handled
by three generic deterministic executors (doc presence / threshold / declaration)
so every verdict stays reproducible and auditable.
"""
import json
import re
from pathlib import Path

from app.llm import llm_json

RULE_TYPES = ("DOC_PRESENCE", "THRESHOLD", "DECLARATION")

RULEBOOK = json.loads(
    (Path(__file__).parents[1] / "rulesets" / "govt_rulebook.json").read_text()
)["provisions"]


def match_rulebook(clause: str) -> dict | None:
    """Find the government rulebook provision backing a clause (keyword scoring).

    Returns {source, provision, title} or None — a drafted rule with no matching
    provision is still valid (tender-specific), it just cites the tender itself.
    """
    low = clause.lower()
    best, best_score = None, 0
    for prov in RULEBOOK:
        score = sum(1 for k in prov["keywords"] if k in low)
        if score > best_score:
            best, best_score = prov, score
    if best is not None:
        return {"source": best["source"], "provision": best["provision"],
                "title": best["title"], "matched_via": "keyword"}
    # No keyword hit: semantic match with the local embedding model (RAG over
    # the rulebook). High threshold so unrelated clauses stay unmatched.
    try:
        from app.ml.embedder import top_k
        corpus = [f"{p['title']}. {p['summary']}" for p in RULEBOOK]
        hits = top_k(clause, corpus, k=1)
        if hits and hits[0][1] >= 0.35:
            prov = RULEBOOK[hits[0][0]]
            return {"source": prov["source"], "provision": prov["provision"],
                    "title": prov["title"], "matched_via": "semantic"}
    except Exception:
        pass
    return None

_NUM = r"(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores|%|percent|years?)?"

_DOC_WORDS = re.compile(
    r"certificate|licen[cs]e|registration copy|demand draft|submit|attach|copy of|annexure",
    re.I,
)

_STOPWORDS = {
    "the", "of", "in", "to", "a", "an", "and", "or", "for", "with", "must", "shall",
    "be", "by", "is", "are", "will", "should", "not", "less", "than", "at", "least",
    "minimum", "maximum", "bidder", "bidders", "firm", "agency", "tender", "last",
    "three", "two", "one", "along", "form", "may", "any", "all", "have", "has",
    "demonstrate", "required", "specified", "submitted", "submit", "quoted",
    "rates", "below", "government", "notified", "services", "this", "that",
    "comply", "against", "under", "upon", "successful", "furnish",
}


def _keywords(text: str, limit: int = 4) -> list[str]:
    words = re.findall(r"[A-Za-z]{4,}", text.lower())
    seen, out = set(), []
    for w in words:
        if w in _STOPWORDS or w in seen:
            continue
        seen.add(w)
        out.append(w)
        if len(out) >= limit:
            break
    return out


def _to_number(raw: str, unit: str | None) -> float:
    n = float(raw.replace(",", ""))
    unit = (unit or "").lower()
    if unit.startswith("lakh"):
        n *= 100_000
    elif unit.startswith("crore"):
        n *= 10_000_000
    return n


DRAFT_PROMPT = """You design compliance rules for an Indian government tender platform.
For the clause below, return ONLY JSON:
{{"rule_type": "DOC_PRESENCE|THRESHOLD|DECLARATION", "keywords": ["..."],
"threshold": number or null, "unit": "rupees|percent|years|" , "comparator": ">=|<=",
"reason_hint": "..."}}
DOC_PRESENCE = a specific document/certificate must be uploaded.
THRESHOLD = a numeric minimum/maximum must be met.
DECLARATION = bidder must declare/confirm something (no number, no specific document).
Clause: {clause}
"""


def draft_rule(clause: str) -> dict:
    """Returns {rule_type, keywords, threshold, unit, comparator, legal_basis}."""
    legal_basis = match_rulebook(clause)
    out = llm_json(DRAFT_PROMPT.format(clause=clause[:400]),
                   f"rule_draft_{abs(hash(clause)) % 10**10}", feature="draft")
    if isinstance(out, dict) and out.get("rule_type") in RULE_TYPES and out.get("keywords"):
        return {
            "rule_type": out["rule_type"],
            "keywords": [str(k).lower() for k in out["keywords"]][:5],
            "threshold": out.get("threshold"),
            "unit": out.get("unit") or "",
            "comparator": out.get("comparator") or ">=",
            "legal_basis": legal_basis,
        }

    # Deterministic fallback drafter
    m = re.search(_NUM, clause, re.I)
    has_number = m and m.group(2)  # a number WITH a unit is a real threshold
    if has_number:
        return {
            "rule_type": "THRESHOLD",
            "keywords": _keywords(clause),
            "threshold": _to_number(m.group(1), m.group(2)),
            "unit": (m.group(2) or "").lower().rstrip("s"),
            "comparator": ">=",
            "legal_basis": legal_basis,
        }
    if _DOC_WORDS.search(clause):
        return {"rule_type": "DOC_PRESENCE", "keywords": _keywords(clause),
                "threshold": None, "unit": "", "comparator": ">=",
                "legal_basis": legal_basis}
    return {"rule_type": "DECLARATION", "keywords": _keywords(clause),
            "threshold": None, "unit": "", "comparator": ">=",
            "legal_basis": legal_basis}


# ---------------------------------------------------------------- execution

COMPLIANT = "Compliant"
REVIEW = "Review Required"
NON_COMPLIANT = "Non-Compliant"


def _find_number_near(text: str, keyword: str, unit: str) -> float | None:
    low = text.lower()
    for m in re.finditer(re.escape(keyword.lower()), low):
        window = text[max(0, m.start() - 60): m.end() + 120]
        nm = re.search(_NUM, window, re.I)
        if nm:
            found_unit = (nm.group(2) or "").lower().rstrip("s")
            if unit in ("", "rupee") or not unit or found_unit in (unit, ""):
                try:
                    return _to_number(nm.group(1), nm.group(2))
                except ValueError:
                    continue
    return None


def evaluate_dynamic(rule: dict, doc_texts: dict[str, str]) -> dict:
    """rule: {rule_type, keywords, threshold, unit, comparator, critical}.
    doc_texts: {filename: extracted text}. Returns {status, reason, evidence}.
    Missing evidence -> Review Required (never a silent pass, FR-G04 spirit)."""
    keywords = [k.lower() for k in rule["keywords"]]
    # A document qualifies only if it matches enough DISTINCT keywords
    # (2-of-N for multi-keyword rules) — one generic word is not evidence.
    need = min(2, len(keywords))
    hits = []  # (filename, first matched keyword) per qualifying document
    for fname, text in doc_texts.items():
        low = text.lower()
        matched = [k for k in keywords if re.search(rf"\b{re.escape(k)}", low)]
        if len(matched) >= need:
            hits.append((fname, matched[0]))

    if rule["rule_type"] == "THRESHOLD" and rule.get("threshold") is not None:
        for fname, k in hits:
            value = _find_number_near(doc_texts[fname], k, rule.get("unit", ""))
            if value is not None:
                ok = value >= rule["threshold"] if rule.get("comparator", ">=") == ">=" \
                    else value <= rule["threshold"]
                unit = rule.get("unit", "")
                if ok:
                    return {"status": COMPLIANT,
                            "reason": f"Found {value:g} {unit} near '{k}' in {fname} — meets {rule['comparator']} {rule['threshold']:g} {unit}",
                            "evidence": {"document": fname, "keyword": k, "value": value}}
                return {"status": NON_COMPLIANT,
                        "reason": f"Found {value:g} {unit} near '{k}' in {fname} — fails {rule['comparator']} {rule['threshold']:g} {unit}",
                        "evidence": {"document": fname, "keyword": k, "value": value}}
        return {"status": REVIEW,
                "reason": "No numeric evidence found in submitted documents — manual verification required",
                "evidence": {"keywords": keywords}}

    if rule["rule_type"] == "DOC_PRESENCE":
        if hits:
            fname, k = hits[0]
            return {"status": COMPLIANT,
                    "reason": f"Supporting document evidence found in {fname} (matched '{k}')",
                    "evidence": {"document": fname, "keyword": k}}
        return {"status": NON_COMPLIANT if rule.get("critical") else REVIEW,
                "reason": "Required supporting document not found among submitted files",
                "evidence": {"keywords": keywords}}

    # DECLARATION
    if hits:
        fname, k = hits[0]
        return {"status": COMPLIANT,
                "reason": f"Declaration/evidence present in {fname} (matched '{k}')",
                "evidence": {"document": fname, "keyword": k}}
    return {"status": REVIEW,
            "reason": "No declaration found in submitted documents — manual verification required",
            "evidence": {"keywords": keywords}}
