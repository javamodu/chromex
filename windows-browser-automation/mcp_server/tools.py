"""CLI komutlarından MCP tool tanımları üretir.

CLI çekirdeği tek kaynak olarak kalır; bu modül yalnızca komut kayıt
tablosunu şemaya çevirir ve çağrıyı `orchestrator.cli.main()`'e yönlendirir.
"""
from __future__ import annotations

import contextlib
import io
from dataclasses import dataclass
from typing import Any

from orchestrator import cli


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: dict[str, Any]
    command_args: tuple[tuple[str, dict[str, Any]], ...]


def _destination(arg_name: str) -> str:
    return arg_name.lstrip("-").replace("-", "_")


def _property_schema(kwargs: dict[str, Any]) -> dict[str, Any]:
    if kwargs.get("action") == "store_true":
        schema = {"type": "boolean"}
    elif kwargs.get("type") is int:
        schema = {"type": "integer"}
    else:
        schema = {"type": "string"}
    schema["description"] = str(kwargs.get("help", ""))
    choices = kwargs.get("choices")
    if choices:
        schema["enum"] = list(choices)
    return schema


def _spec_from_command(command: Any) -> ToolSpec:
    properties: dict[str, Any] = {}
    required: list[str] = []
    for arg_name, kwargs in command.args:
        destination = _destination(arg_name)
        properties[destination] = _property_schema(kwargs)
        if not arg_name.startswith("--") or kwargs.get("required"):
            required.append(destination)
    return ToolSpec(
        name=command.name,
        description=command.help,
        input_schema={
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
        },
        command_args=command.args,
    )


TOOLS: tuple[ToolSpec, ...] = tuple(
    _spec_from_command(command) for command in cli._COMMANDS
)


def tool_by_name(name: str) -> ToolSpec | None:
    return next((tool for tool in TOOLS if tool.name == name), None)


def to_cli_args(spec: ToolSpec, arguments: dict[str, Any]) -> list[str]:
    valid = {_destination(arg_name) for arg_name, _ in spec.command_args}
    unknown = set(arguments) - valid
    if unknown:
        raise ValueError(f"bilinmeyen argüman: {', '.join(sorted(unknown))}")
    argv: list[str] = []
    for arg_name, kwargs in spec.command_args:
        destination = _destination(arg_name)
        default = kwargs.get("default")
        value = arguments.get(destination, default)
        if arg_name.startswith("--"):
            if kwargs.get("action") == "store_true":
                if value is True:
                    argv.append(arg_name)
                elif value not in (False, None):
                    raise ValueError(f"{destination} boolean olmalı")
                continue
            if value is None:
                continue
            argv.extend((arg_name, str(value)))
        else:
            if value is None:
                raise ValueError(f"{destination} zorunlu")
            argv.append(str(value))
    return argv


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    spec = tool_by_name(name)
    if spec is None:
        return {"stdout": "", "stderr": f"bilinmeyen tool: {name}", "exitCode": 2}
    stdout = io.StringIO()
    stderr = io.StringIO()
    try:
        argv = [spec.name, *to_cli_args(spec, arguments)]
    except ValueError as exc:
        return {"stdout": "", "stderr": str(exc), "exitCode": 2}
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exit_code = cli.main(argv)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)
    except Exception as exc:
        return {"stdout": stdout.getvalue(), "stderr": str(exc), "exitCode": 1}
    return {
        "stdout": stdout.getvalue(),
        "stderr": stderr.getvalue(),
        "exitCode": exit_code,
    }
