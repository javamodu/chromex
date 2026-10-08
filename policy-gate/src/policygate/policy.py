"""Yetki policy'si: hangi seviye otomatik, hangisi onaya tabi.

config/policy.json dosyasından okunur; dosya yoksa VEYA bozuksa güvenli
varsayılanlar kullanılır (fail-safe). DELETE seviyesi config ne derse desin
asla "auto" olamaz.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .log import get as _get_logger

_log = _get_logger("policy")

DEFAULT_POLICY: dict = {
    "levels": {
        "READ": "auto",
        "DRAFT": "auto",
        "SEND": "ask",
        "MODIFY": "ask",
        "DELETE": "ask",
    },
    "non_interactive_default": "deny",
    "always_deny": [],
}

_GECERLI_SEVIYELER = {"READ", "DRAFT", "SEND", "MODIFY", "DELETE"}
_GECERLI_MODLAR = {"auto", "ask", "deny"}


def _policy_path() -> Path:
    return Path(os.environ.get("POLICY_FILE", "config/policy.json"))


def load() -> dict:
    """Policy'yi oku; bozuk/eksik dosyada güvenli varsayılanlara düş (fail-safe)."""
    path = _policy_path()
    if not path.exists():
        return json.loads(json.dumps(DEFAULT_POLICY))  # kopya
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _log.warning("policy okunamadı (%s) — güvenli varsayılanlar devrede", exc)
        return json.loads(json.dumps(DEFAULT_POLICY))
    if not isinstance(data, dict):
        _log.warning("policy bir nesne değil — güvenli varsayılanlar devrede")
        return json.loads(json.dumps(DEFAULT_POLICY))
    merged = json.loads(json.dumps(DEFAULT_POLICY))
    # Bilinmeyen üst seviye anahtarlar ileri-uyumluluk için korunur;
    # bilinen üç anahtar şema doğrulamasından geçer (bozuk alan atlanır).
    merged.update({k: v for k, v in data.items()
                   if k not in {"levels", "non_interactive_default",
                                "always_deny"}})
    _dogrula(data, merged)
    return merged


def _dogrula(data: dict, merged: dict) -> None:
    """Şema doğrulaması: geçersiz alanlar uyarıyla atlanır, kalanı uygulanır."""
    levels = data.get("levels")
    if isinstance(levels, dict):
        for ad, mod in levels.items():
            if str(ad).upper() in _GECERLI_SEVIYELER \
                    and str(mod).lower() in _GECERLI_MODLAR:
                merged["levels"][str(ad).upper()] = str(mod).lower()
            else:
                _log.warning("policy.levels: geçersiz girdi atlandı: %r=%r",
                             ad, mod)
    nid = data.get("non_interactive_default")
    if nid is not None:
        if str(nid).lower() in {"auto", "deny"}:
            merged["non_interactive_default"] = str(nid).lower()
        else:
            _log.warning("non_interactive_default geçersiz (%r) — 'deny' "
                         "varsayılıyor", nid)
    ad = data.get("always_deny")
    if ad is None:
        pass
    elif isinstance(ad, list) and all(isinstance(x, str) for x in ad):
        merged["always_deny"] = ad
    else:
        _log.warning("always_deny str listesi değil — yok sayıldı")


def decision_for(level: str, action_name: str, policy: dict | None = None) -> str:
    """Bir işlem için karar: 'auto' | 'ask' | 'deny'."""
    policy = policy or load()
    if action_name in policy.get("always_deny", []):
        return "deny"
    mode = str(policy.get("levels", {}).get(level.upper(), "ask")).lower()
    if mode not in {"auto", "ask", "deny"}:
        mode = "ask"
    if level.upper() == "DELETE" and mode == "auto":
        mode = "ask"  # silme işlemleri hiçbir zaman otomatik onaylanmaz
    return mode
