"""Auth module exports."""
from app.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_token,
    SECRET_KEY,
    ALGORITHM,
)
from app.auth.dependencies import get_current_user, require_role, get_current_user_optional
from app.auth.schemas import UserCreate, UserLogin, Token, UserOut, UserApprove
from app.auth.router import router as auth_router

__all__ = [
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "SECRET_KEY",
    "ALGORITHM",
    "get_current_user",
    "require_role",
    "get_current_user_optional",
    "UserCreate",
    "UserLogin",
    "Token",
    "UserOut",
    "UserApprove",
    "auth_router",
]