"""End-to-end: tender upload -> approval -> bid -> pipeline -> dashboard -> decision.
Runs the govt api replica as a real subprocess so verification goes over HTTP."""
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

os.environ["GOVT_API_URL"] = "http://127.0.0.1:9001"

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import orchestrator

orchestrator.STAGE_DELAY = 0

client = TestClient(app)

REPO = Path(__file__).parents[2]

TENDER_TEXT = """SECURITY SERVICES TENDER - University of Delhi
Eligibility: bidder must possess valid GST registration and PAN.
The agency must hold a licence under the Private Security Agencies (Regulation) Act (PSARA).
EPF registration is mandatory. Bidder must not be blacklisted by any govt department.
MSE bidders may claim Udyam benefits.
"""

DOCS_A = {
    "gst_certificate.txt": "Form GST REG-06 Goods and Services Tax Registration Certificate\nRegistration Number : 07AAECS1234F1Z5\nSHAKTI FACILITY SERVICES PRIVATE LIMITED",
    "pan_card.txt": "INCOME TAX DEPARTMENT Permanent Account Number Card\nAAECS1234F\nSHAKTI FACILITY SERVICES",
    "udyam_cert.txt": "Ministry of Micro, Small and Medium Enterprises UDYAM REGISTRATION CERTIFICATE\nUDYAM-DL-01-0012345",
    "epfo_reg.txt": "Employees' Provident Fund Organisation\nEstablishment Code: DLCPM0012345000\nValid Until: 31/03/2027",
    "psara_licence.txt": "Licence under the Private Security Agencies (Regulation) Act 2005\nLicense No: PSARA/DL/2023/04412\nValid upto: 31/12/2026",
}


@pytest.fixture(scope="module", autouse=True)
def govt_api():
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "9001"],
        cwd=REPO / "govt-api",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(50):
        try:
            httpx.get("http://127.0.0.1:9001/api/v1/debarment/check/AAECS1234F", timeout=1)
            break
        except Exception:
            time.sleep(0.2)
    yield
    proc.terminate()
    proc.wait()


def test_full_flow_bidder_a(tmp_path):
    # 1. tender upload
    tender_file = tmp_path / "tender.txt"
    tender_file.write_text(TENDER_TEXT)
    r = client.post(
        "/api/v1/tenders",
        data={"title": "Security Services Tender", "organization": "University of Delhi"},
        files={"file": ("tender.txt", tender_file.read_bytes(), "text/plain")},
    )
    assert r.status_code == 200, r.text
    tender = r.json()
    assert tender["status"] == "REVIEW"
    keys = {q["rule_key"] for q in tender["requirements"]}
    assert "gst_active" in keys and "psara_license" in keys

    # 2. approve
    r = client.post(f"/api/v1/tenders/{tender['id']}/approve")
    assert r.json()["status"] == "APPROVED"

    # 3. bidder + bid + docs
    r = client.post("/api/v1/bidders", json={
        "legal_name": "Shakti Facility Services Pvt Ltd", "pan": "AAECS1234F",
        "gstin": "07AAECS1234F1Z5", "udyam": "UDYAM-DL-01-0012345",
        "epfo_code": "DLCPM0012345000"})
    bidder_id = r.json()["id"]
    r = client.post("/api/v1/bids", json={"tender_id": tender["id"], "bidder_id": bidder_id})
    bid_id = r.json()["id"]
    for name, content in DOCS_A.items():
        r = client.post(f"/api/v1/bids/{bid_id}/documents",
                        files={"file": (name, content.encode(), "text/plain")})
        assert r.status_code == 200

    # 4. submit -> pipeline runs (TestClient executes background task synchronously)
    r = client.post(f"/api/v1/bids/{bid_id}/submit")
    assert r.status_code == 200
    assert client.get(f"/api/v1/bids/{bid_id}/status").json()["pipeline_status"] == "DONE"

    # 5. drill-down
    detail = client.get(f"/api/v1/bids/{bid_id}").json()
    statuses = {x["requirement_key"]: x["status"] for x in detail["results"]}
    assert statuses["gst_active"] == "Compliant"
    assert statuses["psara_license"] == "Compliant"
    assert statuses["not_blacklisted"] == "Compliant"
    assert detail["risk"]["risk"] == "Low"
    assert detail["risk"]["score"] >= 90
    assert detail["recommendation"]["text"]
    assert any(g["source"] == "GST" and g["mock"] for g in detail["govt_records"])

    # 6. comparison + decision + audit
    comp = client.get(f"/api/v1/tenders/{tender['id']}/comparison").json()
    assert comp[0]["bidder"].startswith("Shakti")
    r = client.post(f"/api/v1/bids/{bid_id}/decision",
                    json={"decision": "Qualified", "remarks": "All checks passed"})
    assert r.json()["ok"]
    audit = client.get("/api/v1/audit").json()
    actions = {e["action"] for e in audit}
    assert {"TENDER_CREATED", "BID_SUBMITTED", "PIPELINE_DONE", "DECISION_RECORDED"} <= actions


def test_delete_tender_cascades(tmp_path):
    # create a throwaway tender + bid + doc, then delete everything
    tf = tmp_path / "t.txt"
    tf.write_text("Bidder must possess GST registration and PAN.")
    t = client.post("/api/v1/tenders", data={"title": "Delete Me"},
                    files={"file": ("t.txt", tf.read_bytes(), "text/plain")}).json()
    b = client.post("/api/v1/bidders", json={"legal_name": "Del Co", "pan": "AAECS1234F"}).json()
    bid = client.post("/api/v1/bids", json={"tender_id": t["id"], "bidder_id": b["id"]}).json()
    client.post(f"/api/v1/bids/{bid['id']}/documents",
                files={"file": ("d.txt", b"PAN AAECS1234F", "text/plain")})

    r = client.delete(f"/api/v1/tenders/{t['id']}")
    assert r.status_code == 200
    assert r.json()["deleted_bids"] == 1
    assert client.get(f"/api/v1/tenders/{t['id']}").status_code == 404
    assert client.get(f"/api/v1/bids/{bid['id']}").status_code == 404
