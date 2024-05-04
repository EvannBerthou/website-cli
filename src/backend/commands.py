import os
from argparse import Namespace, ArgumentError, ArgumentParser, HelpFormatter
from typing import Optional, Callable
from dataclasses import dataclass

from fastapi import WebSocket

from .connectionManager import ConnectionManager
from .models.command import CommandResult, Command


class SmartFormatter(HelpFormatter):
    def format_help(self):
        help = self._root_section.format_help()
        help = "\n".join([s for s in help.split("\n") if s])
        if help:
            help = self._long_break_matcher.sub("\n\n", help)
            help = help.strip("\n") + "\n"
        return help


@dataclass
class ServerCommand:
    name: str
    description: str
    help: str
    execute: Callable


def arg(n, **kwargs):
    return n, kwargs


commands: dict[str, ServerCommand] = {}


def command(*, name, description, help, params=None):
    def decorator(function):
        parser = ArgumentParser(
            prog=name,
            description=description,
            formatter_class=SmartFormatter,
            exit_on_error=False,
        )
        if params:
            for param_name, d in params:
                parser.add_argument(param_name, **d)

        async def wrapper(ws, args):
            parsed_args = parser.parse_args(args)
            return await function(ws, parsed_args)

        commands[name] = ServerCommand(name, description, help, wrapper)
        return wrapper

    return decorator


class Commands:
    manager: ConnectionManager

    def __init__(self, manager: ConnectionManager):
        Commands.manager = manager

    async def handle_cmd(
        self, websocket: WebSocket, command: Command
    ) -> Optional[CommandResult]:
        if c := commands.get(command.cmd):
            try:
                return await c.execute(websocket, command.args)
            # NOTE: except SystemExit because of a bug in argparse.
            # Even with exit_on_error=False, if there is no args passed
            # the lib throws a SystemExit which exits the program if not handled
            except (ArgumentError, SystemExit):
                return CommandResult(c.help)
        else:
            return CommandResult(f"Unknown command : {command.cmd}")


@command(
    name="help",
    description="Gets command help page",
    params=[
        arg(
            "command",
            type=str,
            nargs="?",
        )
    ],
    help="help <command?>",
)
async def help(_: WebSocket, args: Namespace) -> CommandResult:
    if cmd := args.command:
        if c := commands.get(cmd, None):
            return CommandResult(c.help)
        else:
            return CommandResult(f"Unknown command : {cmd}")

    fct_names = ", ".join(commands.keys())
    return CommandResult(f"Type `help <command name>` for more details.\n{fct_names}")


@command(name="clear", description="Clears terminal", help="clear")
async def clear(*_) -> None:
    return None


@command(
    name="cd",
    description="Changes current working directory",
    params=[arg("directory", type=str, nargs=1)],
    help="cd <target_dir>",
)
async def cd(ws: WebSocket, args: Namespace) -> CommandResult:
    user = Commands.manager.get_user(ws)
    user_path = user.working_dir
    target_dir = args.directory[0]
    new_dir = os.path.normpath(os.path.join(user_path, target_dir))
    user.working_dir = new_dir
    return CommandResult(working_dir=new_dir)


@command(
    name="portal",
    description="Changes current portal",
    params=[arg("portal", type=str, nargs=1)],
    help="portal <portal>",
)
async def portal(websocket: WebSocket, args: Namespace) -> CommandResult:
    portal_name = args.portal[0]
    Commands.manager.active_connections[websocket].portal = portal_name
    portals = Commands.manager.get_portals()
    context = {"portals": portals, "current": portal_name}
    await Commands.manager.send_template(websocket, "portals.html", context)
    await Commands.manager.refresh_users()
    return CommandResult(f"Portal changed to {portal_name}")


@command(
    name="msg",
    description="Changes current portal",
    params=[arg("target", type=str, nargs=1), arg("message", type=str, nargs="+")],
    help="msg <target> <message>",
)
async def msg(ws: WebSocket, args: Namespace) -> CommandResult:
    msg = "".join(args.message)
    target_name = args.target[0]
    target_ws = Commands.manager.get_ws(target_name)
    sender = Commands.manager.get_user(ws).username
    if sender == target_name:
        return CommandResult("Cannot send message to yourself")
    if not target_ws:
        return CommandResult(f"User {target_name} not found")
    await Commands.manager.send_template(
        target_ws, "chat.html", {"prefix": "<- ", "user": sender, "chat": msg}
    )
    return CommandResult(f"-> {target_name} : {msg}")


@command(
    name="@",
    description="Sends a global message",
    params=[arg("message", type=str, nargs="+")],
    help="@ <message>",
)
async def handle_global_msg(websocket: WebSocket, args: Namespace) -> None:
    msg = "".join(args.message)
    user = Commands.manager.get_user(websocket).username
    context = {"user": user, "chat": msg, "prefix": "@"}
    await Commands.manager.broadcast_template("chat.html", context)


@command(
    name="#",
    description="Sends a message to the portal",
    params=[arg("message", type=str, nargs="+")],
    help="# <message>",
)
async def handle_portal_msg(websocket: WebSocket, args: Namespace) -> None:
    user = Commands.manager.get_user(websocket)
    msg = "".join(args.message)
    if not user.portal:
        ctx = {"chat": "Vous n'êtes dans aucun portail."}
        await Commands.manager.send_template(websocket, "chat.html", ctx)
    else:
        context = {
            "user": user.username,
            "chat": msg,
            "prefix": "#",
            "suffix": f"({user.portal})",
        }
        await Commands.manager.send_template_portal("chat.html", user.portal, context)
