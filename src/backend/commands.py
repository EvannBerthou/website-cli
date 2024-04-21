import inspect
from typing import Optional, Callable

from fastapi import WebSocket
from pydantic import ValidationError, validate_call, ConfigDict

from .connectionManager import ConnectionManager

pydantic_config = ConfigDict(arbitrary_types_allowed=True)


class Commands:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager

    async def handle_cmd(self, websocket: WebSocket, cmd: str) -> Optional[str]:
        if not cmd:
            return None

        cmd_name, *args = cmd.split()
        params = []
        try:
            cmd_fct: Callable = getattr(self, f"cmd_{cmd_name}")
            params = await self.get_non_optional_params(cmd_fct)
            if len(params) > len(args):
                return await self.get_usage(cmd_name, params)
            return await cmd_fct(websocket, *args)
        except AttributeError:
            return f"Unknown command : {cmd_name}"
        except ValidationError:
            return await self.get_usage(cmd_name, params)

    async def get_non_optional_params(self, cmd_fct: Callable):
        params = await self.get_method_params(cmd_fct)
        return [param for param in params if param.default == inspect.Parameter.empty]

    """
    Commands
    """

    async def get_method_params(self, cmd_fct: Callable):
        sig = inspect.signature(cmd_fct)
        return list(sig.parameters.copy().values())[1:]

    async def get_usage(self, cmd_name: str, params: list[inspect.Parameter]):
        args_usage = " ".join([f"<{arg}>" for arg in params])
        return f"Usage: {cmd_name} {args_usage}"

    @validate_call(config=pydantic_config)
    async def cmd_username(self, websocket: WebSocket, new_name: str):
        await self.manager.set_username(websocket, new_name)
        await self.manager.refresh_users()
        return f"Username changed to {new_name}"

    @validate_call(config=pydantic_config)
    async def cmd_help(self, _: WebSocket, cmd_name: Optional[str] = None):
        if not cmd_name:
            all_fct = inspect.getmembers(Commands, predicate=inspect.isfunction)
            fct_names = ", ".join(x[0][4:] for x in all_fct if x[0].startswith("cmd_"))
            return f"Type `help <command name>` for more details.\n{fct_names}"

        try:
            cmd_fct = getattr(self, f"cmd_{cmd_name}")
        except AttributeError:
            return f"Unknown command : {cmd_name}"
        params = await self.get_method_params(cmd_fct)
        return await self.get_usage(cmd_name, params)

    @validate_call(config=pydantic_config)
    async def cmd_clear(self, _: WebSocket):
        return None

    @validate_call(config=pydantic_config)
    async def cmd_portal(self, websocket: WebSocket, portal_name: str):
        self.manager.active_connections[websocket].portal = portal_name
        context = {"portals": [], "current": portal_name}
        await self.manager.send_template(websocket, "portals.html", context)
        await self.manager.refresh_users()
        return f"Portal changed to {portal_name}"
