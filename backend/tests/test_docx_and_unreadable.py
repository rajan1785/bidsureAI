# Regression: ISSUE-002 — .docx tenders were unreadable and produced fabricated requirements
# Found by /qa on 2026-08-30
# Report: .gstack/qa-reports/qa-report-bidsure-2026-08-30.md
import zipfile

from app.pipeline.ocr import extract_text

DOCX_XML = """<?xml version="1.0"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body><w:p><w:r><w:t>Bidder must have GST registration and PAN.</w:t></w:r></w:p>
<w:p><w:r><w:t>PSARA licence is mandatory.</w:t></w:r></w:p></w:body></w:document>"""


def _make_docx(path):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("word/document.xml", DOCX_XML)


def test_docx_text_extraction(tmp_path):
    p = tmp_path / "tender.docx"
    _make_docx(p)
    res = extract_text(str(p))
    assert res["method"] == "docx"
    assert "GST registration" in res["text"]
    assert "PSARA licence" in res["text"]
    assert res["confidence"] > 0.9


def test_corrupt_docx_returns_empty_not_crash(tmp_path):
    p = tmp_path / "broken.docx"
    p.write_bytes(b"this is not a zip file")
    res = extract_text(str(p))
    assert res["text"] == ""
    assert res["confidence"] == 0.0


def test_unsupported_extension_returns_empty(tmp_path):
    p = tmp_path / "tender.doc"
    p.write_bytes(b"\xd0\xcf\x11\xe0 legacy binary")
    res = extract_text(str(p))
    assert res["text"] == ""
