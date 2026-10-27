import hashlib
import secrets
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, current_user, hash_password, verify_password
from app.models import Attraction, PasswordResetToken, User
from app.models.domain import utcnow
from app.schemas.auth import (LoginIn, PasswordResetConfirmIn,
                              PasswordResetRequestIn, RegisterIn, SessionOut,
                              UserOut)
from app.services.email import send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


def user_out(db: Session, user: User) -> UserOut:
    assigned_attraction_name = None
    if user.assigned_attraction_id:
        assigned_attraction_name = db.scalar(
            select(Attraction.name).where(Attraction.id == user.assigned_attraction_id)
        )
    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        assigned_attraction_id=user.assigned_attraction_id,
        assigned_attraction_name=assigned_attraction_name,
    )


@router.post("/register", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    user = User(full_name=payload.full_name.strip(), email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account already exists for this email.") from exc
    db.refresh(user)
    return SessionOut(access_token=create_access_token(user), user=user_out(db, user))


@router.post("/login", response_model=SessionOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    return SessionOut(access_token=create_access_token(user), user=user_out(db, user))


@router.post("/password-reset/request")
def request_password_reset(payload: PasswordResetRequestIn, db: Session = Depends(get_db)):
    """Issue a short-lived, one-time reset link without revealing account existence."""
    user = db.scalar(
        select(User).where(
            User.email == payload.email.lower(),
            User.role == "customer",
            User.is_active.is_(True),
        )
    )
    if user:
        now = utcnow()
        for previous in db.scalars(
            select(PasswordResetToken).where(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.used_at.is_(None),
            )
        ):
            previous.used_at = now
        raw_token = secrets.token_urlsafe(32)
        reset = PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=now + timedelta(minutes=get_settings().password_reset_minutes),
        )
        db.add(reset)
        db.commit()
        reset_url = f"{get_settings().frontend_origin}/reset-password?token={raw_token}"
        delivery = send_password_reset_email(
            recipient=user.email,
            visitor_name=user.full_name,
            reset_url=reset_url,
        )
        if delivery != "SENT":
            reset.used_at = utcnow()
            db.commit()
    return {"message": "If that customer account exists, a password-reset link has been sent."}


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(payload: PasswordResetConfirmIn, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
    reset = db.scalar(
        select(PasswordResetToken)
        .where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
        )
        .with_for_update()
    )
    if not reset or reset.expires_at < utcnow():
        raise HTTPException(status_code=409, detail="This password-reset link is invalid or expired.")
    user = db.scalar(select(User).where(User.id == reset.user_id, User.role == "customer", User.is_active.is_(True)))
    if not user:
        raise HTTPException(status_code=409, detail="This password-reset link is invalid or expired.")
    user.password_hash = hash_password(payload.password)
    reset.used_at = utcnow()
    for other in db.scalars(
        select(PasswordResetToken).where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
    ):
        other.used_at = utcnow()
    db.commit()


@router.get("/me", response_model=UserOut)
def me(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return user_out(db, user)
