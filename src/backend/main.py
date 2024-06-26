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
from .models.portal import get_portals
from .models.command import Command, build_command
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
    if not user or not websocket.client:
        return

    client_id = websocket.client.host
    await manager.refresh_users()
    try:
        motd = {"chat": f"Vous êtes connectés avec le user : {user.username}"}
        await manager.send_template(websocket, "chat.html", motd)
        await manager.send_template(
            websocket, "cmd.html", {"working_dir": user.working_dir}
        )
        portals = get_portals()
        portals_count = Commands.manager.get_portals()
        context = {"portals": portals, "count": portals_count}
        await Commands.manager.send_template(websocket, "portals.html", context)
        while True:
            data = await websocket.receive_json()
            if not (msg := data.get("cmd", "")):
                continue
            command = build_command(msg)
            await handle_command(websocket, command)
    except WebSocketDisconnect:
        print(f"Disconnect: {client_id}")
        manager.disconnect(websocket)
        await manager.refresh_users()
    except RuntimeError:
        pass


async def handle_command(websocket: WebSocket, command: Command) -> None:
    old_working_path = manager.get_user(websocket).working_dir
    await manager.send_template(
        websocket,
        "cmd_log.html",
        {"cmd": command.full, "old_working_dir": old_working_path},
    )

    if not command.cmd:
        return

    response = await commands.handle_cmd(websocket, command)
    if not response:
        return

    working_dir = response.working_dir or old_working_path
    context = {
        "response": response.text_response,
        "working_dir": working_dir,
    }
    await manager.send_template(websocket, "cmd.html", context)


def chat_response(request: Request, msg: str):
    context = {"request": request, "chat": msg}
    return templates.TemplateResponse("chat.html", context)
