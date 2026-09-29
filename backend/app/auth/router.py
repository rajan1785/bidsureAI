"""Auth router: register, login, me, admin user management."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.db import get_db
from app.auth import security, schemas
from app.auth.dependencies import get_current_user, require_role
from app.models import User, Organization, Bidder, utcnow

router = APIRouter(prefix="/auth", tags=["auth"])

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


@router.post("/register", response_model=schemas.UserOut)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if organization exists or create
    org = db.query(Organization).filter_by(name=user_in.organization_name).first()
    if not org:
        org = Organization(name=user_in.organization_name)
        db.add(org)
        db.flush()

    # Check email unique
    if db.query(User).filter_by(email=user_in.email).first():
        raise HTTPException(400, "Email already registered")

    hashed_pwd = security.get_password_hash(user_in.password)
    # Every new account starts inactive and waits for an admin to approve it.
    is_active = 0

    user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=user_in.role,
        organization_id=org.id,
        is_active=is_active,
    )
    db.add(user)
    db.flush()

    # If bidder, create linked bidder profile (minimal - they complete it later)
    if user_in.role == "bidder":
        bidder = Bidder(
            legal_name=user_in.full_name or user_in.email,
            organization_id=org.id,
            user_id=user.id,
        )
        db.add(bidder)
        db.flush()
        user.bidder_id = bidder.id

    db.commit()
    return user


@router.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=form_data.email).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if form_data.role and user.role != form_data.role:
        raise HTTPException(status.HTTP_403_FORBIDDEN, f"This account is registered as {user.role}. Select that role to continue.")
    if not user.is_active:
        raise HTTPException(403, "Account pending admin approval")

    access_token = security.create_access_token(
        data={"sub": user.id, "role": user.role, "org_id": user.organization_id},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    from app.models import utcnow

# ...

    user.last_login = utcnow()
    db.commit()
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# Admin endpoints
@router.get("/admin/users", response_model=list[schemas.UserOut], dependencies=[Depends(require_role("admin"))])
def list_all_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/admin/users/pending", response_model=list[schemas.UserOut], dependencies=[Depends(require_role("admin"))])
def list_pending_users(db: Session = Depends(get_db)):
    return db.query(User).filter_by(is_active=0).all()


@router.post("/admin/users/{user_id}/approve", dependencies=[Depends(require_role("admin"))])
def approve_user(user_id: int, body: schemas.UserApprove, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    user.is_active = 1 if body.is_active else 0
    db.commit()
    return {"ok": True, "user_id": user.id, "is_active": user.is_active}
