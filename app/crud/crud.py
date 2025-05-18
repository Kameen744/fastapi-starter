from sqlmodel import select
from ..database import get_session
from ..migrations.tables import User, UserRole
from ..crud.security import get_password_hash


def create_initial_admin():
    db = next(get_session())
    admin = db.exec(select(User).where(User.role == UserRole.ADMIN)).first()
    if not admin:
        admin_user = User(
            email="admin@amref.com",
            username="admin",
            hashed_password=get_password_hash("admin"),
            role=UserRole.ADMIN,
        )
        
        db.add(admin_user)
        db.commit()