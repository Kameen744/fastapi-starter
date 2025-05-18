from uuid import UUID
from datetime import datetime, timezone
from typing import Optional, Annotated
from sqlmodel import Field, SQLModel
from pydantic import BaseModel, EmailStr
from enum import Enum as PyEnum
from ..migrations.base_table import BaseTable
# from migrations.tables import User

class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"

# class User(BaseTable, table=True):
#     email: str = Field(unique=True, index=True)
#     username: str = Field(unique=True, index=True)
#     first_name: str | None = Field(default=None)
#     last_name: str | None  = Field(default=None)
#     profile_picture_url: str | None = Field(default=None)
#     hashed_password: str
#     is_active: bool = Field(default=True)
#     role: UserRole = Field(default=UserRole.USER)
   

class UserSchema(BaseTable):
    email: EmailStr | None = None
    username: str | None = None
    is_active: bool = False
    role: UserRole = UserRole.USER

class UserCreate(UserSchema):
    email: EmailStr
    username: str
    password: str


class UserUpdate(UserSchema):
    password: Optional[str] = None


# class UserInDBBase(UserBase):
#     id: Optional[int] = None
#     created_at: Optional[datetime] = None
#     updated_at: Optional[datetime] = None

    # class Config:
    #     orm_mode = True
    #     from_attributes = True


# class User(UserInDBBase):
#     pass


class UserInDB(UserSchema):
    hashed_password: str


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
