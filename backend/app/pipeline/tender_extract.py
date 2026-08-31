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


def _clean(text: str) -> str:
    """Strip pdf cid artifacts and non-ascii (bilingual GeM bids) so keyword
    and semantic detection see plain English."""
    text = re.sub(r"\(cid:\d+\)", "", text)
    return re.sub(r"[^\x00-\x7F]+", " ", text)


def extract_requirements(tender_text: str) -> list[dict]:
    tender_text = _clean(tender_text)
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
    reqs.extend(mine_requirements(tender_text, [r["text"] for r in reqs]))
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
    (r"work experience certificate|experience certificate|similar work|experience criteria|years of past experience",
     "Bidder must meet the experience criteria and submit supporting experience documents"),
    (r"OEM authori[sz]ation",
     "Bidder must submit a valid OEM Authorization Certificate"),
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


OBLIGATION = re.compile(
    r"\b(bidder|seller|tenderer|agency|OEM)s?\b.{0,60}\b(must|shall|should|required to|has to)\b",
    re.I,
)

_PROTOTYPE = ("the bidder must submit a document, certificate or declaration "
              "to prove eligibility for the tender")


def mine_requirements(tender_text: str, existing_texts: list[str], limit: int = 4) -> list[dict]:
    """Semantic requirement mining: rank obligation sentences with the local
    embedding model so clauses outside the known patterns still surface."""
    lines, seen = [], set()
    for l in tender_text.splitlines():
        l = " ".join(l.split())
        if 50 < len(l) < 220 and OBLIGATION.search(l):
            k = l[:60].lower()
            if k not in seen:
                seen.add(k)
                lines.append(l)
    if not lines:
        return []
    try:
        from app.ml.embedder import top_k
    except Exception:
        return []
    picked = []
    corpus = lines[:60]
    ranked = top_k(_PROTOTYPE, corpus, k=min(len(corpus), limit * 3))
    exist = [e.lower() for e in existing_texts]
    for i, score in ranked:
        if score < 0.35 or len(picked) >= limit:
            break
        line = corpus[i]
        # skip clauses we already captured via patterns
        if any(w in line.lower() for e in exist for w in [e[:40]] if w in line.lower()):
            continue
        dup = top_k(line, existing_texts + [p["text"] for p in picked], k=1) if (existing_texts or picked) else []
        if dup and dup[0][1] > 0.8:
            continue
        picked.append({"text": line[:300], "type": "TENDER_SPECIFIC",
                       "priority": "MANDATORY", "rule_key": ""})
    return picked


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
    return reqs[:8]


# --- tender metadata auto-extraction (title / organization / reference no.) ---

_REF_PAT = re.compile(
    r"(?:Bid Number|Tender Ref\.?\s*No\.?|Reference No\.?|Tender No\.?|NIT No\.?)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-\.]{5,40})",
    re.I,
)
_ORG_LABEL = re.compile(r"(?:Organisation Name|Organization Name|Department Name|Ministry/State Name)\s*[:\-]?\s*(.{4,80})", re.I)
_ORG_LINE = re.compile(r"^(?:THE\s+)?(UNIVERSITY|MINISTRY|DEPARTMENT|GOVERNMENT|MUNICIPAL|CORPORATION|INSTITUTE|COUNCIL|AUTHORITY|BOARD|OFFICE)\b", re.I)
_TITLE_LINE = re.compile(r"^[A-Z0-9 ,&/\-\(\)\.]{8,80}(?:TENDER|BID|SERVICES|SUPPLY|WORKS)[A-Z0-9 ,&/\-\(\)\.]{0,40}$")


def extract_tender_meta(tender_text: str) -> dict:
    """Best-effort title / organization / reference number from the document."""
    text = _clean(tender_text)
    head = [" ".join(l.split()) for l in text.splitlines()[:80] if l.strip()]

    ref = ""
    m = _REF_PAT.search(text[:4000])
    if m:
        ref = m.group(1).strip().rstrip(".")

    org = ""
    m = _ORG_LABEL.search(text[:6000])
    if m:
        org = " ".join(m.group(1).split())[:80].strip(" .,")
    if not org:
        for l in head:
            if _ORG_LINE.match(l) and len(l) < 80:
                org = l.title().strip(" .,")
                break

    title = ""
    for l in head:
        if _TITLE_LINE.match(l) and "PAGE" not in l.upper():
            title = l.title()
            break
    if not title:
        # GeM bids: use the item category if present
        m = re.search(r"Item Category[/\w\s]*?[:\-]\s*(.{5,80})", text[:6000], re.I)
        if m:
            title = "GeM Bid — " + " ".join(m.group(1).split())[:60].strip(" .,")
    if not title:
        title = f"Tender {ref}" if ref else "Untitled Tender"

    return {"title": title[:120], "organization": org, "ref_no": ref}
