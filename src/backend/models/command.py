import re
from typing import Any
from dataclasses import dataclass
from pydantic import BaseModel


class Command(BaseModel):
    full: str
    cmd: str
    args: list[str] = []

cmd_keep_spacing = ['@', '#']

def build_command(msg: Any) -> Command:
    cmd = msg.split()[0]
    if cmd in cmd_keep_spacing:
        _, *args = re.split(r"(\s+)", msg)
        if args:
            args = args[1:]
    else:
        _, *args = msg.split()

    return Command.model_validate(
        {
            "full": msg,
            "cmd": cmd.strip(),
            "args": args,
        }
    )


@dataclass
class CommandResult:
    text_response: str | None = None
    working_dir: str | None = None
