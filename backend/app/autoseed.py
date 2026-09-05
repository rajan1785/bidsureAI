"""Self-seeding on startup for ephemeral deployments.

Render's free tier resets the disk on every cold start, wiping SQLite. When
AUTO_SEED is set and the database is empty, a background thread replays the
demo seed through the app's own API so the public site always shows the
A/B/C story without manual reseeding.
"""
import os
import threading
import time
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


def _seed(app):
    from fastapi.testclient import TestClient

    client = TestClient(app)
    tender_pdf = REPO / "demo-assets" / "Tendernotice_1.pdf"
    if not tender_pdf.exists():
        return
    with tender_pdf.open("rb") as f:
        r = client.post("/api/v1/tenders", data={
            "title": "Security Services Tender — University of Delhi, South Campus",
            "organization": "University of Delhi",
            "ref_no": "GB-SDC/074/Security Services/2024-25",
        }, files={"file": (tender_pdf.name, f, "application/pdf")})
    tender = r.json()
    for req in tender["requirements"]:
        if not req["rule_key"] and not req["text"].startswith(KEEP):
            client.delete(f"/api/v1/tenders/{tender['id']}/requirements/{req['id']}")
    client.post(f"/api/v1/tenders/{tender['id']}/approve")

    for key, body in BIDDERS.items():
        bidder = client.post("/api/v1/bidders", json=body).json()
        bid = client.post("/api/v1/bids", json={"tender_id": tender["id"],
                                                "bidder_id": bidder["id"]}).json()
        for pdf in sorted((REPO / "demo-assets" / "bidders" / key).glob("*.pdf")):
            with pdf.open("rb") as f:
                client.post(f"/api/v1/bids/{bid['id']}/documents",
                            files={"file": (pdf.name, f, "application/pdf")})
        # TestClient runs the background pipeline synchronously
        client.post(f"/api/v1/bids/{bid['id']}/submit")


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
