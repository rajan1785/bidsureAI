"""Self-seeding on startup for ephemeral deployments.

Render's free tier resets the disk on every cold start, wiping SQLite. When
AUTO_SEED is set and the database is empty, a background thread replays the
demo seed through the app's own API so the public site always shows the
A/B/C story without manual reseeding.
"""
import os
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).parents[2]

KEEP = ("Earnest Money Deposit", "Bidder must meet the experience",
        "Bidder must demonstrate", "Quoted rates",
        "Successful bidder must furnish", "Bidder must submit a valid OEM",
        "Bidder from a land-border")

BIDDERS = {
    "A": {"legal_name": "Shakti Facility Services Pvt Ltd", "pan": "AAECS1234F",
          "gstin": "07AAECS1234F1Z5", "udyam": "UDYAM-DL-01-0012345",
          "epfo_code": "DLCPM0012345000"},
    "B": {"legal_name": "Nirmal Security Solutions Pvt Ltd", "pan": "AAFCN5678K",
          "gstin": "07AAFCN5678K1Z9", "udyam": "UDYAM-DL-02-0023456",
          "epfo_code": "DLCPM0023456000"},
    "C": {"legal_name": "Apex Guarding Co Pvt Ltd", "pan": "AAKCA9012M",
          "gstin": "07AAKCA9012M1Z7", "udyam": "UDYAM-DL-03-0034567",
          "epfo_code": "DLCPM0034567000"},
}

DEMO_OFFICER = {"email": "officer@demo.gov.in", "password": "demo1234", "full_name": "Demo Officer", "role": "officer", "organization_name": "University of Delhi"}
DEMO_BIDDER = {"email": "bidder@demo.com", "password": "demo1234", "full_name": "Demo Bidder", "role": "bidder", "organization_name": "Shakti Facility Services Pvt Ltd"}


def _get_or_create_user(db, user_data):
    """Get existing user or create new one."""
    from app.models import User
    user = db.query(User).filter_by(email=user_data["email"]).first()
    if user:
        return user
    from app.auth.security import get_password_hash
    from app.models import Organization
    org = db.query(Organization).filter_by(name=user_data["organization_name"]).first()
    if not org:
        org = Organization(name=user_data["organization_name"])
        db.add(org)
        db.flush()
    user = User(
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
        full_name=user_data["full_name"],
        role=user_data["role"],
        organization_id=org.id,
        is_active=1,
    )
    db.add(user)
    db.flush()
    return user


def _create_token(user_id: int, role: str, org_id: int) -> str:
    from app.auth.security import create_access_token
    return create_access_token(data={"sub": user_id, "role": role, "org_id": org_id})


def _seed(app):
    from fastapi.testclient import TestClient
    from app.db import SessionLocal
    from app.models import Tender, Organization, User, Bidder

    client = TestClient(app)

    # Create or get demo users and tokens
    db = SessionLocal()
    try:
        officer_user = _get_or_create_user(db, DEMO_OFFICER)
        bidder_user = _get_or_create_user(db, DEMO_BIDDER)
        db.commit()
        officer_token = _create_token(officer_user.id, officer_user.role, officer_user.organization_id)
        bidder_token = _create_token(bidder_user.id, bidder_user.role, bidder_user.organization_id)
    finally:
        db.close()

    def auth_headers(token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    tender_pdf = REPO / "demo-assets" / "Tendernotice_1.pdf"
    if not tender_pdf.exists():
        return
    with tender_pdf.open("rb") as f:
        r = client.post("/api/v1/tenders", data={
            "title": "Security Services Tender — University of Delhi, South Campus",
            "organization": "University of Delhi",
            "ref_no": "GB-SDC/074/Security Services/2024-25",
            "deadline": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
        }, files={"file": (tender_pdf.name, f, "application/pdf")},
            headers=auth_headers(officer_token))
    tender = r.json()
    for req in tender["requirements"]:
        if not req["rule_key"] and not req["text"].startswith(KEEP):
            client.delete(f"/api/v1/tenders/{tender['id']}/requirements/{req['id']}",
                          headers=auth_headers(officer_token))
    client.post(f"/api/v1/tenders/{tender['id']}/approve", headers=auth_headers(officer_token))

    for key, body in BIDDERS.items():
        bidder_data = body.copy()
        bidder_data["contact_email"] = DEMO_BIDDER["email"]
        bidder = client.post("/api/v1/bidders", json=bidder_data,
                             headers=auth_headers(bidder_token)).json()
        bid = client.post("/api/v1/bids", json={"tender_id": tender["id"],
                                                "bidder_id": bidder["id"]},
                          headers=auth_headers(bidder_token)).json()
        for pdf in sorted((REPO / "demo-assets" / "bidders" / key).glob("*.pdf")):
            with pdf.open("rb") as f:
                client.post(f"/api/v1/bids/{bid['id']}/documents",
                            files={"file": (pdf.name, f, "application/pdf")},
                            headers=auth_headers(bidder_token))
        # TestClient runs the background pipeline synchronously
        client.post(f"/api/v1/bids/{bid['id']}/submit", headers=auth_headers(bidder_token))


def maybe_autoseed(app):
    if not os.environ.get("AUTO_SEED"):
        return

    def run():
        time.sleep(2)  # let the govt replica come up first
        try:
            from app.db import SessionLocal
            from app.models import Tender

            db = SessionLocal()
            empty = db.query(Tender).count() == 0
            db.close()
            if empty:
                _seed(app)
        except Exception:
            pass  # seeding is best-effort; the API must come up regardless

    threading.Thread(target=run, daemon=True).start()
