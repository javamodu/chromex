"""Supabase worker'ı.

- query_table: PostgREST üzerinden SALT-OKUNUR sorgu (READ).
- cli: `supabase` CLI sarmalayıcı; push/deploy/reset gibi mutasyonlar
  MODIFY seviyesinde onaya tabidir.

Güvenlik: SUPABASE_SERVICE_ROLE_KEY yalnızca sunucu tarafında (env) durur;
tarayıcıya, log'a veya örnek dosyalara asla yazılmaz. Agent tarafında
resmi Supabase MCP'nin --read-only modu tercih edilir (bkz. config/).
"""
from __future__ import annotations

import shutil
import subprocess

from core import audit, secrets
from core.approval import ActionRequest, require
from core.http import request_json

WORKER = "supabase"
_MUTATING = {"push", "deploy", "reset", "delete", "unlink", "restore", "seed"}


def query_table(table: str, select: str = "*", limit: int = 20,
                filters: dict[str, str] | None = None) -> list[dict]:
    base = secrets.get("SUPABASE_URL", required=True).rstrip("/")
    key = secrets.get("SUPABASE_SERVICE_ROLE_KEY") or secrets.get(
        "SUPABASE_ANON_KEY", required=True)
    audit.log_event("supabase_query", WORKER, "READ", "auto",
                    {"table": table, "select": select, "limit": limit})
    params: dict[str, str] = {"select": select, "limit": str(limit)}
    if filters:
        params.update(filters)  # ör. {"status": "eq.active"}
    return request_json(
        "GET", f"{base}/rest/v1/{table}", WORKER,
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        params=params,
    )


def cli(args: list[str]) -> str:
    """`supabase <args>` çalıştırır. Mutasyonlar onay kapısından geçer."""
    if shutil.which("supabase") is None:
        raise RuntimeError("supabase CLI kurulu değil (npm i -g supabase).")
    komut = "supabase " + " ".join(args)
    if _MUTATING & set(args):
        require(ActionRequest(
            worker=WORKER, action="supabase.cli", level="MODIFY",
            summary="Supabase CLI ile DEĞİŞTİRİCİ işlem çalıştırılacak.",
            details={"komut": komut},
        ))
    else:
        audit.log_event("supabase_cli", WORKER, "READ", "auto",
                        {"komut": komut})
    out = subprocess.run(["supabase", *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout).strip()[:500])
    return out.stdout
