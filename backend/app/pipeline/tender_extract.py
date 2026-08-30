"""Tender requirement extraction (FR-T04): LLM-assisted with a
deterministic keyword fallback so any tender still produces a usable,
officer-editable requirement list offline."""
from app.llm import llm_json

# fallback: keyword -> (requirement text, type, rule_key)
KEYWORD_REQUIREMENTS = [
    (["gst", "gstin"], "Bidder must hold a valid and active GST registration; GSTIN must match government records", "STATUTORY", "gst_active"),
    (["pan", "permanent account number"], "Bidder PAN must be valid and match Income Tax Department records", "STATUTORY", "pan_valid"),
    (["udyam", "msme", "mse"], "MSE bidders claiming Udyam benefits must hold a valid Udyam registration", "ELIGIBILITY", "udyam_valid"),
    (["epf", "provident fund"], "Bidder must have a valid EPFO registration with unexpired coverage", "STATUTORY", "epfo_valid"),
    (["psara", "private security agencies"], "Bidder must hold a valid PSARA licence for providing private security services", "TENDER_SPECIFIC", "psara_license"),
    (["blacklist", "debar"], "Bidder must not be blacklisted or debarred by any government authority", "ELIGIBILITY", "not_blacklisted"),
    (["local content", "make in india"], "Declared local content must meet the minimum threshold (Make in India)", "TENDER_SPECIFIC", "local_content"),
]

PROMPT = """You are analysing an Indian government tender document. Extract the
compliance requirements a bidder must satisfy. Return ONLY a JSON array where each
item is: {{"text": "...", "type": "ELIGIBILITY|STATUTORY|TENDER_SPECIFIC",
"priority": "MANDATORY|OPTIONAL", "rule_key": one of ["gst_active","pan_valid",
"udyam_valid","epfo_valid","psara_license","not_blacklisted","local_content",""]}}.
Use rule_key "" for requirements outside that list. Tender text (truncated):

{tender_text}
"""


def extract_requirements(tender_text: str) -> list[dict]:
    out = llm_json(PROMPT.format(tender_text=tender_text[:14000]), "tender_requirements")
    if isinstance(out, list) and out:
        cleaned = []
        for item in out:
            if isinstance(item, dict) and item.get("text"):
                cleaned.append({
                    "text": str(item["text"])[:500],
                    "type": item.get("type", "STATUTORY"),
                    "priority": item.get("priority", "MANDATORY"),
                    "rule_key": item.get("rule_key", "") or "",
                })
        if cleaned:
            return cleaned

    # Deterministic fallback
    low = tender_text.lower()
    reqs = []
    for keywords, text, rtype, rule_key in KEYWORD_REQUIREMENTS:
        if any(k in low for k in keywords):
            reqs.append({"text": text, "type": rtype, "priority": "MANDATORY", "rule_key": rule_key})
    reqs.extend(extract_custom_clauses(tender_text))
    if not reqs:  # safety net: statutory basics always apply
        for _, text, rtype, rule_key in KEYWORD_REQUIREMENTS[:2]:
            reqs.append({"text": text, "type": rtype, "priority": "MANDATORY", "rule_key": rule_key})
    return reqs


# Custom (tender-specific) clause detectors: requirements with rule_key "" get an
# AI-drafted dynamic rule instead of a built-in one.
import re  # noqa: E402

CUSTOM_CLAUSE_PATTERNS = [
    (r"earnest money|EMD",
     "Earnest Money Deposit (EMD) must be submitted as specified in the tender{detail}"),
    (r"work experience certificate|experience certificate|similar work",
     "Bidder must submit work experience certificates for similar services"),
    (r"\bturnover\b",
     "Bidder must demonstrate the required average annual turnover{detail}"),
    (r"minimum wages?",
     "Quoted rates must not be below the government-notified minimum wages"),
    (r"performance security|performance bank guarant|epbg|security deposit",
     "Successful bidder must furnish performance security as specified{detail}"),
    (r"integrity pact",
     "Bidder must sign and submit the Integrity Pact"),
    (r"land border|rule 144\s*\(xi\)",
     "Bidder from a land-border country must be registered with the competent authority (GFR Rule 144(xi))"),
]


def extract_custom_clauses(tender_text: str) -> list[dict]:
    reqs = []
    for pattern, template in CUSTOM_CLAUSE_PATTERNS:
        m = re.search(pattern, tender_text, re.I)
        if not m:
            continue
        window = tender_text[max(0, m.start() - 80): m.end() + 160]
        amount = re.search(r"(?<![A-Za-z])Rs\.?\s*[\d,]{2,}(?:\.\d+)?\s*(?:lakhs?|crores?)?", window, re.I)
        detail = f" ({amount.group(0).strip()})" if amount and "{detail}" in template else ""
        reqs.append({
            "text": template.replace("{detail}", detail),
            "type": "TENDER_SPECIFIC",
            "priority": "MANDATORY",
            "rule_key": "",  # no built-in rule -> the rule forge drafts one
        })
    return reqs[:6]
