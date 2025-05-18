from sqlmodel import Session, SQLModel

def add_new_column(session: Session, stmt: str) -> str:
    try:
        # session.exec("ALTER TABLE users ADD COLUMN age INTEGER;")
        session.exec(stmt)
        session.commit()
        return 'update succeed'
    except:
        return 'update failed'
    