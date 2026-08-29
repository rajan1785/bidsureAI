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
    if not reqs:  # safety net: statutory basics always apply
        for _, text, rtype, rule_key in KEYWORD_REQUIREMENTS[:2]:
            reqs.append({"text": text, "type": rtype, "priority": "MANDATORY", "rule_key": rule_key})
    return reqs
