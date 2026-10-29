"""Üretim öncesi tek komut: policy, audit, CLI ve MCP kayıt doğrulaması."""
from __future__ import annotations

from policygate import __version__, audit, policy

BEKLENEN_SURUM = "1.1.0"
BEKLENEN_KOMUT = 21
BEKLENEN_TOOL = 21


def check_policy() -> str:
    pol = policy.load()
    if policy.decision_for("DELETE", "test", pol) == "auto":
        raise RuntimeError("DELETE otomatik onaya açılamaz")
    if policy.decision_for("SEND", "test", pol) != "ask":
        raise RuntimeError("SEND onay zorunlu olmalı")
    if policy.decision_for("MODIFY", "test", pol) != "ask":
        raise RuntimeError("MODIFY onay zorunlu olmalı")
    return "policy: DELETE/SEND/MODIFY onay kapalı"


def check_audit() -> str:
    ok, message = audit.verify_chain()
    if not ok:
        raise RuntimeError(message)
    return f"audit: {message}"


def check_registry() -> str:
    from orchestrator.cli import get_commands
    from mcp_server.tools import get_tool_registry

    commands = get_commands()
    tools = get_tool_registry()
    if len(commands) != BEKLENEN_KOMUT:
        raise RuntimeError(f"CLI komut sayısı {len(commands)}, beklenen {BEKLENEN_KOMUT}")
    if len(tools) != BEKLENEN_TOOL:
        raise RuntimeError(f"MCP tool sayısı {len(tools)}, beklenen {BEKLENEN_TOOL}")
    if [command.name for command in commands] != [tool.name for tool in tools]:
        raise RuntimeError("CLI ve MCP kayıt adları farklı")
    return f"registry: {len(commands)} komut = {len(tools)} tool"


def check_version() -> str:
    if __version__ != BEKLENEN_SURUM:
        raise RuntimeError(f"policygate sürümü {__version__}, beklenen {BEKLENEN_SURUM}")
    return f"version: policygate {__version__}"


def main() -> int:
    checks = (check_version, check_policy, check_audit, check_registry)
    try:
        for check in checks:
            print(check())
    except Exception as exc:
        print(f"PRODUCTION_CHECK_ERROR {type(exc).__name__}: {exc}")
        return 1
    print("PRODUCTION_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
