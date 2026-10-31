"""YouTube Data API v3 worker'ı — salt-okunur arama, video ve oynatma listesi.

Gereken (.env): YOUTUBE_API_KEY (Google Cloud Console -> YouTube Data API v3
-> API anahtarı). Tüm uçlar READ seviyesindedir; sorgu ve limit policygate
audit zincirine yazılır. API anahtarı URL sorgusunda taşındığı için zincirde
tamamen maskelenir (bkz. policygate.http._redact_url) — anahtar hiçbir
çıktıya, loga veya hataya düz metin olarak girmez.
"""
from __future__ import annotations

import json

from policygate import audit, secrets
from policygate.http import HttpError, request_json

from core import store

WORKER = "youtube"
API = "https://www.googleapis.com/youtube/v3"
MAKS_SONUC = 50  # YouTube maxResults üst sınırı

_TURLER = ("video", "channel", "playlist")
_ID_ALANLARI = {"video": "videoId", "channel": "channelId",
                "playlist": "playlistId"}
_URL_KALIPLARI = {
    "video": "https://www.youtube.com/watch?v={}",
    "channel": "https://www.youtube.com/channel/{}",
    "playlist": "https://www.youtube.com/playlist?list={}",
}

# API hata gövdesindeki reason anahtarları -> tek satır, secret'sız mesaj.
_HATA_ESLESMESI = (
    ("keyInvalid",
     "YouTube API anahtarı geçersiz; .env içindeki YOUTUBE_API_KEY değerini kontrol edin."),
    ("quotaExceeded",
     "YouTube API günlük kotası aşıldı; kota sıfırlanınca tekrar deneyin."),
    ("dailyLimitExceeded",
     "YouTube API günlük kotası aşıldı; kota sıfırlanınca tekrar deneyin."),
    ("rateLimitExceeded",
     "YouTube kısa vadeli hız limitine takıldı; birkaç dakika sonra tekrar deneyin."),
    ("forbidden",
     "YouTube isteği reddedildi (403); API anahtarı kısıtlamalarını kontrol edin."),
    ("unauthorized",
     "YouTube yetkilendirmesi geçersiz; API anahtarını kontrol edin."),
)


def _get(endpoint: str, params: dict) -> dict:
    """READ seviyesinde tek GET; hataları tek satır mesaja çevirir."""
    anahtar = secrets.get("YOUTUBE_API_KEY", required=True)
    try:
        return request_json("GET", f"{API}/{endpoint}", WORKER,
                            params={**params, "key": anahtar})
    except HttpError as exc:
        mesaj = " ".join(str(exc).split())  # tek satır
        for neden, aciklama in _HATA_ESLESMESI:
            if neden in mesaj:
                raise RuntimeError(aciklama) from exc
        raise RuntimeError(secrets.redact(mesaj)) from exc


def _sinir(limit: int) -> int:
    """YouTube maxResults 1..50 aralığı dışını kabul etmez."""
    return max(1, min(int(limit), MAKS_SONUC))


def _kaydet(kind: str, items: list[dict]) -> None:
    """Her sonucu SQLite'a yazar; özetleme agent katmanında kalır."""
    for item in items:
        store.save("youtube", kind, item.get("url"), item.get("title"),
                   json.dumps(item, ensure_ascii=False))


def search(query: str, limit: int = 10, tur: str = "video") -> list[dict]:
    """search.list — video, kanal veya oynatma listesi araması (READ)."""
    if tur not in _TURLER:
        raise ValueError(f"bilinmeyen arama türü: {tur} ({'|'.join(_TURLER)})")
    audit.log_event("youtube_search", WORKER, "READ", "auto",
                    {"query": query, "tur": tur, "limit": limit})
    data = _get("search", {"q": query, "type": tur, "part": "snippet",
                           "maxResults": _sinir(limit)})
    items = []
    for kayit in data.get("items", []):
        kimlik = (kayit.get("id") or {}).get(_ID_ALANLARI[tur])
        snippet = kayit.get("snippet") or {}
        items.append({
            "id": kimlik,
            "title": snippet.get("title"),
            "channel": snippet.get("channelTitle"),
            "publishedAt": snippet.get("publishedAt"),
            "url": _URL_KALIPLARI[tur].format(kimlik) if kimlik else None,
        })
    _kaydet(tur, items)
    return items


def video_detail(video_id: str) -> dict:
    """videos.list — tek videonun başlık, istatistik ve süresi (READ)."""
    audit.log_event("youtube_video", WORKER, "READ", "auto",
                    {"video": video_id})
    data = _get("videos", {"part": "snippet,statistics,contentDetails",
                           "id": video_id})
    items = data.get("items", [])
    if not items:
        return {}
    v = items[0]
    snippet = v.get("snippet") or {}
    istatistik = v.get("statistics") or {}
    satir = {
        "id": v.get("id"),
        "title": snippet.get("title"),
        "channel": snippet.get("channelTitle"),
        "publishedAt": snippet.get("publishedAt"),
        "duration": (v.get("contentDetails") or {}).get("duration"),
        "viewCount": istatistik.get("viewCount"),
        "likeCount": istatistik.get("likeCount"),
        "commentCount": istatistik.get("commentCount"),
        "url": f"https://www.youtube.com/watch?v={v.get('id')}",
    }
    _kaydet("video", [satir])
    return satir


def playlist_items(playlist_id: str, limit: int = 25) -> list[dict]:
    """playlistItems.list — oynatma listesindeki videolar (READ)."""
    audit.log_event("youtube_playlist", WORKER, "READ", "auto",
                    {"playlist": playlist_id, "limit": limit})
    data = _get("playlistItems",
                {"part": "snippet", "playlistId": playlist_id,
                 "maxResults": _sinir(limit)})
    items = []
    for kayit in data.get("items", []):
        snippet = kayit.get("snippet") or {}
        video_id = (snippet.get("resourceId") or {}).get("videoId")
        items.append({
            "videoId": video_id,
            "title": snippet.get("title"),
            "channel": snippet.get("channelTitle"),
            "position": snippet.get("position"),
            "publishedAt": snippet.get("publishedAt"),
            "url": (f"https://www.youtube.com/watch?v={video_id}"
                    if video_id else None),
        })
    _kaydet("playlist_video", items)
    return items
