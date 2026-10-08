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
    merged.update({k: v for k, v in data.items() if k != "levels"})
    levels = data.get("levels")
    if isinstance(levels, dict):
        merged["levels"].update(levels)
    return merged


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
