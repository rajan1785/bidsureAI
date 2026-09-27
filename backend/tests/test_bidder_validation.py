# Regression: ISSUE-004 — garbage PAN/GSTIN were accepted at registration
# Found by /qa on 2026-08-30
# Report: .gstack/qa-reports/qa-report-bidsure-2026-08-30.md
from fastapi.testclient import TestClient

from app.main import app
from app.db import SessionLocal
from app.models import User, Organization
from app.auth.security import get_password_hash, create_access_token

client = TestClient(app)


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_test_users():
    """Create test users and return their tokens."""
    db = SessionLocal()
    try:
        # Create organization
        org = db.query(Organization).filter_by(name="Test Org").first()
        if not org:
            org = Organization(name="Test Org")
            db.add(org)
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

        # Create bidder profile for the user
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

        bidder_token = create_access_token(data={"sub": bidder.id, "role": bidder.role, "org_id": bidder.organization_id})

        return {"bidder_token": bidder_token}
    finally:
        db.close()


TEST_USERS = _get_test_users()


def test_valid_bidder_accepted():
    r = client.post("/api/v1/bidders", json={
        "legal_name": "Valid Co", "pan": "AAECS1234F", "gstin": "07AAECS1234F1Z5",
        "udyam": "UDYAM-DL-01-0012345", "epfo_code": "DLCPM0012345000"},
        headers=_auth_headers(TEST_USERS["bidder_token"]))
    assert r.status_code == 200
    assert r.json()["pan"] == "AAECS1234F"


def test_garbage_pan_rejected():
    r = client.post("/api/v1/bidders", json={"legal_name": "Typo Co", "pan": "WRONGPAN"},
                    headers=_auth_headers(TEST_USERS["bidder_token"]))
    assert r.status_code == 422
    assert "AAAAA9999A" in r.text


def test_garbage_gstin_rejected():
    r = client.post("/api/v1/bidders", json={"legal_name": "Typo Co", "pan": "AAECS1234F",
                                      "gstin": "NOT-A-GSTIN"},
                    headers=_auth_headers(TEST_USERS["bidder_token"]))
    assert r.status_code == 422


def test_blank_optional_identifiers_allowed():
    r = client.post("/api/v1/bidders", json={"legal_name": "Minimal Co", "pan": "AAECS1234F"},
                    headers=_auth_headers(TEST_USERS["bidder_token"]))
    assert r.status_code == 200


def test_lowercase_normalized():
    r = client.post("/api/v1/bidders", json={"legal_name": "Lower Co", "pan": "aaecs1234f"},
                    headers=_auth_headers(TEST_USERS["bidder_token"]))
    assert r.status_code == 200
    assert r.json()["pan"] == "AAECS1234F"