"""Chromex MCP sunucusu (opsiyonel `mcp` extra'sı ile)."""
from __future__ import annotations

import inspect
from typing import Any

from policygate import approval

from .approval import MCPApprovalChannel
from .tools import TOOLS, ToolSpec, execute_tool


def _annotation(kwargs: dict[str, Any]) -> type:
    if kwargs.get("action") == "store_true":
        return bool
    if kwargs.get("type") is int:
        return int
    return str


def _tool_function(spec: ToolSpec):
    parameters = [
        inspect.Parameter(
            name=arg_name.lstrip("-").replace("-", "_"),
            kind=inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=kwargs.get("default", inspect.Parameter.empty),
            annotation=_annotation(kwargs),
        )
        for arg_name, kwargs in spec.command_args
    ]

    def wrapper(**kwargs: Any) -> dict[str, Any]:
        return execute_tool(spec.name, kwargs)

    wrapper.__name__ = spec.name
    wrapper.__qualname__ = spec.name
    wrapper.__doc__ = spec.description
    wrapper.__signature__ = inspect.Signature(parameters)
    wrapper.__annotations__["return"] = dict[str, Any]
    return wrapper


def register_tools(server: Any) -> None:
    for spec in TOOLS:
        server.tool(name=spec.name, description=spec.description)(
            _tool_function(spec)
        )


def create_server(approval_callback=None) -> Any:
    try:
        from mcp.server import MCPServer
    except ImportError as exc:
        raise RuntimeError(
            "MCP sunucusu için `pip install chromex-otomasyon[mcp]` gerekir"
        ) from exc
    server = MCPServer("chromex-otomasyon")
    register_tools(server)
    approval.set_channel(
        MCPApprovalChannel(approval_callback),
        allow_non_interactive=True,
    )
    return server


def main() -> int:
    create_server().run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
