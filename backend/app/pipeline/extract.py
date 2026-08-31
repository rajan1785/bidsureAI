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


# OCR confusion pairs; PAN/GSTIN have fixed letter/digit positions, so we can
# repair misreads positionally (e.g. "AAECSI234F" -> "AAECS1234F").
_TO_DIGIT = {"O": "0", "I": "1", "L": "1", "S": "5", "B": "8", "Z": "2", "G": "6", "Q": "0", "D": "0", "/": "1", "\\": "1", "|": "1"}
_TO_LETTER = {v: k for k, v in {"O": "0", "I": "1", "S": "5", "B": "8", "Z": "2", "G": "6"}.items()}


def _fix_positions(token: str, spec: str) -> str | None:
    """spec: 'L'=letter, 'D'=digit, '*'=either, literal char = itself."""
    if len(token) != len(spec):
        return None
    out = []
    for ch, want in zip(token.upper(), spec):
        if want == "L":
            if ch.isalpha():
                out.append(ch)
            elif ch in _TO_LETTER:
                out.append(_TO_LETTER[ch])
            else:
                return None
        elif want == "D":
            if ch.isdigit():
                out.append(ch)
            elif ch in _TO_DIGIT:
                out.append(_TO_DIGIT[ch])
            else:
                return None
        elif want == "*":
            out.append("1" if ch in ("/", "\\", "|") else ch)
        else:  # literal
            if ch == want:
                out.append(ch)
            elif want == "Z" and ch in ("2", "7"):
                out.append("Z")
            else:
                return None
    return "".join(out)


_PAN_SPEC = "LLLLLDDDDL"
_GSTIN_SPEC = "DDLLLLLDDDDL*Z*"
_UDYAM_SPEC = "LLDDDDDDDDD"


_LABELS = [
    ("gstin", r"(?:GSTIN|Registration\s+Number)[^A-Z0-9]{0,8}", 15, "_GSTIN_SPEC"),
    ("pan", r"(?:PAN|Permanent\s+Account\s+Number)[^A-Z0-9]{0,10}", 10, "_PAN_SPEC"),
    ("udyam", r"UDYAM(?:\s+Registration)?(?:\s+(?:Number|No\.?))?[^A-Z0-9]{0,8}", 11, "_UDYAM_SPEC"),
]


def _label_anchored(text: str) -> list[dict]:
    """Reassemble identifiers that OCR split into fragments after their label
    (e.g. 'GSTIN): O7AAECS 1234F 1Z5' -> strip separators, repair positionally)."""
    out = []
    specs = {"_PAN_SPEC": _PAN_SPEC, "_GSTIN_SPEC": _GSTIN_SPEC, "_UDYAM_SPEC": _UDYAM_SPEC}
    for field, label_pat, length, spec_name in _LABELS:
        for m in re.finditer(label_pat, text, re.IGNORECASE):
            window = text[m.end(): m.end() + length * 2 + 10]
            # translate slash/pipe misreads to '1' BEFORE stripping separators,
            # or the character (and the position alignment) is lost entirely
            cleaned = re.sub(r"[/|\\]", "1", window.upper())
            compact = re.sub(r"[^A-Z0-9]", "", cleaned)[:length]
            if len(compact) < length:
                continue
            if field == "udyam" and compact.startswith("UDYAM"):
                compact = re.sub(r"[^A-Z0-9]", "", cleaned.replace("UDYAM", "", 1))[:length]
            repaired = _fix_positions(compact, specs[spec_name])
            if field == "udyam" and repaired:
                repaired = f"UDYAM-{repaired[:2]}-{repaired[2:4]}-{repaired[4:]}"
            if repaired and PATTERNS[field].fullmatch(repaired):
                out.append({"field": field, "value": repaired, "confidence": 0.75,
                            "evidence_location": f"chars {m.start()}-{m.end()+length} (OCR-reassembled near '{field.upper()}' label)"})
                break
    return out


def ocr_correct_identifiers(text: str) -> list[dict]:
    """Find OCR-mangled PAN/GSTIN candidates and repair them positionally."""
    fixed = []
    for m in re.finditer(r"\b[A-Z0-9]{10}\b", text):
        if PATTERNS["pan"].fullmatch(m.group(0)):
            continue  # already valid — normal extraction handles it
        repaired = _fix_positions(m.group(0), _PAN_SPEC)
        if repaired and PATTERNS["pan"].fullmatch(repaired):
            fixed.append({"field": "pan", "value": repaired, "confidence": 0.8,
                          "evidence_location": f"chars {m.start()}-{m.end()} (OCR-corrected from {m.group(0)})"})
    for m in re.finditer(r"\b[A-Z0-9]{15}\b", text):
        if PATTERNS["gstin"].fullmatch(m.group(0)):
            continue
        repaired = _fix_positions(m.group(0), _GSTIN_SPEC)
        if repaired and PATTERNS["gstin"].fullmatch(repaired):
            fixed.append({"field": "gstin", "value": repaired, "confidence": 0.8,
                          "evidence_location": f"chars {m.start()}-{m.end()} (OCR-corrected from {m.group(0)})"})
    have = {f["field"] for f in fixed}
    fixed.extend(f for f in _label_anchored(text) if f["field"] not in have)
    return fixed


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

    # OCR repair: if pan/gstin were expected for this doc type but not found,
    # try positional correction of near-miss tokens (stamped/scanned docs).
    have = {f["field"] for f in fields}
    wanted = set(RELEVANT.get(doc_type, RELEVANT["OTHER"]))
    if ("pan" in wanted and "pan" not in have) or ("gstin" in wanted and "gstin" not in have):
        for fix in ocr_correct_identifiers(text):
            if fix["field"] in wanted and fix["field"] not in have:
                fields.append(fix)
                have.add(fix["field"])
    return fields
