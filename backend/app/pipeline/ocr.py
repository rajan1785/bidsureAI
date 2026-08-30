"""Text extraction: pdfplumber for digital PDFs, Tesseract (if installed)
for scanned pages, explicit low-confidence flag otherwise (FR-D01, FR-D04)."""
import shutil
import subprocess
from pathlib import Path


def _tesseract_available() -> bool:
    return shutil.which("tesseract") is not None


def extract_text(path: str) -> dict:
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".pdf":
        import pdfplumber

        texts = []
        with pdfplumber.open(p) as pdf:
            for page in pdf.pages:
                texts.append(page.extract_text() or "")
        text = "\n".join(texts).strip()
        if text:
            return {"text": text, "method": "pdfplumber", "confidence": 0.98}
        # Scanned PDF with no text layer
        if _tesseract_available():
            return _tesseract(p)
        return {"text": "", "method": "none", "confidence": 0.0}

    if suffix in (".png", ".jpg", ".jpeg", ".tiff"):
        if _tesseract_available():
            return _tesseract(p)
        return {"text": "", "method": "none", "confidence": 0.0}

    if suffix in (".txt", ".md"):
        return {"text": p.read_text(errors="ignore"), "method": "plain", "confidence": 1.0}

    if suffix == ".docx":
        return _docx(p)

    return {"text": "", "method": "unsupported", "confidence": 0.0}


def _docx(p: Path) -> dict:
    # .docx is a zip; pull paragraph text out of word/document.xml with stdlib only
    import re
    import zipfile
    from html import unescape

    try:
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="ignore")
        xml = re.sub(r"</w:p>", "\n", xml)
        text = unescape(re.sub(r"<[^>]+>", "", xml)).strip()
        return {"text": text, "method": "docx", "confidence": 0.95 if text else 0.0}
    except Exception:
        return {"text": "", "method": "docx_failed", "confidence": 0.0}


def _tesseract(p: Path) -> dict:
    try:
        out = subprocess.run(
            ["tesseract", str(p), "stdout"], capture_output=True, text=True, timeout=120
        )
        text = out.stdout.strip()
        return {"text": text, "method": "tesseract", "confidence": 0.85 if text else 0.0}
    except Exception:
        return {"text": "", "method": "tesseract_failed", "confidence": 0.0}
