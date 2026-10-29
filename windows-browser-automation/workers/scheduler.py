"""Tek seferlik dosya tabanlı iş koşucu (yalnız READ/DRAFT)."""
from __future__ import annotations

import json, subprocess, sys
from pathlib import Path

from core import store
from policygate import (ActionRequest, ApprovalDenied, audit, preflight,
                        require)

WORKER = "scheduler"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
IZINLI_SEVIYELER = {"READ", "DRAFT"}
VARSAYILAN_ZAMAN_ASIMI = 60


class SchedulerError(RuntimeError):
    pass


def _log_reject(reason: str, command: str | None = None,
                level: str = "READ") -> None:
    audit.log_event("scheduler_job_rejected", WORKER, level, "deny",
                    {"reason": reason, **({"command": command} if command else {})})


def load_job(path: str | Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        _log_reject("geçersiz JSON")
        raise SchedulerError("İş tanımı okunamadı veya JSON bozuk") from exc
    if not isinstance(data, dict):
        _log_reject("kök nesne değil")
        raise SchedulerError("İş tanımı bir JSON nesnesi olmalı")

    command = data.get("komut")
    args = data.get("args", [])
    level = data.get("seviye")
    timeout = data.get("zaman_asimi", VARSAYILAN_ZAMAN_ASIMI)
    if not isinstance(command, str) or not command.strip():
        _log_reject("komut eksik", command if isinstance(command, str) else None)
        raise SchedulerError("komut boş olamaz")
    if command == "zamanla":
        _log_reject("özyineleme yasak", command)
        raise SchedulerError("zamanla komutu zamanlanamaz")
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        _log_reject("args liste değil", command)
        raise SchedulerError("args yalnızca metin listesi olabilir")
    if not isinstance(level, str) or level.upper() not in IZINLI_SEVIYELER:
        raw_level = level if isinstance(level, str) else "(boş)"
        _log_reject("izin dışı seviye", command, raw_level)
        raise ApprovalDenied(f"Zamanlayıcı yalnız READ/DRAFT kabul eder: {raw_level}")
    if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
        _log_reject("zaman aşımı geçersiz", command, level.upper())
        raise SchedulerError("zaman_asimi 1 veya daha büyük olmalı")
    return {"komut": command, "args": args, "seviye": level.upper(), "zaman_asimi": timeout}


def run_job(path: str | Path) -> int:
    job = load_job(path)
    command, level = job["komut"], job["seviye"]
    request = ActionRequest(worker=WORKER, action=f"scheduler.{command}", level=level,
                            summary="Zamanlanmış iş çalıştırılacak.",
                            details={"command": command, "args": job["args"]})
    preflight(request)
    require(request)
    audit.log_event("scheduler_job_started", WORKER, level, "auto",
                    {"command": command, "args": job["args"]})
    cli_command = [sys.executable, "-m", "orchestrator.cli", command, *job["args"]]
    try:
        result = subprocess.run(cli_command, cwd=PACKAGE_ROOT, check=False, timeout=job["zaman_asimi"])
    except subprocess.TimeoutExpired as exc:
        audit.log_event("scheduler_job_failed", WORKER, level, "failed",
                        {"command": command, "reason": "timeout"})
        store.save(WORKER, "job", command, level, "timeout")
        raise TimeoutError(f"Zamanlanmış iş zaman aşımına uğradı: {command}") from exc
    except OSError as exc:
        audit.log_event("scheduler_job_failed", WORKER, level, "failed",
                        {"command": command, "reason": type(exc).__name__})
        store.save(WORKER, "job", command, level, "error")
        raise SchedulerError(f"Zamanlanmış iş başlatılamadı: {command}") from exc
    audit.log_event("scheduler_job_finished", WORKER, level, "auto",
                    {"command": command, "exit_code": result.returncode})
    store.save(WORKER, "job", command, level,
               f"exit:{result.returncode}" if result.returncode else "ok")
    return result.returncode
