from sqlalchemy.exc import IntegrityError
from .db import engine
from sqlmodel import Field, SQLModel, select, Session


class Portal(SQLModel, table=True):
    __tablename__ = "portals"  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    creator: int = Field(foreign_key="users.id")


def get_portals() -> list[str]:
    with Session(engine) as db:
        return list(db.exec(select(Portal.name)).all())


def create_portal(portal_name: str, creator: int) -> bool:
    portal = Portal(name=portal_name, creator=creator)
    try:
        with Session(engine) as db:
            db.add(portal)
            db.commit()
    except IntegrityError:
        return False
    return True
