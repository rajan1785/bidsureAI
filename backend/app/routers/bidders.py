import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.audit import log_event
from app.auth.dependencies import get_current_user, require_role
from app.db import get_db
from app.models import Bidder, User

router = APIRouter(prefix="/bidders", tags=["bidders"])

ID_FORMATS = {
    "pan": (r"^[A-Z]{5}\d{4}[A-Z]$", "PAN must look like AAAAA9999A"),
    "gstin": (r"^\d{2}[A-Z]{5}\d{4}[A-Z][A-Z\d]Z[A-Z\d]$", "GSTIN must be 15 characters like 07AAECS1234F1Z5"),
    "udyam": (r"^UDYAM-[A-Z]{2}-\d{2}-\d{7}$", "Udyam number must look like UDYAM-DL-01-0012345"),
    "epfo_code": (r"^[A-Z]{5}\d{10}$", "EPFO code must look like DLCPM0012345000"),
}


class BidderIn(BaseModel):
    legal_name: str
    pan: str = ""
    gstin: str = ""
    udyam: str = ""
    epfo_code: str = ""
    contact_email: str = ""

    @field_validator("pan", "gstin", "udyam", "epfo_code")
    @classmethod
    def check_format(cls, v: str, info):
        v = v.strip().upper()
        if not v:
            return v  # optional identifiers may be blank
        pattern, message = ID_FORMATS[info.field_name]
        if not re.match(pattern, v):
            raise ValueError(message)
        return v


@router.post("", dependencies=[Depends(get_current_user)])
def create_bidder(body: BidderIn, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "bidder":
        # Bidder can only create/update their own profile
        bidder = db.query(Bidder).filter_by(user_id=current_user.id).first()
        if not bidder:
            raise HTTPException(404, "Bidder profile not found")
        for k, v in body.model_dump().items():
            setattr(bidder, k, v)
    elif current_user.role == "officer":
        # Officer creates bidder for their org
        bidder = Bidder(**body.model_dump(), organization_id=current_user.organization_id)
        db.add(bidder)
    else:
        raise HTTPException(403, "Not authorized")
    db.commit()
    log_event(db, current_user.role, "BIDDER_UPSERTED", f"bidder:{bidder.id}", bidder.legal_name)
    return _dict(bidder)


@router.get("", dependencies=[Depends(get_current_user)])
def list_bidders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role == "officer":
        return [_dict(b) for b in db.query(Bidder).filter_by(organization_id=current_user.organization_id).all()]
    elif current_user.role == "bidder":
        bidder = db.query(Bidder).filter_by(user_id=current_user.id).first()
        return [_dict(bidder)] if bidder else []
    return [_dict(b) for b in db.query(Bidder).all()]  # admin


def _dict(b: Bidder):
    return {"id": b.id, "legal_name": b.legal_name, "pan": b.pan, "gstin": b.gstin,
            "udyam": b.udyam, "epfo_code": b.epfo_code, "contact_email": b.contact_email}
