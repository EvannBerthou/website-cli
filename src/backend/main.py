import random
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .connectionManager import ConnectionManager
from .commands import Commands

app = FastAPI()

templates = Jinja2Templates(directory='src/backend/templates')
app.mount(
    "/static", StaticFiles(directory="src/backend/templates/static"),
    name="static")

manager = ConnectionManager()
commands = Commands(manager)


@app.get('/')
async def index(request: Request):
    context = {'request': request, 'user_id': random.randint(1, 1000)}
    return templates.TemplateResponse('index.html', context)


@app.websocket('/ws/{user_id}')
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    client_id = websocket.client.host
    await manager.refresh_users()
    try:
        while True:
            data = await websocket.receive_json()
            cmd: str = data.get('cmd', '').strip()
            if cmd.startswith('@'):
                user = manager.get_user(websocket).username
                context = {'user': user, 'chat': cmd, 'prefix': '@'}
                await manager.broadcast_template('chat.html', context)
            elif cmd.startswith('#'):
                user = manager.get_user(websocket)
                context = {'user': user.username, 'chat': cmd, 'prefix': '#'}
                await manager.send_template_portal('chat.html',
                                                   user.portal, context)
            else:
                response = await commands.handle_cmd(websocket, cmd) or ''
                context = {'cmd': cmd, 'response': response}
                await manager.send_template(websocket, 'cmd.html', context)
    except WebSocketDisconnect:
        print(f'Disconnect: {client_id}')
        manager.disconnect(websocket)
        await manager.refresh_users()
