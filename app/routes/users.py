from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..database import get_session
# from ..models.user import User, UserRole
from ..migrations.tables import User
from ..models.user import UserSchema, UserUpdate
from ..crud.auth import get_current_active_user, get_current_admin_user

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user
    """
    return current_user


@router.put("/me", response_model=UserSchema)
def update_user_me(
    user_in: UserUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user
    """
    from ..crud.security import get_password_hash
    
    # Check if email exists and is different from current user
    if user_in.email and user_in.email != current_user.email:
        user = db.exec(select(User).where(User.email == user_in.email)).first()
        if user:
            raise HTTPException(
                status_code=400,
                detail="Email already registered",
            )
    
    # Check if username exists and is different from current user
    if user_in.username and user_in.username != current_user.username:
        user = db.exec(select(User).where(User.username == user_in.username)).first()
        if user:
            raise HTTPException(
                status_code=400,
                detail="Username already registered",
            )
    
    # Update user
    update_data = user_in.dict(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.get("", response_model=List[UserSchema])
def read_users(
    db: Session = Depends(get_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Retrieve users (admin only)
    """
    users = db.exec(select(User).offset(skip).limit(limit)).all()
    return users


@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Get a specific user by id (admin only)
    """
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    return user


@router.put("/{user_id}", response_model=UserSchema)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    """
    Update a user (admin only)
    """
    from ..crud.security import get_password_hash
    
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )
    
    # Update user
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        update_data["hashed_password"] = get_password_hash(update_data["password"])
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
