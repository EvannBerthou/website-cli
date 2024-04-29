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


def build_command(data: Any) -> Command:
    msg = data.get("cmd", "")
    cmd, *args = re.split(r"(\s+)", msg)
    if args:
        args = args[1:]

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
        }
    )


@dataclass
class CommandResult:
    text_response: str | None = None
    working_dir: str | None = None
