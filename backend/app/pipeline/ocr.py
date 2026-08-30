"""Text extraction: pdfplumber for digital PDFs, enhanced OCR for scans
(FR-D01, FR-D04).

Digital documents use their embedded text layer (fast, ~0.98 confidence).
Scanned pages and images go through the stamp-aware OCR pipeline in
ocr_enhance (ink suppression + binarization + best-of-N Tesseract passes,
confidence straight from the engine). Scanned PDFs are rasterized first —
Tesseract cannot read PDF files directly.
"""
import shutil
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
        # No text layer -> scanned PDF: rasterize pages, then OCR each
        if _tesseract_available():
            return _ocr_scanned_pdf(p)
        return {"text": "", "method": "none", "confidence": 0.0}

    if suffix in (".png", ".jpg", ".jpeg", ".tiff"):
        if _tesseract_available():
            from app.pipeline.ocr_enhance import ocr_image_best

            return ocr_image_best(str(p))
        return {"text": "", "method": "none", "confidence": 0.0}

    if suffix in (".txt", ".md"):
        return {"text": p.read_text(errors="ignore"), "method": "plain", "confidence": 1.0}

    if suffix == ".docx":
        return _docx(p)

    return {"text": "", "method": "unsupported", "confidence": 0.0}


def _ocr_scanned_pdf(p: Path) -> dict:
    from app.pipeline.ocr_enhance import ocr_image_best, rasterize_pdf

    try:
        pages = rasterize_pdf(str(p))
    except Exception:
        return {"text": "", "method": "rasterize_failed", "confidence": 0.0}
    texts, confs = [], []
    for page_png in pages:
        res = ocr_image_best(page_png)
        if res["text"]:
            texts.append(res["text"])
            confs.append(res["confidence"])
    if not texts:
        return {"text": "", "method": "tesseract-scanned-pdf", "confidence": 0.0}
    return {"text": "\n".join(texts), "method": "tesseract-scanned-pdf",
            "confidence": round(sum(confs) / len(confs), 3)}


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
