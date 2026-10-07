"""Ortak HTTP yardımcısı.

- Her deneme audit zincirine yazılır (URL + durum kodu; header'lar ve
  token'lar ASLA loglanmaz).
- 429 / 5xx / ağ hatalarında üstel geri çekilme + jitter ile yeniden dener
  (varsayılan 3 tekrar; Retry-After başlığına saygı duyar, bekleme <= 60 sn).
- Diğer 4xx durumlarında kısa gövdeyle HttpError fırlatır (retry edilmez).

Not: Yeniden deneme mutasyon uçlarında da çalışır; idempotent OLMAYAN bir
POST çağırıyorsanız max_retries=0 geçin.
"""
from __future__ import annotations

import random
import time
from typing import Any

import requests

from . import audit
from .log import get as _get_logger

_log = _get_logger("http")


class HttpError(RuntimeError):
    pass


def _wait_seconds(attempt: int, retry_after: str | None) -> float:
    if retry_after and retry_after.isdigit():
        wait = float(retry_after)
    else:
        wait = (2 ** attempt) + random.uniform(0, 0.5)
    return min(wait, 60.0)


def request_json(
    method: str,
    url: str,
    worker: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: int = 30,
    level: str = "READ",
    max_retries: int = 3,
) -> Any:
    attempt = 0
    while True:
        try:
            resp = requests.request(
                method, url, headers=headers, params=params,
                json=json_body, timeout=timeout,
            )
        except requests.RequestException as exc:
            if attempt >= max_retries:
                raise HttpError(
                    f"{method.upper()} {url} ağ hatası "
                    f"({attempt + 1} deneme): {exc}") from exc
            wait = _wait_seconds(attempt, None)
            audit.log_event("http_retry", worker, level, "auto", {
                "url": url, "neden": type(exc).__name__,
                "deneme": attempt + 1, "bekleme_sn": round(wait, 1)})
            _log.info("%s ağ hatası — %.1fs sonra tekrar (%d/%d)",
                      url, wait, attempt + 1, max_retries + 1)
            time.sleep(wait)
            attempt += 1
            continue

        audit.log_event("http_request", worker, level, "auto", {
            "method": method.upper(), "url": url,
            "status": resp.status_code, "deneme": attempt + 1})

        retryable = resp.status_code == 429 or resp.status_code >= 500
        if retryable and attempt < max_retries:
            wait = _wait_seconds(attempt, resp.headers.get("Retry-After"))
            audit.log_event("http_retry", worker, level, "auto", {
                "url": url, "neden": f"HTTP {resp.status_code}",
                "deneme": attempt + 1, "bekleme_sn": round(wait, 1)})
            _log.info("%s HTTP %s — %.1fs sonra tekrar (%d/%d)",
                      url, resp.status_code, wait, attempt + 1, max_retries + 1)
            time.sleep(wait)
            attempt += 1
            continue

        if resp.status_code >= 400:
            raise HttpError(
                f"{method.upper()} {url} -> {resp.status_code} "
                f"({attempt + 1} deneme): {resp.text[:300]}")

        content_type = resp.headers.get("Content-Type", "")
        if resp.content and "json" in content_type:
            return resp.json()
        return resp
