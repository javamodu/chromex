#!/usr/bin/env python3
"""ralph.sh → audit köprüsü (stdlib-only, bağımlılık yok).

Plan 2'deki core/audit.py ile BİREBİR AYNI formatta append-only, SHA-256
hash zincirli JSONL üretir; iki zincir aynı araçlarla doğrulanabilir.

Bu dosya bilinçli bir KOPYADIR: kit başka projelere taşınabilmesi için
bağımsız tutulur. Format eşdeğerliği windows-browser-automation tarafındaki
tests/test_workers.py::AuditBridgeParityTests ile sabitlenmiştir —
core/audit.py'nin formatını değiştirirsen burayı da güncelle (ve tersi).

Kullanım:
    python3 audit_bridge.py log <event> [anahtar=deger ...]
    python3 audit_bridge.py verify

Dosya: $AUDIT_DIR/audit.jsonl (varsayılan: ./audit/audit.jsonl — komutu
çalıştırdığın dizinde oluşur; commit etme).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

_GENESIS = "0" * 64

if os.name == "nt":
    import msvcrt

    def _lock(fh) -> None:
        fh.seek(0, 2)
        if fh.tell() == 0:
            fh.write(b"\0")
            fh.flush()
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock(fh) -> None:
        fh.seek(0)
        msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _lock(fh) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)

    def _unlock(fh) -> None:
        fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _audit_file() -> Path:
    return Path(os.environ.get("AUDIT_DIR", "audit")) / "audit.jsonl"


def _canonical(record: dict) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def _record_hash(prev_hash: str, body: dict) -> str:
    payload = prev_hash + _canonical(body)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _last() -> tuple[str, int]:
    path = _audit_file()
    if not path.exists():
        return _GENESIS, 0
    last_line, count = None, 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                last_line, count = line, count + 1
    if last_line is None:
        return _GENESIS, 0
    return json.loads(last_line)["hash"], count


def log(event: str, details: dict) -> dict:
    path = _audit_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_suffix(".lock")
    with open(lock_path, "a+b") as lock_fh:
        _lock(lock_fh)
        try:
            prev, seq = _last()
            record = {
                "seq": seq + 1,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "event": event,
                "worker": "ralph",
                "level": "READ",
                "decision": "auto",
                "details": details,
                "prev_hash": prev,
            }
            record["hash"] = _record_hash(prev, record)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(_canonical(record) + "\n")
        finally:
            _unlock(lock_fh)
    return record


def verify() -> tuple[bool, str]:
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
            prev, n = rec["hash"], n + 1
    return True, f"Zincir sağlam: {n} kayıt."


def main(argv: list[str]) -> int:
    if len(argv) >= 3 and argv[1] == "log":
        details = dict(arg.split("=", 1) for arg in argv[3:] if "=" in arg)
        log(argv[2], details)
        return 0
    if len(argv) >= 2 and argv[1] == "verify":
        ok, msg = verify()
        print(("SAĞLAM — " if ok else "BOZUK — ") + msg)
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
