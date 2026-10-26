from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, current_user, hash_password, verify_password
from app.models import User
from app.schemas.auth import LoginIn, RegisterIn, SessionOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


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
    return SessionOut(access_token=create_access_token(user), user=UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role))


@router.post("/login", response_model=SessionOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email or password is incorrect.")
    return SessionOut(access_token=create_access_token(user), user=UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(current_user)):
    return UserOut(id=user.id, full_name=user.full_name, email=user.email, role=user.role)
