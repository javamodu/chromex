"""Append-only audit log (JSONL) + SHA-256 hash zinciri.

Her kayıt bir önceki kaydın hash'ini içerir; dosyada sonradan yapılan her
değişiklik `verify_chain()` ile tespit edilir. Secret değerleri yazılmadan
önce core.secrets.redact_obj ile maskelenir.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

from . import secrets

_GENESIS = "0" * 64
_last_cache: dict[str, tuple[str, int]] = {}  # dosya yolu -> (son hash, kayıt sayısı)


def _audit_file() -> Path:
    return Path(os.environ.get("AUDIT_DIR", "audit")) / "audit.jsonl"


def _canonical(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _record_hash(prev_hash: str, record_without_hash: dict) -> str:
    payload = prev_hash + _canonical(record_without_hash)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _last_hash(path: Path) -> tuple[str, int]:
    key = str(path.resolve())
    if key in _last_cache:
        return _last_cache[key]
    if not path.exists():
        _last_cache[key] = (_GENESIS, 0)
        return _last_cache[key]
    last_line, count = None, 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                last_line = line
                count += 1
    if last_line is None:
        _last_cache[key] = (_GENESIS, 0)
    else:
        _last_cache[key] = (json.loads(last_line)["hash"], count)
    return _last_cache[key]


def log_event(
    event: str,
    worker: str,
    level: str,
    decision: str,
    details: dict[str, Any] | None = None,
) -> dict:
    """Bir olayı zincire ekler ve kaydı döndürür."""
    path = _audit_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    prev_hash, seq = _last_hash(path)
    record: dict[str, Any] = {
        "seq": seq + 1,
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "event": event,
        "worker": worker,
        "level": level.upper(),
        "decision": decision,
        "details": secrets.redact_obj(details or {}),
        "prev_hash": prev_hash,
    }
    record["hash"] = _record_hash(prev_hash, record)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(_canonical(record) + "\n")
    _last_cache[str(path.resolve())] = (record["hash"], record["seq"])
    return record


def verify_chain() -> tuple[bool, str]:
    """Tüm zinciri baştan doğrular: (sağlam mı, mesaj)."""
    path = _audit_file()
    if not path.exists():
        return True, "Audit dosyası yok; zincir boş."
    prev, n = _GENESIS, 0
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                return False, f"{i}. satır geçerli JSON değil."
            body = {k: v for k, v in rec.items() if k != "hash"}
            if rec.get("prev_hash") != prev or rec.get("hash") != _record_hash(prev, body):
                return False, f"Zincir {i}. satırda bozuk (seq={rec.get('seq')})."
            prev = rec["hash"]
            n += 1
    return True, f"Zincir sağlam: {n} kayıt."
