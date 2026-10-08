"""policygate — AI ajanları için onay kapısı + SHA-256 audit zinciri.

Sıfır bağımlılık (yalnızca stdlib). Dış etki yaratan her ajan işlemini
beş seviyeli policy + birebir 'EVET' onayı + kurcalama-kanıtlı audit
zinciriyle sarar.

Hızlı kullanım:
    from policygate import ActionRequest, require

    require(ActionRequest(
        worker="gmail", action="gmail.send", level="SEND",
        summary="ahmet@ornek.com'a teklif e-postası gönderilecek",
        details={"konu": "Teklif", "boyut": "2.1 KB"},
    ))
"""
from .approval import (ActionRequest, ApprovalChannel, ApprovalDenied,
                       TerminalChannel, WebhookChannel, require, set_channel)
from .audit import log_event, verify_chain
from .policy import DEFAULT_POLICY, decision_for, load

__version__ = "1.0.0"

__all__ = [
    "ActionRequest", "ApprovalDenied", "require",
    "ApprovalChannel", "TerminalChannel", "WebhookChannel", "set_channel",
    "log_event", "verify_chain",
    "DEFAULT_POLICY", "decision_for", "load",
    "__version__",
]
