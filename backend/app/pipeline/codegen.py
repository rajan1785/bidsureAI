"""Code generation for drafted rules: every custom clause gets its own
generated Python check function.

The source is rendered deterministically from the drafted rule definition,
shown to the officer for review, and executed in a restricted sandbox
(no imports, no file/network access, whitelisted builtins only). If the
generated code ever fails at runtime, the pipeline falls back to the
built-in executor for the same rule type — the demo can never crash here.
"""
import re

SAFE_GLOBALS = {"re": re, "float": float, "len": len, "max": max, "min": min,
                "abs": abs, "str": str, "round": round, "__builtins__": {}}

_NUM_HELPER = '''\
def _parse_number(raw, unit):
    n = float(raw.replace(",", ""))
    unit = (unit or "").lower()
    if unit.startswith("lakh"):
        n = n * 100000
    elif unit.startswith("crore"):
        n = n * 10000000
    return n
'''

_HELPERS = '''\
def _find_hits(doc_texts, keywords):
    # evidence: one matched clause PHRASE, or 2-of-N distinct keywords
    need = min(2, len(keywords))
    hits = []
    for fname, text in doc_texts.items():
        low = text.lower()
        matched = [kw for kw in keywords if re.search("\\\\b" + re.escape(kw), low)]
        phrase = [m for m in matched if " " in m]
        if phrase or len(matched) >= need:
            hits.append((fname, phrase[0] if phrase else matched[0]))
    return hits
'''

_NUM_PATTERN = r"(?:rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores|%|percent|years?)?"


def generate_code(rule: dict, rule_label: str, clause: str) -> str:
    """Render self-contained Python source for this rule's check(doc_texts)."""
    lb = rule.get("legal_basis")
    basis = f"{lb['source']}, {lb['provision']}" if lb else "tender-specific clause"
    rule_def = {
        "id": rule_label, "engine": "BidSure Rule Composer (dyn-v1)",
        "check_type": rule["rule_type"], "critical": bool(rule.get("critical")),
        "weight": rule.get("weight", 1), "threshold": rule.get("threshold"),
        "unit": rule.get("unit") or None, "comparator": rule.get("comparator", ">="),
        "legal_basis": basis,
    }
    header = (
        f'"""Verification code for {rule_label} - rendered by the Rule Composer\n'
        f"from the rule definition below; runs sandboxed in the compliance\n"
        f"pipeline (built-in executor is the fallback).\n"
        f"Clause: {clause[:120]}\n"
        f'"""\n'
        f"RULE = {rule_def!r}\n"
        f"KEYWORDS = {[k.lower() for k in rule['keywords']]!r}  # evidence phrases from the clause\n"
    )

    if rule["rule_type"] == "THRESHOLD" and rule.get("threshold") is not None:
        body = f'''THRESHOLD = {float(rule["threshold"])!r}
UNIT = {rule.get("unit", "")!r}

{_NUM_HELPER}

{_HELPERS}

def check(doc_texts):
    hits = _find_hits(doc_texts, KEYWORDS)
    for fname, kw in hits:
        low = doc_texts[fname].lower()
        for m in re.finditer(re.escape(kw), low):
            window = doc_texts[fname][max(0, m.start() - 60): m.end() + 120]
            nm = re.search({_NUM_PATTERN!r}, window, re.I)
            if nm:
                value = _parse_number(nm.group(1), nm.group(2))
                if value {rule.get("comparator", ">=")} THRESHOLD:
                    return {{"status": "Compliant",
                             "reason": "Found " + str(value) + " " + UNIT + " near '" + kw + "' in " + fname + " - meets {rule.get("comparator", ">=")} " + str(THRESHOLD),
                             "evidence": {{"document": fname, "keyword": kw, "value": value}}}}
                return {{"status": "Non-Compliant",
                         "reason": "Found " + str(value) + " " + UNIT + " near '" + kw + "' in " + fname + " - fails {rule.get("comparator", ">=")} " + str(THRESHOLD),
                         "evidence": {{"document": fname, "keyword": kw, "value": value}}}}
    return {{"status": "Review Required",
             "reason": "No numeric evidence found in submitted documents - manual verification required",
             "evidence": {{"keywords": KEYWORDS}}}}
'''
    elif rule["rule_type"] == "DOC_PRESENCE":
        miss = "Non-Compliant" if rule.get("critical") else "Review Required"
        body = f'''{_HELPERS}

def check(doc_texts):
    hits = _find_hits(doc_texts, KEYWORDS)
    if hits:
        fname, kw = hits[0]
        return {{"status": "Compliant",
                 "reason": "Supporting document evidence found in " + fname + " (matched '" + kw + "')",
                 "evidence": {{"document": fname, "keyword": kw}}}}
    return {{"status": {miss!r},
             "reason": "Required supporting document not found among submitted files",
             "evidence": {{"keywords": KEYWORDS}}}}
'''
    else:  # DECLARATION
        body = f'''{_HELPERS}

def check(doc_texts):
    hits = _find_hits(doc_texts, KEYWORDS)
    if hits:
        fname, kw = hits[0]
        return {{"status": "Compliant",
                 "reason": "Declaration/evidence present in " + fname + " (matched '" + kw + "')",
                 "evidence": {{"document": fname, "keyword": kw}}}}
    return {{"status": "Review Required",
             "reason": "No declaration found in submitted documents - manual verification required",
             "evidence": {{"keywords": KEYWORDS}}}}
'''
    return header + body


def run_generated(code: str, doc_texts: dict[str, str]) -> dict:
    """Execute generated check() in a restricted namespace. Raises on failure —
    the caller decides the fallback (built-in executor)."""
    ns: dict = dict(SAFE_GLOBALS)
    exec(compile(code, "<generated-rule>", "exec"), ns)  # noqa: S102
    result = ns["check"](doc_texts)
    if not (isinstance(result, dict) and result.get("status") and result.get("reason")):
        raise ValueError("generated check() returned invalid result")
    return result
