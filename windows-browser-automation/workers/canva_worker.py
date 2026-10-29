"""Canva Connect worker'ı — tasarım export'u (async job).

Gereken (.env): CANVA_ACCESS_TOKEN (Connect API OAuth token'ı,
design:content:read + asset kapsamlarıyla).

Not: Canva'nın canvas'ını UI'dan sürükle-bırakla yönetmek yerine export
API'si kullanılır; API'nin yapamadığı editör işlemleri için masaüstü
fallback (Terminator) devreye girer — bkz. README.
"""
from __future__ import annotations

import re
import time
from pathlib import Path

from policygate import ActionRequest, audit, require, secrets
from core.http import request_bytes, request_json

WORKER = "canva"
API = "https://api.canva.com/rest/v1"
POLL_SANIYE = 2
POLL_DENEME = 60  # ~2 dakika
_DESIGN_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_FORMAT_RE = re.compile(r"^[a-z0-9]+$")


def _headers() -> dict[str, str]:
    token = secrets.get("CANVA_ACCESS_TOKEN", required=True)
    return {"Authorization": f"Bearer {token}"}


def export_design(design_id: str, fmt: str = "pdf",
                  out_dir: str = "data/canva") -> list[Path]:
    """Export job başlatır, tamamlanana dek bekler, dosyaları indirir."""
    if not _DESIGN_ID_RE.fullmatch(design_id):
        raise ValueError("Canva tasarım kimliği yalnız harf, rakam, _ ve - içerebilir")
    if not _FORMAT_RE.fullmatch(fmt):
        raise ValueError("Canva formatı yalnız küçük harf ve rakam içerebilir")
    require(ActionRequest(
        worker=WORKER,
        action="canva.export_design",
        level="DRAFT",
        summary="Canva export job başlatılacak ve dosya yazılacak.",
        details={"design_id": design_id, "format": fmt, "out_dir": out_dir},
    ))
    audit.log_event("canva_export_start", WORKER, "DRAFT", "auto",
                    {"design_id": design_id, "format": fmt})
    job = request_json(
        "POST", f"{API}/exports", WORKER, headers=_headers(),
        json_body={"design_id": design_id, "format": {"type": fmt}},
        level="DRAFT", max_retries=0,  # her deneme yeni job açar (idempotent değil)
    )
    job_id = job["job"]["id"]

    for _ in range(POLL_DENEME):
        time.sleep(POLL_SANIYE)
        status = request_json(
            "GET", f"{API}/exports/{job_id}", WORKER, headers=_headers())
        state = status["job"]["status"]
        if state == "success":
            return _download(status["job"].get("urls", []), design_id, fmt, out_dir)
        if state == "failed":
            raise RuntimeError(
                f"Canva export başarısız: {status['job'].get('error')}")
    raise TimeoutError("Canva export zaman aşımına uğradı (~2 dk).")


def _download(urls: list[str], design_id: str, fmt: str,
              out_dir: str) -> list[Path]:
    out = Path(out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, url in enumerate(urls):
        path = (out / f"{design_id}-{i}.{fmt}").resolve()
        if path.parent != out:
            raise ValueError("Canva çıktısı hedef dizinin dışına çıkamaz")
        part = path.with_name(path.name + ".part")
        try:
            data = request_bytes(
                "GET", url, WORKER, timeout=120, level="DRAFT")
            if not data:
                raise RuntimeError(f"Canva indirmesi boş döndü: {design_id}-{i}")
            part.write_bytes(data)
            part.replace(path)
        except Exception:
            part.unlink(missing_ok=True)
            for produced in paths:
                produced.unlink(missing_ok=True)
            raise
        paths.append(path)
    audit.log_event("canva_export_done", WORKER, "DRAFT", "done",
                    {"files": [str(path) for path in paths]})
    return paths
