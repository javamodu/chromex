"""X (Twitter) yer işaretleri worker'ı — resmi API v2.

Gerekenler (.env):
- X_CLIENT_ID     : developer.x.com'daki uygulamanın OAuth2 client id'si
- X_ACCESS_TOKEN  : OAuth2 user-context access token
                    (scope: bookmark.read tweet.read users.read offline.access)
- X_REFRESH_TOKEN : offline.access ile alınan refresh token
- X_USER_ID       : kendi sayısal kullanıcı id'niz

MALİYET UYARISI: X'in Nisan 2026 fiyatlandırmasında owned-read çağrıları
kayıt başına (~$0.001/kayıt) ücretlendirilir; büyük limitlerde faturayı
Developer Console'dan doğrulayın. Browser fallback'i kırılgandır ve
önerilmez — bkz. README.
"""
from __future__ import annotations

import json

from core import oauth, store
from policygate import audit, secrets
from core.http import request_json

WORKER = "x"
API = "https://api.x.com/2"


def _headers() -> dict[str, str]:
    token = secrets.get("X_ACCESS_TOKEN", required=True)
    return {"Authorization": f"Bearer {token}"}


def fetch_bookmarks(limit: int = 50) -> list[dict]:
    """Kendi yer işaretlerini sayfalayarak çeker ve depoya yazar."""
    user_id = secrets.get("X_USER_ID", required=True)
    audit.log_event("x_bookmarks_fetch", WORKER, "READ", "auto",
                    {"limit": limit})
    collected: list[dict] = []
    next_token: str | None = None
    while len(collected) < limit:
        params: dict = {
            "max_results": max(1, min(100, limit - len(collected))),
            "tweet.fields": "created_at,text,author_id",
        }
        if next_token:
            params["pagination_token"] = next_token
        data = request_json(
            "GET", f"{API}/users/{user_id}/bookmarks", WORKER,
            headers=_headers(), params=params,
        )
        for tweet in data.get("data", []):
            collected.append(tweet)
            store.save("x", "bookmark", tweet.get("id"),
                       (tweet.get("text") or "")[:80],
                       json.dumps(tweet, ensure_ascii=False))
        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            break
    return collected


def refresh_access_token() -> str:
    """OAuth2 refresh (public/PKCE client). Yeni token'ları .env'e siz yazın."""
    return oauth.refresh_access_token(
        token_url=f"{API}/oauth2/token",
        client_id=secrets.get("X_CLIENT_ID", required=True),
        refresh_token=secrets.get("X_REFRESH_TOKEN", required=True),
        out_file="data/x_tokens.env",
        access_key="X_ACCESS_TOKEN",
        refresh_key="X_REFRESH_TOKEN",
        worker=WORKER,
    )
