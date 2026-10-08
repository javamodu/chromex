"""Onay kapısı.

Dış etki yaratan her işlem (SEND/MODIFY/DELETE) buradan geçer:
1) policy'ye bakılır (auto/ask/deny),
2) "ask" ise işlemin TAM detayı (alıcı, konu, komut...) kullanıcıya gösterilir,
3) yalnızca birebir 'EVET' yanıtı onay sayılır,
4) her karar audit zincirine yazılır,
5) etkileşimsiz (pipe/cron) oturumda varsayılan karar RED'dir; SEND ve
   DELETE seviyesi non_interactive_default ne olursa olsun HER ZAMAN reddedilir.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from . import audit, policy


class ApprovalDenied(Exception):
    """İşlem policy veya kullanıcı tarafından reddedildi."""


@dataclass
class ActionRequest:
    worker: str            # ör. "gmail"
    action: str            # ör. "gmail.send_draft"
    level: str             # READ / DRAFT / SEND / MODIFY / DELETE
    summary: str           # kullanıcıya gösterilecek tek satır özet
    details: dict[str, Any] = field(default_factory=dict)


def _show(req: ActionRequest) -> None:
    print("\n" + "=" * 62)
    print(f"ONAY GEREKİYOR  [{req.level.upper()}]  {req.action}")
    print("-" * 62)
    print(req.summary)
    for key, value in req.details.items():
        text = str(value)
        if len(text) > 600:
            text = text[:600] + f"... (+{len(text) - 600} karakter)"
        print(f"  {key}: {text}")
    print("-" * 62)


def _ask_user(req: ActionRequest) -> bool:
    _show(req)
    answer = input("Bu işlemi onaylıyor musunuz? Yalnızca 'EVET' kabul edilir: ")
    return answer.strip() == "EVET"


def require(req: ActionRequest) -> None:
    """Onay alınamazsa ApprovalDenied fırlatır; alınırsa sessizce döner."""
    pol = policy.load()
    mode = policy.decision_for(req.level, req.action, pol)

    if mode == "deny":
        audit.log_event("action_denied_by_policy", req.worker, req.level, "deny",
                        {"action": req.action, **req.details})
        raise ApprovalDenied(f"Policy bu işlemi yasaklıyor: {req.action}")

    if mode == "auto":
        audit.log_event("action_auto_approved", req.worker, req.level, "auto",
                        {"action": req.action, "summary": req.summary})
        return

    # mode == "ask"
    if not sys.stdin.isatty():
        if req.level.upper() in {"SEND", "DELETE"}:
            # Kritik seviyeler etkileşimsiz oturumda asla otomatik onaylanmaz;
            # non_interactive_default="auto" bile bunu geçemez.
            audit.log_event("action_non_interactive", req.worker, req.level,
                            "deny", {"action": req.action,
                                     "neden": "kritik_seviye_etkilesimsiz"})
            raise ApprovalDenied(
                f"Etkileşimsiz oturumda {req.level} seviyesi her zaman "
                f"reddedilir: {req.action}"
            )
        default = str(pol.get("non_interactive_default", "deny")).lower()
        audit.log_event("action_non_interactive", req.worker, req.level, default,
                        {"action": req.action})
        if default != "auto":
            raise ApprovalDenied(
                "Etkileşimsiz oturumda onay istenemez; işlem reddedildi "
                "(policy: non_interactive_default)."
            )
        return

    if _ask_user(req):
        audit.log_event("action_user_approved", req.worker, req.level, "approved",
                        {"action": req.action, **req.details})
        return

    audit.log_event("action_user_rejected", req.worker, req.level, "rejected",
                    {"action": req.action})
    raise ApprovalDenied(f"Kullanıcı onay vermedi: {req.action}")
