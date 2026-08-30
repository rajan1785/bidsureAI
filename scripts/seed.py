"""Reset the demo to a known state.

Usage (backend + govt api must be running):
  python scripts/seed.py --checkpoint clean      # empty database
  python scripts/seed.py --checkpoint tender     # tender uploaded + approved
  python scripts/seed.py --checkpoint evaluated  # + bidders A and B fully evaluated
                                                 #   (bidder C left for the live demo)
  python scripts/seed.py --checkpoint full       # + bidder C also evaluated
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

import requests

REPO = Path(__file__).parents[1]
API = "http://127.0.0.1:8000"
DB = REPO / "backend" / "app.db"

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


def wipe():
    if not DB.exists():
        return
    con = sqlite3.connect(DB)
    tables = [r[0] for r in con.execute(
        "select name from sqlite_master where type='table' and name not like 'sqlite_%'")]
    for t in tables:
        con.execute(f"delete from {t}")
    con.commit()
    con.close()
    for f in (REPO / "backend" / "uploads").glob("*"):
        f.unlink()
    print("database wiped")


def check_services():
    try:
        requests.get(f"{API}/health", timeout=3)
    except Exception:
        sys.exit("backend not running on :8000 — start it first (scripts/start_all.sh)")


def seed_tender() -> int:
    tender_pdf = REPO / "demo-assets" / "Tendernotice_1.pdf"
    with tender_pdf.open("rb") as f:
        r = requests.post(f"{API}/tenders", data={
            "title": "Security Services Tender — University of Delhi, South Campus",
            "organization": "University of Delhi",
            "ref_no": "GB-SDC/074/Security Services/2024-25",
        }, files={"file": (tender_pdf.name, f, "application/pdf")}, timeout=180)
    r.raise_for_status()
    tender = r.json()
    requests.post(f"{API}/tenders/{tender['id']}/approve", timeout=10).raise_for_status()
    print(f"tender {tender['id']} uploaded, {len(tender['requirements'])} requirements, approved")
    return tender["id"]


def seed_bid(tender_id: int, key: str, submit=True) -> int:
    r = requests.post(f"{API}/bidders", json=BIDDERS[key], timeout=10)
    bidder_id = r.json()["id"]
    r = requests.post(f"{API}/bids", json={"tender_id": tender_id, "bidder_id": bidder_id}, timeout=10)
    bid_id = r.json()["id"]
    for pdf in sorted((REPO / "demo-assets" / "bidders" / key).glob("*.pdf")):
        with pdf.open("rb") as f:
            requests.post(f"{API}/bids/{bid_id}/documents",
                          files={"file": (pdf.name, f, "application/pdf")},
                          timeout=60).raise_for_status()
    if submit:
        requests.post(f"{API}/bids/{bid_id}/submit", timeout=10).raise_for_status()
        for _ in range(120):
            status = requests.get(f"{API}/bids/{bid_id}/status", timeout=10).json()["pipeline_status"]
            if status in ("DONE", "ERROR"):
                break
            time.sleep(0.5)
        print(f"bidder {key} bid {bid_id}: {status}")
    else:
        print(f"bidder {key} bid {bid_id}: documents uploaded, not submitted")
    return bid_id


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="evaluated",
                    choices=["clean", "tender", "evaluated", "full"])
    args = ap.parse_args()

    check_services()
    wipe()
    if args.checkpoint == "clean":
        return
    tender_id = seed_tender()
    if args.checkpoint == "tender":
        return
    seed_bid(tender_id, "A")
    seed_bid(tender_id, "B")
    if args.checkpoint == "full":
        seed_bid(tender_id, "C")
    print("seed complete")


if __name__ == "__main__":
    main()
