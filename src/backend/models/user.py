import bcrypt
from sqlalchemy import Column, Integer, String, insert
from .db import Base, SessionLocal
from ..main import login_manager


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)


# TODO: Au lieu de renvoyer un objet Schéma de la base, il faudrait passer par un Objet Pydantic


@login_manager.user_loader()
def get_user(username: str):
    return SessionLocal().query(User).where(User.username == username).first()


def user_valid(username: str, password: str):
    user = get_user(username)
    if not user:
        return False

    hashed_password = str(user.password).encode()
    return bcrypt.checkpw(password.encode(), hashed_password)


def user_exists(username: str):
    return get_user(username) is not None


def create_user(username: str, password: str):
    salt = bcrypt.gensalt()
    hash = bcrypt.hashpw(password.encode(), salt).decode()

    s = SessionLocal()
    s.execute(insert(User), [{"username": username, "password": hash}])
    s.commit()
