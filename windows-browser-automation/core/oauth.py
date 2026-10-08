"""OAuth2 refresh_token akışı için ortak yardımcı.

X (public/PKCE client) ve LinkedIn (confidential client) worker'ları bunu
kullanır; yeni bir OAuth2 worker'ı eklemek tek bir fonksiyon çağrısıdır.

Güvenlik: token değerleri terminale BASILMAZ; sonuç gitignore kapsamındaki
data/ altına yazılır ve kullanıcıdan .env'e taşıması istenir.
"""
from __future__ import annotations

from pathlib import Path

from . import audit


def refresh_access_token(
    *,
    token_url: str,
    client_id: str,
    refresh_token: str,
    client_secret: str | None = None,
    out_file: str,
    access_key: str,
    refresh_key: str,
    worker: str,
    timeout: int = 30,
) -> str:
    """Refresh token ile yeni access token alır ve data/<...>.env'e yazar.

    Dönen access token çağırıcıya verilir; dosyaya yazma kullanıcıya
    değerleri kalıcı .env'e taşıması için geçici bir köprüdür.
    """
    import requests

    form = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    if client_secret:
        form["client_secret"] = client_secret
    resp = requests.post(token_url, data=form, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    audit.log_event(f"{worker}_token_refreshed", worker, "READ", "auto",
                    {"expires_in": payload.get("expires_in")})
    out = Path(out_file)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{access_key}={payload.get('access_token', '')}"]
    if payload.get("refresh_token"):
        lines.append(f"{refresh_key}={payload['refresh_token']}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Yeni token(lar) {out} dosyasına yazıldı — değerleri .env'e taşıyıp "
          "bu dosyayı silin.")
    return payload["access_token"]