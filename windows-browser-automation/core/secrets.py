"""Ortam değişkenleri ve .env yükleme.

Kurallar:
- Secret değerleri ASLA loglanmaz ve print edilmez.
- get() ile okunan her değer redaksiyon kaydına girer; audit log'a yazılan
  metinlerde bu değerler otomatik olarak *** ile maskelenir.
"""
from __future__ import annotations

import os
from pathlib import Path

_REGISTERED: set[str] = set()


def load_dotenv(path: str | Path = ".env") -> None:
    """Basit .env yükleyici (yalnızca KEY=VALUE satırları, stdlib)."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def get(name: str, required: bool = False, default: str | None = None) -> str | None:
    """Env değişkeni oku; secret ise redaksiyon kaydına ekle."""
    value = os.environ.get(name) or default
    if required and not value:
        raise RuntimeError(
            f"Gerekli ortam değişkeni eksik: {name} — .env.example dosyasına bakın."
        )
    if value and len(value) >= 6:
        _REGISTERED.add(value)
    return value


def redact(text: str) -> str:
    """Metindeki bilinen secret değerlerini maskele."""
    for secret in _REGISTERED:
        if secret in text:
            text = text.replace(secret, "***")
    return text


def redact_obj(obj):
    """dict/list/str yapılarında özyinelemeli redaksiyon."""
    if isinstance(obj, str):
        return redact(obj)
    if isinstance(obj, dict):
        return {k: redact_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_obj(v) for v in obj]
    return obj
