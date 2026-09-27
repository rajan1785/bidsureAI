"""
Reset the demo environment to a known state.

Usage:

    python scripts/seed.py --checkpoint clean
    python scripts/seed.py --checkpoint tender
    python scripts/seed.py --checkpoint evaluated
    python scripts/seed.py --checkpoint full

The script:
1. Wipes the local SQLite demo database
2. Creates demo admin/officer/bidder users directly in the DB
3. Creates JWT tokens directly
4. Seeds the tender
5. Seeds bidder A/B/C
6. Uploads bid documents
7. Submits bids for pipeline evaluation

IMPORTANT:
This script intentionally does NOT use /auth/register because the database
has already been wiped and normal registration makes officer/bidder accounts
pending admin approval.
"""

import argparse
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path
import requests

# Make backend/app importable when running:
# python scripts/seed.py
REPO = Path(__file__).resolve().parents[1]
BACKEND = REPO / "backend"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# ---------------------------------------------------------------------------
# Paths / API
# ---------------------------------------------------------------------------

REPO = Path(__file__).resolve().parents[1]

BASE = os.environ.get(
    "BIDSURE_URL",
    "http://127.0.0.1:8000",
)

API = f"{BASE}/api/v1"

DB = REPO / "backend" / "app.db"

UPLOADS = REPO / "backend" / "uploads"


# ---------------------------------------------------------------------------
# Demo data
# ---------------------------------------------------------------------------

DEMO_ADMIN = {
    "email": "admin@demo.gov.in",
    "password": "admin1234",
    "full_name": "Admin User",
    "role": "admin",
    "organization_name": "Demo Org",
}

DEMO_OFFICER = {
    "email": "officer@demo.gov.in",
    "password": "demo1234",
    "full_name": "Demo Officer",
    "role": "officer",
    "organization_name": "University of Delhi",
}

DEMO_BIDDER = {
    "email": "bidder@demo.com",
    "password": "demo1234",
    "full_name": "Demo Bidder",
    "role": "bidder",
    "organization_name": "Shakti Facility Services Pvt Ltd",
}


BIDDERS = {
    "A": {
        "legal_name": "Shakti Facility Services Pvt Ltd",
        "pan": "AAECS1234F",
        "gstin": "07AAECS1234F1Z5",
        "udyam": "UDYAM-DL-01-0012345",
        "epfo_code": "DLCPM0012345000",
    },
    "B": {
        "legal_name": "Nirmal Security Solutions Pvt Ltd",
        "pan": "AAFCN5678K",
        "gstin": "07AAFCN5678K1Z9",
        "udyam": "UDYAM-DL-02-0023456",
        "epfo_code": "DLCPM0023456000",
    },
    "C": {
        "legal_name": "Apex Guarding Co Pvt Ltd",
        "pan": "AAKCA9012M",
        "gstin": "07AAKCA9012M1Z7",
        "udyam": "UDYAM-DL-03-0034567",
        "epfo_code": "DLCPM0034567000",
    },
}


KEEP = (
    "Earnest Money Deposit",
    "Bidder must meet the experience",
    "Bidder must demonstrate",
    "Quoted rates",
    "Successful bidder must furnish",
    "Bidder must submit a valid OEM",
    "Bidder from a land-border",
)


# ---------------------------------------------------------------------------
# Auth tokens
# ---------------------------------------------------------------------------

ADMIN_TOKEN = None
OFFICER_TOKEN = None
BIDDER_TOKEN = None


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def wipe_database():
    """Delete all application data from the local SQLite DB."""

    if BASE != "http://127.0.0.1:8000":
        print("Remote target detected - skipping local DB wipe")
        return

    if not DB.exists():
        print("Database does not exist - nothing to wipe")
        return

    print("Wiping database...")

    con = sqlite3.connect(DB)

    tables = [
        row[0]
        for row in con.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type='table'
              AND name NOT LIKE 'sqlite_%'
            """
        )
    ]

    # Disable FK checks while wiping.
    con.execute("PRAGMA foreign_keys = OFF")

    for table in tables:
        con.execute(f'DELETE FROM "{table}"')

    con.execute("PRAGMA foreign_keys = ON")

    con.commit()
    con.close()

    # Remove uploaded files.
    if UPLOADS.exists():
        for path in UPLOADS.iterdir():
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except Exception as exc:
                print(f"Warning: could not remove {path}: {exc}")

    print("database wiped")


# ---------------------------------------------------------------------------
# Direct demo-user creation
# ---------------------------------------------------------------------------

def create_demo_users():
    """
    Create admin/officer/bidder directly in the DB.

    This deliberately bypasses /auth/register.

    After wipe:
        admin     -> active
        officer   -> active
        bidder    -> active

    This makes the seed deterministic and avoids the approval bootstrap
    problem.
    """

    from app.db import SessionLocal
    from app.models import User, Organization, Bidder
    from app.auth.security import get_password_hash

    db = SessionLocal()

    try:
        print("Creating demo users...")

        def get_or_create_org(name):
            org = db.query(Organization).filter(
                Organization.name == name
            ).first()

            if org:
                return org

            gem_org_id = "DEMO-" + "".join(
                c if c.isalnum() else "-"
                for c in name.upper()
            ).strip("-")

            org = Organization(
                name=name,
                gem_org_id=gem_org_id,
                is_active=1,
            )

            db.add(org)
            db.flush()
            return org
        def create_user(user_data):
            org = get_or_create_org(
                user_data["organization_name"]
            )

            user = (
                db.query(User)
                .filter_by(email=user_data["email"])
                .first()
            )

            if not user:
                user = User(
                    email=user_data["email"],
                    hashed_password=get_password_hash(
                        user_data["password"]
                    ),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    organization_id=org.id,

                    # Seed accounts are trusted demo accounts.
                    is_active=1,
                )

                db.add(user)
                db.flush()

            else:
                # Make the seed idempotent.
                user.hashed_password = get_password_hash(
                    user_data["password"]
                )
                user.full_name = user_data["full_name"]
                user.role = user_data["role"]
                user.organization_id = org.id
                user.is_active = 1

                db.flush()

            return user

        admin_user = create_user(DEMO_ADMIN)
        officer_user = create_user(DEMO_OFFICER)
        bidder_user = create_user(DEMO_BIDDER)

        # The normal /auth/register endpoint creates a minimal bidder profile.
        # Because we bypass registration, create the linked profile ourselves.
        bidder_profile = (
            db.query(Bidder)
            .filter_by(user_id=bidder_user.id)
            .first()
        )

        if not bidder_profile:
            bidder_profile = Bidder(
                legal_name=DEMO_BIDDER["organization_name"],
                organization_id=bidder_user.organization_id,
                user_id=bidder_user.id,
                contact_email=DEMO_BIDDER["email"],
            )

            db.add(bidder_profile)
            db.flush()

        bidder_user.bidder_id = bidder_profile.id

        db.commit()

        print(
            f"  admin   : {admin_user.email} "
            f"(id={admin_user.id}, active={admin_user.is_active})"
        )

        print(
            f"  officer : {officer_user.email} "
            f"(id={officer_user.id}, active={officer_user.is_active})"
        )

        print(
            f"  bidder  : {bidder_user.email} "
            f"(id={bidder_user.id}, active={bidder_user.is_active})"
        )

        return admin_user, officer_user, bidder_user

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# ---------------------------------------------------------------------------
# JWT creation
# ---------------------------------------------------------------------------

def create_token(user):
    from app.auth.security import create_access_token

    return create_access_token(
        data={
            "sub": user.id,
            "role": user.role,
            "org_id": user.organization_id,
        }
    )


def create_demo_tokens():
    global ADMIN_TOKEN
    global OFFICER_TOKEN
    global BIDDER_TOKEN

    from app.db import SessionLocal
    from app.models import User

    db = SessionLocal()

    try:
        admin = db.query(User).filter_by(
            email=DEMO_ADMIN["email"]
        ).first()

        officer = db.query(User).filter_by(
            email=DEMO_OFFICER["email"]
        ).first()

        bidder = db.query(User).filter_by(
            email=DEMO_BIDDER["email"]
        ).first()

        if not admin or not officer or not bidder:
            raise RuntimeError(
                "Demo users were not created correctly."
            )

        ADMIN_TOKEN = create_token(admin)
        OFFICER_TOKEN = create_token(officer)
        BIDDER_TOKEN = create_token(bidder)

    finally:
        db.close()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


def request_or_die(method, url, **kwargs):
    """
    Make an HTTP request and print useful error information before failing.
    """

    response = requests.request(
        method,
        url,
        timeout=kwargs.pop("timeout", 30),
        **kwargs,
    )

    if not response.ok:
        print()
        print("REQUEST FAILED")
        print(f"{method} {url}")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        print()

        response.raise_for_status()

    return response


# ---------------------------------------------------------------------------
# Service check
# ---------------------------------------------------------------------------

def check_services():
    try:
        response = requests.get(
            f"{BASE}/health",
            timeout=5,
        )

        response.raise_for_status()

    except Exception as exc:
        sys.exit(
            f"Backend not reachable at {BASE}.\n"
            f"Start it first using scripts/start_all.sh\n"
            f"Error: {exc}"
        )

    print(f"backend OK: {BASE}")


# ---------------------------------------------------------------------------
# Tender
# ---------------------------------------------------------------------------

def seed_tender():
    if not OFFICER_TOKEN:
        raise RuntimeError("Officer token missing")

    tender_pdf = (
        REPO
        / "demo-assets"
        / "Tendernotice_1.pdf"
    )

    if not tender_pdf.exists():
        raise FileNotFoundError(
            f"Tender PDF not found: {tender_pdf}"
        )

    print("Uploading tender...")

    with tender_pdf.open("rb") as f:
        response = request_or_die(
            "POST",
            f"{API}/tenders",
            data={
                "title": (
                    "Security Services Tender — "
                    "University of Delhi, South Campus"
                ),
                "organization": "University of Delhi",
                "ref_no": (
                    "GB-SDC/074/"
                    "Security Services/2024-25"
                ),
            },
            files={
                "file": (
                    tender_pdf.name,
                    f,
                    "application/pdf",
                )
            },
            headers=auth_headers(OFFICER_TOKEN),
            timeout=180,
        )

    tender = response.json()

    tender_id = tender["id"]

    print(
        f"tender {tender_id} uploaded "
        f"with {len(tender.get('requirements', []))} requirements"
    )

    # Officer curation.
    removed = 0

    for req in tender.get("requirements", []):

        if (
            not req.get("rule_key")
            and not req.get("text", "").startswith(KEEP)
        ):
            request_or_die(
                "DELETE",
                (
                    f"{API}/tenders/"
                    f"{tender_id}/requirements/"
                    f"{req['id']}"
                ),
                headers=auth_headers(OFFICER_TOKEN),
                timeout=10,
            )

            removed += 1

    if removed:
        print(
            f"officer curation: "
            f"removed {removed} mined/duplicate requirements"
        )

    request_or_die(
        "POST",
        f"{API}/tenders/{tender_id}/approve",
        headers=auth_headers(OFFICER_TOKEN),
        timeout=20,
    )

    print(f"tender {tender_id} approved")

    return tender_id


# ---------------------------------------------------------------------------
# Bidder / bids
# ---------------------------------------------------------------------------

def create_bidder_profile(key):
    bidder_data = BIDDERS[key].copy()

    bidder_data["contact_email"] = DEMO_BIDDER["email"]

    response = request_or_die(
        "POST",
        f"{API}/bidders",
        json=bidder_data,
        headers=auth_headers(BIDDER_TOKEN),
        timeout=20,
    )

    return response.json()


def seed_bid(tender_id, key, submit=True):
    print(f"Creating bidder {key}...")

    bidder = create_bidder_profile(key)

    bidder_id = bidder["id"]

    response = request_or_die(
        "POST",
        f"{API}/bids",
        json={
            "tender_id": tender_id,
            "bidder_id": bidder_id,
        },
        headers=auth_headers(BIDDER_TOKEN),
        timeout=20,
    )

    bid = response.json()

    bid_id = bid["id"]

    print(
        f"bidder {key}: profile={bidder_id}, "
        f"bid={bid_id}"
    )

    bidder_dir = (
        REPO
        / "demo-assets"
        / "bidders"
        / key
    )

    pdfs = sorted(bidder_dir.glob("*.pdf"))

    if not pdfs:
        print(
            f"Warning: no PDFs found for bidder {key} "
            f"in {bidder_dir}"
        )

    for pdf in pdfs:

        print(
            f"  uploading {pdf.name}"
        )

        with pdf.open("rb") as f:
            request_or_die(
                "POST",
                f"{API}/bids/{bid_id}/documents",
                files={
                    "file": (
                        pdf.name,
                        f,
                        "application/pdf",
                    )
                },
                headers=auth_headers(BIDDER_TOKEN),
                timeout=60,
            )

    if not submit:
        print(
            f"bidder {key} bid {bid_id}: "
            "documents uploaded, not submitted"
        )
        return bid_id

    print(
        f"submitting bidder {key} bid {bid_id}..."
    )

    request_or_die(
        "POST",
        f"{API}/bids/{bid_id}/submit",
        headers=auth_headers(BIDDER_TOKEN),
        timeout=30,
    )

    status = "QUEUED"

    for _ in range(120):

        response = request_or_die(
            "GET",
            f"{API}/bids/{bid_id}/status",
            headers=auth_headers(BIDDER_TOKEN),
            timeout=10,
        )

        status = response.json().get(
            "pipeline_status",
            "UNKNOWN",
        )

        if status in ("DONE", "ERROR"):
            break

        time.sleep(0.5)

    print(
        f"bidder {key} bid {bid_id}: {status}"
    )

    return bid_id


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--checkpoint",
        default="evaluated",
        choices=[
            "clean",
            "tender",
            "evaluated",
            "full",
        ],
    )

    args = parser.parse_args()

    print()
    print("=" * 60)
    print("BidSureAI Demo Seeder")
    print("=" * 60)
    print(
        f"checkpoint: {args.checkpoint}"
    )
    print()

    check_services()

    # ---------------------------------------------------------------
    # 1. Wipe
    # ---------------------------------------------------------------

    wipe_database()

    if args.checkpoint == "clean":
        print()
        print("DONE: database is clean")
        return

    # ---------------------------------------------------------------
    # 2. Create users DIRECTLY in DB
    # ---------------------------------------------------------------

    create_demo_users()

    # ---------------------------------------------------------------
    # 3. Create JWTs DIRECTLY
    # ---------------------------------------------------------------

    create_demo_tokens()

    print()
    print("demo authentication ready")
    print(f"  admin   = {DEMO_ADMIN['email']}")
    print(f"  officer = {DEMO_OFFICER['email']}")
    print(f"  bidder  = {DEMO_BIDDER['email']}")

    # ---------------------------------------------------------------
    # 4. Tender
    # ---------------------------------------------------------------

    tender_id = seed_tender()

    if args.checkpoint == "tender":
        print()
        print("=" * 60)
        print("DONE: tender checkpoint")
        print("=" * 60)
        return

    # ---------------------------------------------------------------
    # 5. Bidder A + B
    # ---------------------------------------------------------------

    seed_bid(
        tender_id,
        "A",
        submit=True,
    )

    seed_bid(
        tender_id,
        "B",
        submit=True,
    )

    # ---------------------------------------------------------------
    # 6. Optional bidder C
    # ---------------------------------------------------------------

    if args.checkpoint == "full":
        seed_bid(
            tender_id,
            "C",
            submit=True,
        )

    # ---------------------------------------------------------------
    # Done
    # ---------------------------------------------------------------

    print()
    print("=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print()
    print("Demo accounts:")
    print()
    print("Admin:")
    print("  email    :", DEMO_ADMIN["email"])
    print("  password :", DEMO_ADMIN["password"])
    print()
    print("Officer:")
    print("  email    :", DEMO_OFFICER["email"])
    print("  password :", DEMO_OFFICER["password"])
    print()
    print("Bidder:")
    print("  email    :", DEMO_BIDDER["email"])
    print("  password :", DEMO_BIDDER["password"])
    print()


if __name__ == "__main__":
    main()