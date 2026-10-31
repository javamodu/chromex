"""Gerçek MCP istemcisi ile stdio tabanlı smoke testi."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any


EXPECTED_TOOL_COUNT = 28


async def _run_smoke(
    client_session: type,
    server_parameters: type,
    stdio_client: Any,
) -> int:
    package_root = Path(__file__).resolve().parents[1]
    environment = os.environ.copy()
    python_path = [
        str(package_root),
        environment.get("PYTHONPATH", ""),
    ]
    environment["PYTHONPATH"] = os.pathsep.join(path for path in python_path if path)
    parameters = server_parameters(
        command=sys.executable,
        args=["-m", "mcp_server.server"],
        cwd=package_root,
        env=environment,
    )
    async with stdio_client(parameters) as streams:
        async with client_session(*streams) as session:
            await session.initialize()
            result = await session.list_tools()
            count = len(result.tools)
            if count != EXPECTED_TOOL_COUNT:
                print(f"MCP_SMOKE_ERROR tools={count} expected={EXPECTED_TOOL_COUNT}")
                return 1
            print(f"MCP_SMOKE_OK tools={count}")
            return 0


def main() -> int:
    try:
        from mcp import ClientSession, StdioServerParameters, stdio_client
    except ImportError as exc:
        print(f"MCP_SMOKE_ERROR missing_dependency mcp ({exc})")
        print("Kurulum: python -m pip install -e .[mcp]")
        return 2
    try:
        return asyncio.run(
            _run_smoke(ClientSession, StdioServerParameters, stdio_client)
        )
    except Exception as exc:
        print(f"MCP_SMOKE_ERROR {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
