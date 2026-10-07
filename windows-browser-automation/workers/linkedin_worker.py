"""LinkedIn worker'ı — resmi API (OIDC userinfo + UGC Posts).

Gerekenler (.env):
- LINKEDIN_CLIENT_ID      : developer.linkedin.com uygulamasının client id'si
- LINKEDIN_CLIENT_SECRET  : yalnızca token yenileme için
- LINKEDIN_ACCESS_TOKEN   : OAuth2 user-context access token
                            (scope: openid profile w_member_social)
- LINKEDIN_REFRESH_TOKEN  : uygulamada refresh token etkinse

Token üretimi: developer.linkedin.com'da uygulamaya "Sign In with LinkedIn
using OpenID Connect" ve "Share on LinkedIn" ürünlerini ekleyin, OAuth2
3-legged akışıyla access token alın (access token ömrü ~60 gün).

KAPSAM (dürüst not): Self-serve API yalnızca kendi profilinizi okumaya
(userinfo) ve kendi adınıza paylaşım yapmaya (w_member_social) izin verir.
Akış okuma, kişi arama ve başkasının içeriğini çekme resmi API'de YOKTUR;
tarayıcıyla scraping LinkedIn kullanım koşullarına aykırıdır ve bu depo
bilinçli olarak içermez (X worker'ındaki yaklaşımın aynısı).

UGC API taslak desteklemez; paylaşım doğrudan YAYINLANIR, bu yüzden SEND
seviyesinde onay kapısından geçer (geri alma yoktur, yalnızca silinebilir).
"""
from __future__ import annotations

import json

from core import audit, secrets, store
from core.approval import ActionRequest, require
from core.http import request_json

WORKER = "linkedin"
API = "https://api.linkedin.com"


def _headers() -> dict[str, str]:
    token = secrets.get("LINKEDIN_ACCESS_TOKEN", required=True)
    return {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def me() -> dict:
    """Token sahibinin temel profili (OIDC userinfo; openid + profile scope)."""
    audit.log_event("linkedin_me", WORKER, "READ", "auto", {})
    data = request_json("GET", f"{API}/v2/userinfo", WORKER, headers=_headers())
    profile = {
        "id": data.get("sub"),
        "ad": data.get("name"),
        "email": data.get("email"),
        "resim": data.get("picture"),
    }
    store.save(WORKER, "profile", profile["id"], profile["ad"],
               json.dumps(data, ensure_ascii=False))
    return profile


def create_post(text: str, visibility: str = "PUBLIC") -> str:
    """Metin paylaşımı YAYINLAR — SEND seviyesi, onay ister. Taslak yoktur."""
    visibility = visibility.upper()
    if visibility not in {"PUBLIC", "CONNECTIONS"}:
        raise ValueError("visibility PUBLIC veya CONNECTIONS olmalı.")
    author_id = me()["id"]
    require(ActionRequest(
        worker=WORKER,
        action="linkedin.create_post",
        level="SEND",
        summary="LinkedIn'de paylaşım YAYINLANACAK — metni ve görünürlüğü "
                "kontrol edin (geri alma yok; yalnızca silinebilir).",
        details={
            "görünürlük": visibility,
            "metin_önizleme": text[:500],
            "uzunluk": len(text),
        },
    ))
    body = {
        "author": f"urn:li:person:{author_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": visibility,
        },
    }
    data = request_json(
        "POST", f"{API}/v2/ugcPosts", WORKER,
        headers=_headers(), json_body=body, level="SEND", max_retries=0,
    )
    post_id = data.get("id", "") if isinstance(data, dict) else ""
    audit.log_event("linkedin_post_created", WORKER, "SEND", "done",
                    {"id": post_id, "görünürlük": visibility})
    store.save(WORKER, "post", post_id, text[:80], None)
    return post_id


def refresh_access_token() -> str:
    """OAuth2 refresh (uygulamada refresh token etkin olmalı).

    Yeni token'lar gitignore kapsamındaki data/linkedin_tokens.env dosyasına
    yazılır; terminale BASILMAZ. Değerleri .env'e taşıyıp dosyayı silin.
    """
    import requests
    from pathlib import Path

    client_id = secrets.get("LINKEDIN_CLIENT_ID", required=True)
    client_secret = secrets.get("LINKEDIN_CLIENT_SECRET", required=True)
    refresh = secrets.get("LINKEDIN_REFRESH_TOKEN", required=True)
    resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    audit.log_event("linkedin_token_refreshed", WORKER, "READ", "auto",
                    {"expires_in": data.get("expires_in")})
    out = Path("data/linkedin_tokens.env")
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"LINKEDIN_ACCESS_TOKEN={data.get('access_token', '')}"]
    if data.get("refresh_token"):
        lines.append(f"LINKEDIN_REFRESH_TOKEN={data['refresh_token']}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Yeni token(lar) {out} dosyasına yazıldı — değerleri .env'e taşıyıp "
          "bu dosyayı silin.")
    return data["access_token"]
