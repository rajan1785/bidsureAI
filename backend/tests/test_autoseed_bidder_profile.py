"""A bidder user is only usable with a linked Bidder profile.

POST /bidders answers 404 "Bidder profile not found" without one, which is what
the seeded demo account hit on the deployed site: autoseed created the user but
not the profile, so the Bidder Portal could not save firm details and the seed
never got as far as creating any bids.
"""
from app.autoseed import DEMO_BIDDER, _get_or_create_user
from app.auth.security import get_password_hash
from app.models import Bidder, Organization, User


def test_seeded_bidder_user_gets_a_linked_profile(db):
    user = _get_or_create_user(db, DEMO_BIDDER)
    db.commit()

    profile = db.query(Bidder).filter_by(user_id=user.id).first()
    assert profile is not None, "bidder user was created without a Bidder profile"
    assert user.bidder_id == profile.id


def test_bidder_user_that_predates_the_profile_is_repaired(db):
    """Databases seeded before the fix already hold a profile-less bidder, and
    _get_or_create_user returns early for a user that exists."""
    org = Organization(name="Legacy Bidder Co")
    db.add(org)
    db.flush()
    stale = User(
        email="legacy-bidder@demo.com",
        hashed_password=get_password_hash("demo1234"),
        full_name="Legacy Bidder",
        role="bidder",
        organization_id=org.id,
        is_active=1,
    )
    db.add(stale)
    db.commit()
    assert db.query(Bidder).filter_by(user_id=stale.id).first() is None

    returned = _get_or_create_user(db, {
        "email": "legacy-bidder@demo.com",
        "password": "demo1234",
        "full_name": "Legacy Bidder",
        "role": "bidder",
        "organization_name": "Legacy Bidder Co",
    })
    db.commit()

    assert returned.id == stale.id
    profile = db.query(Bidder).filter_by(user_id=stale.id).first()
    assert profile is not None, "existing bidder user was not given a profile"


def test_officer_user_gets_no_bidder_profile(db):
    officer = _get_or_create_user(db, {
        "email": "officer-no-profile@demo.gov.in",
        "password": "demo1234",
        "full_name": "Officer",
        "role": "officer",
        "organization_name": "Some Department",
    })
    db.commit()
    assert db.query(Bidder).filter_by(user_id=officer.id).first() is None
