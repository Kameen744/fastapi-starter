from datetime import datetime
from sqlmodel import Field, SQLModel
from sqlalchemy import text
import uuid
from uuid import UUID

def id_field():
    return Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True
    )

def created_field():
    return Field(
        default=None,
        nullable=False,
        sa_column_kwargs={"server_default": text("CURRENT_TIMESTAMP")}
    )

def updated_field():
    return Field(
        default=None,
        nullable=False,
        sa_column_kwargs={
            "server_default": text("CURRENT_TIMESTAMP"),
            "onupdate": text("CURRENT_TIMESTAMP")
        }
    )

class BaseTable(SQLModel):
    id: UUID = id_field()
    created_at: datetime = created_field()
    updated_at: datetime = updated_field()