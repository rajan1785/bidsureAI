"""Deterministic field extraction with regexes for Indian identifiers (FR-D03).

Every extracted field carries a confidence and the character span it was
found at, which becomes the evidence reference (FR-C04).
"""
import re

PATTERNS = {
    "gstin": re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]\b"),
    "pan": re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"),
    "udyam": re.compile(r"\bUDYAM-[A-Z]{2}-\d{2}-\d{7}\b"),
    "epfo_code": re.compile(r"\b[A-Z]{5}\d{7}\d{3}\b"),
    "cin": re.compile(r"\b[UL]\d{5}[A-Z]{2}\d{4}[A-Z]{3}\d{6}\b"),
    "date": re.compile(
        r"\b(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2}|\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
        re.IGNORECASE,
    ),
    "local_content_pct": re.compile(r"local\s+content[^%\n]{0,60}?(\d{1,3})\s*%", re.IGNORECASE),
    "valid_until": re.compile(r"valid\s+(?:up\s?to|until|till)\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}-\d{2}-\d{2})", re.IGNORECASE),
    "license_no": re.compile(r"licen[cs]e\s*(?:no\.?|number)\s*[:\-]?\s*([A-Z0-9/\-]{4,})", re.IGNORECASE),
}

# Which fields matter for which document type; a GSTIN embeds a PAN, so a
# PAN match inside a GST cert is expected and kept (used for cross-checks).
RELEVANT = {
    "GST_CERT": ["gstin", "pan", "date"],
    "PAN_CARD": ["pan"],
    "UDYAM_CERT": ["udyam", "pan", "date"],
    "EPFO_REG": ["epfo_code", "valid_until", "date"],
    "PSARA_LICENSE": ["license_no", "valid_until", "date"],
    "OEM_AUTH": ["date"],
    "LOCAL_CONTENT_DECL": ["local_content_pct", "pan", "date"],
    "COMPANY_PROFILE": ["local_content_pct", "pan", "date"],
    "ITR_ACK": ["pan", "date"],
    "OTHER": ["gstin", "pan", "udyam", "date"],
}


def extract_fields(text: str, doc_type: str) -> list[dict]:
    fields = []
    for name in RELEVANT.get(doc_type, RELEVANT["OTHER"]):
        pat = PATTERNS[name]
        for m in pat.finditer(text):
            value = m.group(1) if m.groups() else m.group(0)
            # A GSTIN contains a PAN substring; skip PAN hits inside a GSTIN.
            if name == "pan":
                window = text[max(0, m.start() - 2) : m.end() + 4]
                if PATTERNS["gstin"].search(window):
                    continue
            fields.append(
                {
                    "field": name,
                    "value": value,
                    "confidence": 0.95,
                    "evidence_location": f"chars {m.start()}-{m.end()}",
                }
            )
            if name != "date":
                break  # first hit wins for identifier fields
    return fields
