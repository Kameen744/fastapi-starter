from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel
from sqlalchemy import text
import uuid
from uuid import UUID

# Base model with properly defined timestamps
class TimestampModel(SQLModel):
    """Base model with timestamp fields"""
    
    created_at: datetime = Field(
        default=None,
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )
    
    updated_at: datetime = Field(
        default=None,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )

# Base model with UUID ID field
class UUIDModel(SQLModel):
    """Base model with UUID primary key"""
    
    id: UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

# Complete base model with both UUID and timestamps
class BaseTable(UUIDModel, TimestampModel):
    """Base model with UUID primary key and timestamps"""
    pass