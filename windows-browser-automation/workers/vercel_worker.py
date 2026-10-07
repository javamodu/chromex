"""Vercel worker'ı — deployment durumu ve build log'ları (REST).

Gereken (.env): VERCEL_TOKEN (Account Settings → Tokens),
opsiyonel VERCEL_TEAM_ID (takım hesapları için).

cancel_deployment, MODIFY seviyesinde onay kapısının nasıl kullanılacağına
örnektir; production'a dokunan her ek uç için aynı kalıp uygulanmalıdır.
"""
from __future__ import annotations

from core import audit, secrets
from core.approval import ActionRequest, require
from core.http import request_json

WORKER = "vercel"
API = "https://api.vercel.com"


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {secrets.get('VERCEL_TOKEN', required=True)}"}


def _team_params() -> dict[str, str]:
    team = secrets.get("VERCEL_TEAM_ID")
    return {"teamId": team} if team else {}


def list_deployments(app: str | None = None, limit: int = 10) -> list[dict]:
    audit.log_event("vercel_deployments", WORKER, "READ", "auto",
                    {"app": app, "limit": limit})
    params: dict = {"limit": limit, **_team_params()}
    if app:
        params["app"] = app
    data = request_json("GET", f"{API}/v6/deployments", WORKER,
                        headers=_headers(), params=params)
    return [
        {
            "uid": d.get("uid"),
            "name": d.get("name"),
            "state": d.get("state") or d.get("readyState"),
            "url": d.get("url"),
            "created": d.get("created") or d.get("createdAt"),
        }
        for d in data.get("deployments", [])
    ]


def deployment_events(deployment_id: str, limit: int = 100) -> list[dict]:
    audit.log_event("vercel_events", WORKER, "READ", "auto",
                    {"deployment": deployment_id, "limit": limit})
    data = request_json(
        "GET", f"{API}/v3/deployments/{deployment_id}/events", WORKER,
        headers=_headers(), params={"limit": limit, **_team_params()})
    events = data if isinstance(data, list) else data.get("events", [])
    out = []
    for e in events:
        text = e.get("text") or (e.get("payload") or {}).get("text") or ""
        out.append({
            "type": e.get("type"),
            "created": e.get("created") or e.get("createdAt"),
            "text": str(text)[:2000],
        })
    return out


def cancel_deployment(deployment_id: str) -> dict:
    """Devam eden deployment'ı iptal eder — MODIFY, kullanıcı onayı ister."""
    require(ActionRequest(
        worker=WORKER, action="vercel.cancel_deployment", level="MODIFY",
        summary="Vercel deployment İPTAL edilecek.",
        details={"deployment_id": deployment_id},
    ))
    return request_json(
        "PATCH", f"{API}/v12/deployments/{deployment_id}/cancel", WORKER,
        headers=_headers(), params=_team_params(), level="MODIFY")
