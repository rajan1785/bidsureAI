"""Pydantic schemas for auth endpoints."""
from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""
    role: str = "bidder"  # "bidder" or "officer"
    organization_name: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("bidder", "officer", "admin"):
            raise ValueError("Role must be 'bidder', 'officer', or 'admin'")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: str | None = None

    @field_validator("role")
    @classmethod
    def validate_login_role(cls, v: str | None) -> str | None:
        if v is not None and v not in ("bidder", "officer", "admin"):
            raise ValueError("Role must be 'bidder', 'officer', or 'admin'")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    organization_id: int
    is_active: int
    created_at: str

    class Config:
        from_attributes = True


class UserApprove(BaseModel):
    user_id: int
    is_active: bool
