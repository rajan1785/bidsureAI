"""Stamp-aware OCR: ink suppression, positional/label-anchored identifier
repair, and the scanned-PDF rasterization path."""
import shutil

import numpy as np
import pytest
from PIL import Image, ImageDraw

from app.pipeline.extract import _fix_positions, extract_fields, ocr_correct_identifiers
from app.pipeline.ocr_enhance import suppress_stamp_ink

HAS_TESSERACT = shutil.which("tesseract") is not None


def test_ink_suppression_removes_stamp_keeps_text():
    img = Image.new("RGB", (100, 40), "white")
    d = ImageDraw.Draw(img)
    d.rectangle([5, 5, 40, 35], fill=(210, 60, 60))     # bright red stamp ink
    d.rectangle([50, 5, 70, 35], fill=(15, 15, 15))     # black text
    d.rectangle([75, 5, 95, 35], fill=(127, 27, 27))    # dark = text UNDER ink
    out = np.asarray(suppress_stamp_ink(img))
    assert (out[20, 20] == [255, 255, 255]).all()   # stamp ink gone
    assert (out[20, 60] < 60).all()                 # black text kept
    assert (out[20, 85] < 140).all()                # under-ink text kept dark


def test_positional_repair():
    assert _fix_positions("AAECSI234F", "LLLLLDDDDL") == "AAECS1234F"
    assert _fix_positions("O7AAECS1234F1Z5", "DDLLLLLDDDDL*Z*") == "07AAECS1234F1Z5"
    assert _fix_positions("AAECS1234F", "LLLLLDDDDL") == "AAECS1234F"  # already fine
    assert _fix_positions("!!badtoken", "LLLLLDDDDL") is None


def test_ocr_corrected_pan_used_when_regex_misses():
    fields = extract_fields(
        "INCOME TAX DEPARTMENT Permanent Account Number\nAAEC5I234F", "PAN_CARD")
    pans = [f for f in fields if f["field"] == "pan"]
    assert pans and pans[0]["value"] == "AAECS1234F"
    assert "OCR-corrected" in pans[0]["evidence_location"]


def test_label_anchored_reassembly_of_fragmented_gstin():
    text = "Registration Number (GSTIN): O7AAECS 1234F 1Z5\nLegal Name: X"
    fixes = {f["field"]: f["value"] for f in ocr_correct_identifiers(text)}
    assert fixes.get("gstin") == "07AAECS1234F1Z5"


@pytest.mark.skipif(not HAS_TESSERACT, reason="tesseract not installed")
def test_stamped_scan_end_to_end(tmp_path):
    # Regression: stamped govt documents must still yield the exact GSTIN
    import math

    from app.pipeline.classify import classify_doc
    from app.pipeline.ocr import extract_text

    img = Image.new("RGB", (1400, 500), (252, 250, 246))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((90, 70), "Goods and Services Tax Registration Certificate",
           fill=(15, 15, 15), font_size=42)
    d.text((90, 150), "Registration Number (GSTIN): 07AAECS1234F1Z5",
           fill=(15, 15, 15), font_size=42)
    cx, cy, r = 1000, 280, 160
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(205, 35, 35, 150), width=7)
    d.text((cx-110, cy-30), "VERIFIED", fill=(205, 35, 35, 160), font_size=44)
    pts = [(cx-260+i*8, cy+140+int(20*math.sin(i/2))) for i in range(40)]
    d.line(pts, fill=(40, 60, 190, 200), width=5)
    p = tmp_path / "stamped.png"
    img.save(p)

    res = extract_text(str(p))
    assert res["confidence"] > 0.6
    dt = classify_doc(res["text"])
    fields = {f["field"]: f["value"] for f in extract_fields(res["text"], dt)}
    assert fields.get("gstin") == "07AAECS1234F1Z5"


@pytest.mark.skipif(not HAS_TESSERACT, reason="tesseract not installed")
def test_scanned_pdf_rasterize_path():
    from pathlib import Path

    from app.pipeline.ocr_enhance import rasterize_pdf

    pdf = Path(__file__).parents[2] / "demo-assets" / "bidders" / "A" / "gst_registration_certificate.pdf"
    pages = rasterize_pdf(str(pdf))
    assert pages and pages[0].endswith(".png")
