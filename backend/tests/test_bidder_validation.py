# Regression: ISSUE-004 — garbage PAN/GSTIN were accepted at registration
# Found by /qa on 2026-08-30
# Report: .gstack/qa-reports/qa-report-bidsure-2026-08-30.md
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_valid_bidder_accepted():
    r = client.post("/bidders", json={
        "legal_name": "Valid Co", "pan": "AAECS1234F", "gstin": "07AAECS1234F1Z5",
        "udyam": "UDYAM-DL-01-0012345", "epfo_code": "DLCPM0012345000"})
    assert r.status_code == 200
    assert r.json()["pan"] == "AAECS1234F"


def test_garbage_pan_rejected():
    r = client.post("/bidders", json={"legal_name": "Typo Co", "pan": "WRONGPAN"})
    assert r.status_code == 422
    assert "AAAAA9999A" in r.text


def test_garbage_gstin_rejected():
    r = client.post("/bidders", json={"legal_name": "Typo Co", "pan": "AAECS1234F",
                                      "gstin": "NOT-A-GSTIN"})
    assert r.status_code == 422


def test_blank_optional_identifiers_allowed():
    r = client.post("/bidders", json={"legal_name": "Minimal Co", "pan": "AAECS1234F"})
    assert r.status_code == 200


def test_lowercase_normalized():
    r = client.post("/bidders", json={"legal_name": "Lower Co", "pan": "aaecs1234f"})
    assert r.status_code == 200
    assert r.json()["pan"] == "AAECS1234F"
