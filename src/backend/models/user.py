import bcrypt
from sqlmodel import Field, SQLModel, select, Session

from .db import engine
from ..login import login_manager


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password: str = Field(nullable=False)


@login_manager.user_loader()
def get_user(username: str) -> User | None:
    with Session(engine) as session:
        return get_user_by_username(session, username)


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return db.exec(stmt).first()


def user_valid(db: Session, username: str, password: str) -> bool:
    user = get_user_by_username(db, username)
    if not user:
        return False

    hashed_password = str(user.password).encode()
    return bcrypt.checkpw(password.encode(), hashed_password)


def user_exists(db: Session, username: str) -> bool:
    return get_user_by_username(db, username) is not None


def create_user(db: Session, username: str, password: str) -> None:
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(password.encode(), salt).decode()
    user = User.model_validate({"username": username, "password": hash})
    db.add(user)
    db.commit()
