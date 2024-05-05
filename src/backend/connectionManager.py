from sys import stderr
from fastapi import HTTPException, WebSocket

from .user import User
from .templating import render_template
from .login import login_manager


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, User] = {}

    async def verify_token(self, websocket: WebSocket, token: str) -> User | None:
        await websocket.accept()
        try:
            user_obj: User = await login_manager.get_current_user(token)
            user = str(user_obj.username)
            return await self.connect(websocket, user)
        except HTTPException:
            motd = {"chat": "ERROR: InvalidCreds"}
            await self.send_template(websocket, "chat.html", motd)
            await self.send_template(websocket, "login.html", {})
            await websocket.close()
            return None

    async def connect(self, websocket: WebSocket, user: str):
        new_user = User(ws=websocket, username=user)
        self.active_connections[websocket] = new_user
        return new_user

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except RuntimeError:
            print("Error sending msg", file=stderr)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def set_username(self, websocket: WebSocket, new_name: str):
        self.active_connections[websocket].username = new_name

    async def send_template(
        self, websocket: WebSocket, template_name: str, context: dict
    ):
        resp = render_template(template_name, context)
        await self.send_personal_message(resp, websocket)

    async def broadcast_template(self, template_name: str, context: dict):
        resp = render_template(template_name, context)
        await self.broadcast(resp)

    async def send_template_portal(self, template_name: str, portal_name: str, context):
        for ws, user in self.active_connections.items():
            if user.portal == portal_name:
                await self.send_template(ws, template_name, context)

    async def refresh_users(self):
        all_users = self.active_connections.values()
        for ws, user in self.active_connections.items():
            portal_users = [u.username for u in all_users if u.portal == user.portal]
            context = {"users": portal_users, "current": self.get_user(ws).username}
            await self.send_template(ws, "users.html", context)

    def get_user(self, websocket: WebSocket) -> User:
        return self.active_connections[websocket]

    def get_ws(self, username: str) -> WebSocket | None:
        for user in self.active_connections.values():
            if user.username == username:
                return user.ws
        return None

    def get_portals(self) -> dict[str, int]:
        portals: dict[str, int] = {}
        for user in self.active_connections.values():
            if user.portal:
                portals[user.portal] = 1 + portals.get(user.portal, 0)
        return portals
