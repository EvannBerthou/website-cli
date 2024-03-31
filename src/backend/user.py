from fastapi import WebSocket
from pydantic import BaseModel

pydantic_config = dict(arbitrary_types_allowed=True)


class User(BaseModel):
    ws: WebSocket
    username: str
    portal: str | None = None

    class Config:
        arbitrary_types_allowed = True
