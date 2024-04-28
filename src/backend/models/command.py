import re
from typing import Any
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel


class MsgType(Enum):
    Global = 1
    Portal = 2
    Command = 3


class Command(BaseModel):
    full: str
    cmd: str
    args: list[str] = []
    msg_type: MsgType
    working_dir: str


command_needing_working_dir = ["cd"]
command_keep_args_spacing = ["msg"]


def build_command(data: Any) -> Command:
    msg = data.get("cmd", "")
    working_dir = data.get("working-dir", "")
    cmd, *args = msg.split()

    if cmd in command_needing_working_dir:
        args.append(working_dir)

    if cmd in command_keep_args_spacing:
        args = re.split(r'(\s+)', msg)[2:]

    match cmd[0]:
        case "@":
            msg_type = MsgType.Global
        case "#":
            msg_type = MsgType.Portal
        case _:
            msg_type = MsgType.Command

    return Command.model_validate(
        {
            "full": msg,
            "cmd": cmd,
            "args": args,
            "msg_type": msg_type,
            "working_dir": working_dir,
        }
    )


@dataclass
class CommandResult:
    text_response: str | None = None
    working_dir: str | None = None
