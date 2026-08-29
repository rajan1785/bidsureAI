import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_gst_known_gstin_active():
    r = client.get("/gst/07AAECS1234F1Z5")
    assert r.status_code == 200
    body = r.json()
    assert body["mock"] is True
    assert body["data"]["status"] == "Active"
    assert body["data"]["legal_name"].startswith("SHAKTI")


def test_gst_unknown_gstin_404():
    r = client.get("/gst/29ZZZZZ9999Z1Z9")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "RECORD_NOT_FOUND"


def test_pan_valid():
    r = client.get("/pan/AAFCN5678K")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "Valid"


def test_blacklist_hit_for_bidder_c():
    r = client.get("/blacklist/AAKCA9012M")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["clean"] is False
    assert data["records"][0]["status"] == "Active"


def test_blacklist_clean_for_bidder_a():
    r = client.get("/blacklist/AAECS1234F")
    assert r.status_code == 200
    assert r.json()["data"]["clean"] is True


def test_epfo_bidder_b_expired_validity():
    r = client.get("/epfo/DLCPM0023456000")
    assert r.status_code == 200
    assert r.json()["data"]["valid_until"] == "2026-03-31"
