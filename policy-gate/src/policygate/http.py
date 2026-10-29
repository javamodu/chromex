"""Ortak HTTP yardımcısı (opsiyonel: `policygate[http]` extra'sı gerektirir).

- Her deneme audit zincirine yazılır (URL + durum kodu; header'lar ve
  token'lar ASLA loglanmaz).
- 429 / 5xx / ağ hatalarında üstel geri çekilme + jitter ile yeniden dener
  (varsayılan 3 tekrar; Retry-After başlığına saygı duyar, bekleme <= 60 sn).
- Diğer 4xx durumlarında kısa gövdeyle HttpError fırlatır (retry edilmez);
  gövde metni secrets.redact ile maskelenir.
- 2xx gelip gövde JSON değilse HttpError fırlatır (sessiz hata yok).

Not: Yeniden deneme mutasyon uçlarında da çalışır; idempotent OLMAYAN bir
POST çağırıyorsanız max_retries=0 geçin.
"""
from __future__ import annotations

import random
import time
from urllib.parse import urlsplit, urlunsplit
from typing import Any

try:
    import requests
except ImportError:  # policygate[http] extra'sı kurulu değil
    requests = None

from . import audit, secrets
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


def _redact_url(url: str) -> str:
    """Audit ve hata yüzeyleri için URL userinfo ve sorguyu maskeler."""
    parsed = urlsplit(url)
    if parsed.username is not None or parsed.password is not None:
        parsed = parsed._replace(netloc="***")
    masked_query = "***" if parsed.query else ""
    return secrets.redact(urlunsplit(parsed._replace(query=masked_query)))


def _request_response(
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
    if requests is None:
        raise RuntimeError(
            "requests kurulu değil — pip install 'policy-gate[http]' ile kurun.")
    audit_url = _redact_url(url)
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
                    f"{method.upper()} {audit_url} ağ hatası "
                    f"({attempt + 1} deneme): {secrets.redact(str(exc))}") from exc
            wait = _wait_seconds(attempt, None)
            audit.log_event("http_retry", worker, level, "auto", {
                "url": audit_url, "neden": type(exc).__name__,
                "deneme": attempt + 1, "bekleme_sn": round(wait, 1)})
            _log.warning(  # sessiz bekleyis tuzagi: varsayilan seviyede gorunur
                "%s %s ağ hatası — %.1fs sonra tekrar (%d/%d)",
                method.upper(), audit_url, wait, attempt + 1, max_retries + 1)
            time.sleep(wait)
            attempt += 1
            continue

        audit.log_event("http_request", worker, level, "auto", {
            "method": method.upper(), "url": audit_url,
            "status": resp.status_code, "deneme": attempt + 1})

        retryable = resp.status_code == 429 or resp.status_code >= 500
        if retryable and attempt < max_retries:
            wait = _wait_seconds(attempt, resp.headers.get("Retry-After"))
            audit.log_event("http_retry", worker, level, "auto", {
                "url": audit_url, "neden": f"HTTP {resp.status_code}",
                "deneme": attempt + 1, "bekleme_sn": round(wait, 1)})
            _log.warning(  # sessiz bekleyis tuzagi: varsayilan seviyede gorunur
                "%s %s HTTP %s — %.1fs sonra tekrar (%d/%d)",
                method.upper(), audit_url, resp.status_code, wait,
                attempt + 1, max_retries + 1)
            time.sleep(wait)
            attempt += 1
            continue

        return resp


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
    resp = _request_response(
        method, url, worker, headers=headers, params=params,
        json_body=json_body, timeout=timeout, level=level,
        max_retries=max_retries)
    if resp.status_code >= 400:
        raise HttpError(
            f"{method.upper()} {_redact_url(url)} -> {resp.status_code}: "
            f"{secrets.redact(resp.text)[:300]}")
    if not resp.content:
        return resp  # 204 No Content vb. gövdesiz başarı
    content_type = resp.headers.get("Content-Type", "")
    if "json" not in content_type.lower():
        raise HttpError(
            f"{method.upper()} {_redact_url(url)} -> {resp.status_code} "
            f"ama gövde JSON değil (Content-Type: "
            f"{content_type or 'yok'}): {secrets.redact(resp.text)[:200]}")
    try:
        return resp.json()
    except ValueError as exc:
        raise HttpError(
            f"{method.upper()} {_redact_url(url)} -> geçersiz JSON gövdesi: "
            f"{secrets.redact(resp.text)[:200]}") from exc


def request_bytes(
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
) -> bytes:
    """Bayt indirmesi için aynı retry/audit/redaksiyon akışını kullanır."""
    resp = _request_response(
        method, url, worker, headers=headers, params=params,
        json_body=json_body, timeout=timeout, level=level,
        max_retries=max_retries)
    if resp.status_code >= 400:
        raise HttpError(
            f"{method.upper()} {_redact_url(url)} -> {resp.status_code}: "
            f"{secrets.redact(resp.text)[:300]}")
    return resp.content
