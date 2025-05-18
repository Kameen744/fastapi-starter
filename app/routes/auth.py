from datetime import timedelta
from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from ..crud.auth import authenticate_user
from ..crud.security import (
    create_access_token,
    get_password_hash,
    verify_password_reset_token,
    generate_password_reset_token,
)
from ..config import settings
from ..database import get_session
from ..models.token import Token
from ..migrations.tables import User
from ..models.user import UserCreate, PasswordReset, PasswordResetConfirm

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(get_session),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, user.role, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/register", response_model=Token)
def register_user(
    user_in: Annotated[UserCreate, Body()],
    db: Session = Depends(get_session),
) -> Any:
    """
    Create new user
    """
    # Check if user with this email exists
    user = db.exec(select(User).where(User.email == user_in.email)).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    # Check if user with this username exists
    user = db.exec(select(User).where(User.username == user_in.username)).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists",
        )
    
    # Create new user
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            db_user.id, db_user.role, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }


@router.post("/password-reset")
def request_password_reset(
    body: PasswordReset,
    db: Session = Depends(get_session),
) -> Any:
    """
    Request password reset
    """
    user = db.exec(select(User).where(User.email == body.email)).first()
    if not user:
        # Return success anyway to prevent email enumeration
        return {"msg": "Password reset email sent"}
    
    password_reset_token = generate_password_reset_token(email=body.email)
    
    # In a real app, send email with token
    print(f"Password reset token for {body.email}: {password_reset_token}")
    
    return {"msg": "Password reset email sent"}


@router.post("/password-reset/confirm")
def reset_password_confirm(
    body: PasswordResetConfirm,
    db: Session = Depends(get_session),
) -> Any:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token",
        )
    
    user = db.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user.hashed_password = get_password_hash(body.new_password)
    db.add(user)
    db.commit()
    
    return {"msg": "Password updated successfully"}
