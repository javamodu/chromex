"""Onay kapısı.

Dış etki yaratan her işlem (SEND/MODIFY/DELETE) buradan geçer:
1) policy'ye bakılır (auto/ask/deny),
2) "ask" ise işlemin TAM detayı (alıcı, konu, komut...) aktif onay kanalına
   gösterilir — varsayılan terminal; set_channel() ile webhook/bot köprüsü
   takılabilir,
3) yalnızca birebir 'EVET' yanıtı (veya kanaldan True) onay sayılır,
4) her karar audit zincirine yazılır,
5) etkileşimsiz (pipe/cron) oturumda varsayılan karar RED'dir; SEND ve
   DELETE seviyesi non_interactive_default ne olursa olsun HER ZAMAN
   reddedilir (özel kanal allow_non_interactive=True ile kurulmadıkça).
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from . import audit, policy
from .log import get as _get_logger

_log = _get_logger("approval")


def _console_safe(text: str) -> str:
    """cp1252 gibi sınırlı kod sayfalı konsollarda patlamamak için metni
    gerektiğinde ASCII'ye katlar (UTF-8 konsolda metne dokunulmaz)."""
    try:
        text.encode(sys.stdout.encoding or "utf-8")
        return text
    except (UnicodeEncodeError, UnicodeDecodeError, AttributeError):
        return text.encode("ascii", "replace").decode()


class ApprovalDenied(Exception):
    """İşlem policy veya kullanıcı tarafından reddedildi."""


@dataclass
class ActionRequest:
    worker: str            # ör. "gmail"
    action: str            # ör. "gmail.send_draft"
    level: str             # READ / DRAFT / SEND / MODIFY / DELETE
    summary: str           # kullanıcıya gösterilecek tek satır özet
    details: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ApprovalChannel(Protocol):
    """Onay kanalı arayüzü: isteği sunar, True (onay) / False (red) döner."""

    def ask(self, req: ActionRequest) -> bool: ...


def _show(req: ActionRequest) -> None:
    print(_console_safe("\n" + "=" * 62))
    print(_console_safe(f"ONAY GEREKİYOR  [{req.level.upper()}]  {req.action}"))
    print(_console_safe("-" * 62))
    print(_console_safe(req.summary))
    for key, value in req.details.items():
        text = str(value)
        if len(text) > 600:
            text = text[:600] + f"... (+{len(text) - 600} karakter)"
        print(_console_safe(f"  {key}: {text}"))
    print(_console_safe("-" * 62))


class TerminalChannel:
    """Varsayılan kanal: terminalde detay gösterir, birebir 'EVET' ister."""

    def ask(self, req: ActionRequest) -> bool:
        _show(req)
        answer = input(_console_safe(
            "Bu işlemi onaylıyor musunuz? Yalnızca 'EVET' kabul edilir: "))
        return answer.strip() == "EVET"


class WebhookChannel:
    """Onayı bir HTTP uç noktasına sorar (ör. Slack/mobil onay köprüsü).

    POST body'si: {"worker", "action", "level", "summary", "details"}
    Beklenen yanıt: JSON {"approve": true} — başka her şey red sayılır
    (ağ/parse hatası dahil; fail-closed).
    """

    def __init__(self, url: str, timeout: int = 120) -> None:
        self.url = url
        self.timeout = timeout

    def ask(self, req: ActionRequest) -> bool:
        import urllib.request

        body = json.dumps({
            "worker": req.worker, "action": req.action, "level": req.level,
            "summary": req.summary, "details": req.details,
        }).encode("utf-8")
        http_req = urllib.request.Request(
            self.url, data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(http_req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # ağ/parse hatası — fail-closed
            _log.warning("webhook onayı alınamadı (%s) — red sayılıyor", exc)
            return False
        return isinstance(payload, dict) and payload.get("approve") is True


_channel: ApprovalChannel = TerminalChannel()
_channel_allow_non_interactive = False


def set_channel(channel: ApprovalChannel, *,
                allow_non_interactive: bool = False) -> None:
    """Aktif onay kanalını değiştirir (gömülü uygulamalar/bot köprüleri için).

    allow_non_interactive=True verilirse etkileşimsiz oturumlarda bile
    (SEND/DELETE dahil) onay bu kanala sorulur — bilinçli bir tercihtir ve
    kararlar audit zincirine kullanılan kanalın adıyla yazılır.
    """
    global _channel, _channel_allow_non_interactive
    _channel = channel
    _channel_allow_non_interactive = allow_non_interactive


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
    if not sys.stdin.isatty() and not _channel_allow_non_interactive:
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

    kanal = type(_channel).__name__
    if _channel.ask(req):
        audit.log_event("action_user_approved", req.worker, req.level, "approved",
                        {"action": req.action, "kanal": kanal, **req.details})
        return

    audit.log_event("action_user_rejected", req.worker, req.level, "rejected",
                    {"action": req.action, "kanal": kanal})
    raise ApprovalDenied(f"Onay alınamadı: {req.action}")
