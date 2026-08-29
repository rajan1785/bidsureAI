"""Keyword-based document type classification (FR-D02)."""

DOC_TYPES = {
    "GST_CERT": ["goods and services tax", "gst registration", "gstin", "form gst reg"],
    "PAN_CARD": ["permanent account number", "income tax department", "pan services"],
    "UDYAM_CERT": ["udyam registration", "ministry of micro", "msme"],
    "EPFO_REG": ["employees' provident fund", "employees provident fund", "epfo", "provident fund organisation"],
    "PSARA_LICENSE": ["private security agencies", "psara", "security agency licence", "security agency license"],
    "OEM_AUTH": ["oem authorization", "oem authorisation", "manufacturer authorization"],
    "LOCAL_CONTENT_DECL": ["local content", "make in india", "class-i local supplier"],
    "ITR_ACK": ["income tax return", "itr-v", "acknowledgement number"],
}

# Order matters: more specific first.
_PRIORITY = [
    "UDYAM_CERT",
    "PSARA_LICENSE",
    "OEM_AUTH",
    "EPFO_REG",
    "LOCAL_CONTENT_DECL",
    "ITR_ACK",
    "GST_CERT",
    "PAN_CARD",
]


def classify_doc(text: str) -> str:
    low = text.lower()
    scores = {}
    for dt in _PRIORITY:
        hits = sum(1 for kw in DOC_TYPES[dt] if kw in low)
        if hits:
            scores[dt] = hits
    if not scores:
        return "OTHER"
    return max(scores, key=lambda k: (scores[k], -_PRIORITY.index(k)))
