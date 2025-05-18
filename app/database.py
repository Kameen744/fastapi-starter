from sqlmodel import SQLModel, Session, create_engine
from .config import settings
from .migrations.tables import User

# engine = create_engine(settings.DATABASE_URL)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,  # Prevents connection timeouts
    connect_args={"charset": "utf8mb4"}  # Support full Unicode
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session