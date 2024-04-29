import re
from typing import Any
from dataclasses import dataclass
from pydantic import BaseModel


class Command(BaseModel):
    full: str
    cmd: str
    args: list[str] = []


def build_command(data: Any) -> Command:
    msg = data.get("cmd", "")
    cmd, *args = re.split(r"(\s+)", msg)
    if args:
        args = args[1:]

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
