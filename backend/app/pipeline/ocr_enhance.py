"""Scanned-document reader: preprocessing + best-of-N OCR.

Government documents carry stamps, seals and signatures in red/blue ink that
overlap the printed text and wreck naive OCR. This module:

1. suppresses colored stamp ink (red/blue channels) while keeping black text,
2. binarizes (Otsu), boosts contrast and upscales,
3. runs Tesseract on BOTH the original and the enhanced image,
4. keeps whichever pass has the higher mean word confidence.

Confidence comes from Tesseract's TSV output, so the number shown to the
officer is the OCR engine's own estimate — not a made-up constant.
"""
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps


def suppress_stamp_ink(img: Image.Image) -> Image.Image:
    """Replace saturated red/blue ink (stamps, seals) with white; keep dark text."""
    rgb = np.asarray(img.convert("RGB")).astype(int)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # Only remove BRIGHT colored ink (stamp on paper). A dark pixel that is
    # reddish is printed text UNDER translucent stamp ink — keep it, or the
    # stamp punches holes through the very characters we need to read.
    bright = rgb.mean(axis=-1) > 75
    red_ink = (r > 110) & (r > g + 35) & (r > b + 35) & bright
    blue_ink = (b > 110) & (b > r + 35) & (b > g + 35) & bright
    out = rgb.copy()
    out[red_ink | blue_ink] = [255, 255, 255]
    return Image.fromarray(out.astype(np.uint8))


def binarize(img: Image.Image, upscale: int = 2) -> Image.Image:
    """Grayscale -> autocontrast -> Otsu threshold -> upscale for OCR."""
    g = ImageOps.autocontrast(img.convert("L"))
    a = np.asarray(g)
    # Otsu's threshold
    hist, _ = np.histogram(a, bins=256, range=(0, 256))
    total = a.size
    sum_all = np.dot(np.arange(256), hist)
    sum_b = 0.0
    w_b = 0.0
    best_t, best_var = 128, 0.0
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        var = w_b * w_f * (m_b - m_f) ** 2
        if var > best_var:
            best_var, best_t = var, t
    binary = Image.fromarray(((a > best_t) * 255).astype(np.uint8))
    if upscale > 1:
        binary = binary.resize((binary.width * upscale, binary.height * upscale),
                               Image.LANCZOS)
    return binary


def _tesseract_tsv(path: str) -> tuple[str, float]:
    """Run tesseract, return (text, mean word confidence 0..1)."""
    out = subprocess.run(
        ["tesseract", path, "stdout", "--oem", "1", "--psm", "6", "tsv"],
        capture_output=True, text=True, timeout=120,
    )
    words, confs = [], []
    for line in out.stdout.splitlines()[1:]:
        parts = line.split("\t")
        if len(parts) >= 12 and parts[11].strip():
            try:
                conf = float(parts[10])
            except ValueError:
                continue
            if conf >= 0:
                words.append(parts[11])
                confs.append(conf)
        elif len(parts) >= 12 and parts[6] == "1" and words and words[-1] != "\n":
            words.append("\n")  # new line marker on line-level rows
    text = " ".join(words).replace(" \n ", "\n")
    mean_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
    return text, mean_conf


def ocr_image_best(path: str) -> dict:
    """Best-of-N OCR: raw pass vs stamp-suppressed + binarized pass."""
    img = Image.open(path)
    passes = [("tesseract-raw", path)]
    try:
        enhanced = binarize(suppress_stamp_ink(img))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        enhanced.save(tmp.name)
        passes.append(("tesseract-enhanced", tmp.name))
    except Exception:
        pass

    best = {"text": "", "method": "tesseract-failed", "confidence": 0.0}
    for name, p in passes:
        try:
            text, conf = _tesseract_tsv(p)
        except Exception:
            continue
        if conf > best["confidence"]:
            best = {"text": text, "method": name, "confidence": round(conf, 3)}
    return best


def rasterize_pdf(path: str, dpi: int = 200) -> list[str]:
    """Scanned PDF -> per-page PNGs (Tesseract can't read PDFs directly)."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(path)
    out = []
    for i, page in enumerate(pdf):
        bitmap = page.render(scale=dpi / 72)
        img = bitmap.to_pil()
        tmp = tempfile.NamedTemporaryFile(suffix=f"_p{i}.png", delete=False)
        img.save(tmp.name)
        out.append(tmp.name)
        if i >= 19:  # safety cap for the prototype
            break
    return out
