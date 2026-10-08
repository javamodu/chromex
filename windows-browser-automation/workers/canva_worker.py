"""Canva Connect worker'ı — tasarım export'u (async job).

Gereken (.env): CANVA_ACCESS_TOKEN (Connect API OAuth token'ı,
design:content:read + asset kapsamlarıyla).

Not: Canva'nın canvas'ını UI'dan sürükle-bırakla yönetmek yerine export
API'si kullanılır; API'nin yapamadığı editör işlemleri için masaüstü
fallback (Terminator) devreye girer — bkz. README.
"""
from __future__ import annotations

import time
from pathlib import Path

from policygate import audit, secrets
from core.http import request_json

WORKER = "canva"
API = "https://api.canva.com/rest/v1"
POLL_SANIYE = 2
POLL_DENEME = 60  # ~2 dakika


def _headers() -> dict[str, str]:
    token = secrets.get("CANVA_ACCESS_TOKEN", required=True)
    return {"Authorization": f"Bearer {token}"}


def export_design(design_id: str, fmt: str = "pdf",
                  out_dir: str = "data/canva") -> list[Path]:
    """Export job başlatır, tamamlanana dek bekler, dosyaları indirir."""
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
    import requests

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for i, url in enumerate(urls):
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        path = out / f"{design_id}-{i}.{fmt}"
        path.write_bytes(resp.content)
        paths.append(path)
    audit.log_event("canva_export_done", WORKER, "DRAFT", "done",
                    {"files": [str(p) for p in paths]})
    return paths
