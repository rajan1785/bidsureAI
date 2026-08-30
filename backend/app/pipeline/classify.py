"""Document type classification (FR-D02).

Primary: our trained TF-IDF + LogisticRegression model
(backend/app/ml/doc_classifier.joblib, trained by scripts/train_classifier.py
on a synthetic corpus — metrics in ml/metrics.json). Fallback: keyword rules.
"""
from pathlib import Path

_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is None:
        try:
            import joblib
            _MODEL = joblib.load(Path(__file__).parents[1] / "ml" / "doc_classifier.joblib")
        except Exception:
            _MODEL = False
    return _MODEL


def classify_doc_ml(text: str):
    """Returns (doc_type, confidence) from the trained model, or None."""
    model = _load_model()
    if not model:
        return None
    proba = model.predict_proba([text])[0]
    idx = proba.argmax()
    label, conf = model.classes_[idx], float(proba[idx])
    if conf < 0.45:
        return None  # low confidence -> let the keyword fallback decide
    return label, conf


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
    ml = classify_doc_ml(text)
    if ml:
        return ml[0]
    low = text.lower()
    scores = {}
    for dt in _PRIORITY:
        hits = sum(1 for kw in DOC_TYPES[dt] if kw in low)
        if hits:
            scores[dt] = hits
    if not scores:
        return "OTHER"
    return max(scores, key=lambda k: (scores[k], -_PRIORITY.index(k)))
