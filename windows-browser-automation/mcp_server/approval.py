"""MCP için policygate onay kanalı köprüsü."""
from __future__ import annotations

from collections.abc import Callable

from policygate import ActionRequest
from policygate.log import get as _get_logger

_log = _get_logger("mcp_approval")
ApprovalCallback = Callable[[ActionRequest], bool]


def _deny(_: ActionRequest) -> bool:
    return False


class MCPApprovalChannel:
    """MCP istemcisine onay soran katıştırılabilir kanal.

    Callback `True` dönerse onay, diğer her değer ve hata red sayılır.
    Callback verilmezse güvenli varsayılan RED'dir; böylece standalone
    sunucuda onaysuz SEND/DELETE işlemi sızamaz.
    """

    def __init__(self, ask_user: ApprovalCallback | None = None) -> None:
        self._ask_user = ask_user or _deny

    def ask(self, req: ActionRequest) -> bool:
        try:
            return self._ask_user(req) is True
        except Exception as exc:
            _log.warning("MCP onayı alınamadı (%s) — red sayılıyor", exc)
            return False

