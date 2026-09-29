"""End-to-end: tender upload -> approval -> bid -> pipeline -> dashboard -> decision.
Runs the govt api replica as a real subprocess so verification goes over HTTP."""
import os
import subprocess
import sys
import time
from pathlib import Path

import httpx
from datetime import datetime, timedelta, timezone

import pytest

os.environ["GOVT_API_URL"] = "http://127.0.0.1:9001"

from fastapi.testclient import TestClient

from app.main import app
from app.pipeline import orchestrator
from app.db import SessionLocal
from app.models import User, Organization
from app.auth.security import get_password_hash, create_access_token

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


def _future_deadline(days: int = 30) -> str:
    """Tender creation rejects a deadline in the past."""
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


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


@pytest.fixture(scope="module")
def test_users():
    """Create test users and return their tokens."""
    db = SessionLocal()
    try:
        # Create organization
        org = db.query(Organization).filter_by(name="Test Org").first()
        if not org:
            org = Organization(name="Test Org")
            db.add(org)
            db.flush()

        # Create officer user
        officer = db.query(User).filter_by(email="officer@test.com").first()
        if not officer:
            officer = User(
                email="officer@test.com",
                hashed_password=get_password_hash("testpass"),
                full_name="Test Officer",
                role="officer",
                organization_id=org.id,
                is_active=1,
            )
            db.add(officer)
            db.flush()

        # Create bidder user
        bidder = db.query(User).filter_by(email="bidder@test.com").first()
        if not bidder:
            bidder = User(
                email="bidder@test.com",
                hashed_password=get_password_hash("testpass"),
                full_name="Test Bidder",
                role="bidder",
                organization_id=org.id,
                is_active=1,
            )
            db.add(bidder)
            db.flush()

        # Create bidder profile for bidder user
        from app.models import Bidder
        bidder_profile = db.query(Bidder).filter_by(user_id=bidder.id).first()
        if not bidder_profile:
            bidder_profile = Bidder(
                legal_name="Test Bidder Pvt Ltd",
                pan="AAECS1234F",
                gstin="07AAECS1234F1Z5",
                udyam="UDYAM-DL-01-0012345",
                epfo_code="DLCPM0012345000",
                organization_id=org.id,
                user_id=bidder.id,
            )
            db.add(bidder_profile)
            db.flush()
            bidder.bidder_id = bidder_profile.id

        db.commit()

        officer_token = create_access_token(data={"sub": officer.id, "role": officer.role, "org_id": officer.organization_id})
        bidder_token = create_access_token(data={"sub": bidder.id, "role": bidder.role, "org_id": bidder.organization_id})

        return {
            "officer_token": officer_token,
            "bidder_token": bidder_token,
            "officer_id": officer.id,
            "bidder_id": bidder.id,
            "bidder_profile_id": bidder_profile.id,
            "org_id": org.id,
        }
    finally:
        db.close()


def test_full_flow_bidder_a(tmp_path, test_users):
    # 1. tender upload (as officer)
    tender_file = tmp_path / "tender.txt"
    tender_file.write_text(TENDER_TEXT)
    r = client.post(
        "/api/v1/tenders",
        data={
            "title": "Security Services Tender",
            "organization": "University of Delhi",
            "deadline": _future_deadline(),
        },
        files={"file": ("tender.txt", tender_file.read_bytes(), "text/plain")},
        headers=_auth_headers(test_users["officer_token"]),
    )
    assert r.status_code == 200, r.text
    tender = r.json()
    assert tender["status"] == "REVIEW"
    keys = {q["rule_key"] for q in tender["requirements"]}
    assert "gst_active" in keys and "psara_license" in keys

    # 2. approve (as officer)
    r = client.post(f"/api/v1/tenders/{tender['id']}/approve",
                    headers=_auth_headers(test_users["officer_token"]))
    assert r.json()["status"] == "APPROVED"

    # 3. bidder + bid + docs (as bidder)
    # Use the pre-created bidder profile
    bidder_id = test_users["bidder_profile_id"]
    r = client.post("/api/v1/bids", json={"tender_id": tender["id"], "bidder_id": bidder_id},
                    headers=_auth_headers(test_users["bidder_token"]))
    bid_id = r.json()["id"]
    for name, content in DOCS_A.items():
        r = client.post(f"/api/v1/bids/{bid_id}/documents",
                        files={"file": (name, content.encode(), "text/plain")},
                        headers=_auth_headers(test_users["bidder_token"]))
        assert r.status_code == 200

    # 4. submit -> pipeline runs (TestClient executes background task synchronously)
    r = client.post(f"/api/v1/bids/{bid_id}/submit",
                    headers=_auth_headers(test_users["bidder_token"]))
    assert r.status_code == 200
    assert client.get(f"/api/v1/bids/{bid_id}/status",
                      headers=_auth_headers(test_users["bidder_token"])).json()["pipeline_status"] == "DONE"

    # 5. drill-down (as officer)
    detail = client.get(f"/api/v1/bids/{bid_id}",
                        headers=_auth_headers(test_users["officer_token"])).json()
    statuses = {x["requirement_key"]: x["status"] for x in detail["results"]}
    assert statuses["gst_active"] == "Compliant"
    assert statuses["psara_license"] == "Compliant"
    assert statuses["not_blacklisted"] == "Compliant"
    assert detail["risk"]["risk"] == "Low"
    assert detail["risk"]["score"] >= 90
    assert detail["recommendation"]["text"]
    assert any(g["source"] == "GST" and g["mock"] for g in detail["govt_records"])

    # 6. comparison + decision + audit (as officer)
    comp = client.get(f"/api/v1/tenders/{tender['id']}/comparison",
                      headers=_auth_headers(test_users["officer_token"])).json()
    assert comp[0]["bidder"].startswith("Test Bidder")
    r = client.post(f"/api/v1/bids/{bid_id}/decision",
                    json={"decision": "Qualified", "remarks": "All checks passed"},
                    headers=_auth_headers(test_users["officer_token"]))
    assert r.json()["ok"]
    audit = client.get("/api/v1/audit",
                       headers=_auth_headers(test_users["officer_token"])).json()
    actions = {e["action"] for e in audit}
    assert {"TENDER_CREATED", "BID_SUBMITTED", "PIPELINE_DONE", "DECISION_RECORDED"} <= actions


def test_delete_tender_cascades(tmp_path, test_users):
    # create a throwaway tender + bid + doc, then delete everything
    tf = tmp_path / "t.txt"
    tf.write_text("Bidder must possess GST registration and PAN.")
    t = client.post("/api/v1/tenders",
                    data={"title": "Delete Me", "deadline": _future_deadline()},
                    files={"file": ("t.txt", tf.read_bytes(), "text/plain")},
                    headers=_auth_headers(test_users["officer_token"])).json()
    # approve tender first
    client.post(f"/api/v1/tenders/{t['id']}/approve",
                headers=_auth_headers(test_users["officer_token"]))
    bidder_id = test_users["bidder_profile_id"]
    bid = client.post("/api/v1/bids", json={"tender_id": t["id"], "bidder_id": bidder_id},
                      headers=_auth_headers(test_users["bidder_token"])).json()
    client.post(f"/api/v1/bids/{bid['id']}/documents",
                files={"file": ("d.txt", b"PAN AAECS1234F", "text/plain")},
                headers=_auth_headers(test_users["bidder_token"]))

    r = client.delete(f"/api/v1/tenders/{t['id']}",
                      headers=_auth_headers(test_users["officer_token"]))
    assert r.status_code == 200
    assert r.json()["deleted_bids"] == 1
    assert client.get(f"/api/v1/tenders/{t['id']}",
                      headers=_auth_headers(test_users["officer_token"])).status_code == 404
    assert client.get(f"/api/v1/bids/{bid['id']}",
                      headers=_auth_headers(test_users["officer_token"])).status_code == 404