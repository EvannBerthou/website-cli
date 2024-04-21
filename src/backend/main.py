from typing import Annotated
from fastapi import (
    FastAPI,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Form,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .deps import SessionDep

from .commands import Commands
from .models.user import user_exists, create_user, user_valid
from .connectionManager import ConnectionManager
from .login import login_manager

app = FastAPI()

templates = Jinja2Templates(directory="src/backend/templates")
app.mount(
    "/static", StaticFiles(directory="src/backend/templates/static"), name="static"
)

manager = ConnectionManager()
commands = Commands(manager)


@app.get("/")
async def index(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("index.html", context)


@app.get("/motd")
async def motd(request: Request):
    context = {"request": request}
    return templates.TemplateResponse("motd.html", context)


@app.post("/login")
async def login(request: Request, cmd: Annotated[str, Form()], db: SessionDep):
    match cmd.split():
        case ["login", username, password]:
            if not user_valid(db, username, password):
                return chat_response(request, "Utilisateur ou mot de passe invalide")
        case ["register", username, password, confirm]:
            if password != confirm:
                return chat_response(request, "Mots de passes différents")
            if user_exists(db, username):
                return chat_response(request, "L'utilisateur existe déjà")
            create_user(db, username, password)
        case _:
            return chat_response(request, "Commande invalide")

    token = login_manager.create_access_token(data={"sub": username})
    context = {"request": request, "token": token}
    resp = templates.TemplateResponse("cli.html", context)
    login_manager.set_cookie(resp, token)
    return resp


@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = await manager.verify_token(websocket, token)
    assert websocket.client is not None
    client_id = websocket.client.host
    await manager.refresh_users()
    try:
        motd = {"chat": f"Vous êtes connectés avec le user : {user}"}
        await manager.send_template(websocket, "chat.html", motd)
        while True:
            data = await websocket.receive_json()
            msg: str = data.get("cmd", "").strip()
            match msg[0]:
                case "@":
                    await handle_global_msg(websocket, msg)
                case "#":
                    await handle_portal_msg(websocket, msg)
                case _:
                    await handle_command(websocket, msg)
    except WebSocketDisconnect:
        print(f"Disconnect: {client_id}")
        manager.disconnect(websocket)
        await manager.refresh_users()
    except RuntimeError:
        pass


async def handle_global_msg(websocket: WebSocket, msg: str) -> None:
    msg = msg[1:]
    user = manager.get_user(websocket).username
    context = {"user": user, "chat": msg, "prefix": "@"}
    await manager.broadcast_template("chat.html", context)


async def handle_portal_msg(websocket: WebSocket, msg: str) -> None:
    user = manager.get_user(websocket)
    msg = msg[1:]
    if not user.portal:
        ctx = {"chat": "Vous n'êtes dans aucun portail."}
        await manager.send_template(websocket, "chat.html", ctx)
    else:
        context = {
            "user": user.username,
            "chat": msg,
            "prefix": "#",
            "suffix": f"({user.portal})",
        }
        await manager.send_template_portal("chat.html", user.portal, context)


async def handle_command(websocket: WebSocket, cmd: str) -> None:
    response = await commands.handle_cmd(websocket, cmd) or ""
    context = {"cmd": cmd, "response": response}
    await manager.send_template(websocket, "cmd.html", context)


def chat_response(request: Request, msg: str):
    context = {"request": request, "chat": msg}
    return templates.TemplateResponse("chat.html", context)
