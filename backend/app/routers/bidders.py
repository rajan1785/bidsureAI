import re

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.audit import log_event
from app.db import get_db
from app.models import Bidder

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


@router.post("")
def create_bidder(body: BidderIn, db: Session = Depends(get_db)):
    b = Bidder(**body.model_dump())
    db.add(b)
    db.commit()
    log_event(db, "bidder", "BIDDER_REGISTERED", f"bidder:{b.id}", b.legal_name)
    return _dict(b)


@router.get("")
def list_bidders(db: Session = Depends(get_db)):
    return [_dict(b) for b in db.query(Bidder).all()]


def _dict(b: Bidder):
    return {"id": b.id, "legal_name": b.legal_name, "pan": b.pan, "gstin": b.gstin,
            "udyam": b.udyam, "epfo_code": b.epfo_code, "contact_email": b.contact_email}
