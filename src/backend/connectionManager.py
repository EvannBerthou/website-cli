from fastapi import WebSocket

from .user import User
from .templating import render_template


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[WebSocket, User] = {}

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept()
        self.active_connections[websocket] = User(ws=websocket, username=user)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.pop(websocket, None)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

    async def set_username(self, websocket: WebSocket, new_name: str):
        self.active_connections[websocket].username = new_name

    async def send_template(self, websocket: WebSocket,
                            template_name: str, context: dict):
        resp = render_template(template_name, context)
        await self.send_personal_message(resp, websocket)

    async def broadcast_template(self, template_name: str, context: dict):
        resp = render_template(template_name, context)
        await self.broadcast(resp)

    async def send_template_portal(self, template_name: str,
                                   portal_name: str, context):
        for ws, user in self.active_connections.items():
            if user.portal == portal_name:
                await self.send_template(ws, template_name, context)

    async def refresh_users(self):
        all_users = self.active_connections.values()
        for ws, user in self.active_connections.items():
            portal_users = [
                u.username for u in all_users if u.portal == user.portal]
            context = {'users': portal_users,
                       'current': self.get_user(ws).username}
            await self.send_template(ws, 'users.html', context)

    def get_user(self, websocket: WebSocket) -> User:
        return self.active_connections[websocket]
