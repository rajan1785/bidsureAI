from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.audit import log_event
from app.db import get_db
from app.models import Bidder

router = APIRouter(prefix="/bidders", tags=["bidders"])


class BidderIn(BaseModel):
    legal_name: str
    pan: str = ""
    gstin: str = ""
    udyam: str = ""
    epfo_code: str = ""
    contact_email: str = ""


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
