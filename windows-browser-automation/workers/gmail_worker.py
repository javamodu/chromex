"""Gmail worker'ı (resmi Gmail API).

Kurulum (bir kez):
1) console.cloud.google.com → proje aç → Gmail API'yi etkinleştir.
2) OAuth consent screen → Desktop app credential oluştur → credentials.json
   olarak proje köküne kaydet.
3) İlk `gmail-ara` çağrısında tarayıcı açılır, izin verilir; token.json
   otomatik oluşur ve sonraki çağrılarda yenilenir.

Seviyeler: arama/okuma READ, taslak DRAFT (otomatik ama audit'li),
gönderme SEND (her zaman kullanıcı onayı ister).
"""
from __future__ import annotations

import base64
import os
from email.message import EmailMessage
from pathlib import Path

from core import store
from policygate import ActionRequest, audit, require

WORKER = "gmail"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
]


def _cred_file() -> Path:
    return Path(os.environ.get("GMAIL_CREDENTIALS", "credentials.json"))


def _token_file() -> Path:
    return Path(os.environ.get("GMAIL_TOKEN", "token.json"))


def _service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if _token_file().exists():
        creds = Credentials.from_authorized_user_file(str(_token_file()), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not _cred_file().exists():
                raise RuntimeError(
                    "credentials.json bulunamadı — README'deki Gmail OAuth "
                    "adımlarını izleyin."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(_cred_file()), SCOPES)
            creds = flow.run_local_server(port=0)
        _token_file().write_text(creds.to_json(), encoding="utf-8")
    return build("gmail", "v1", credentials=creds)


def search(query: str, limit: int = 10) -> list[dict]:
    audit.log_event("gmail_search", WORKER, "READ", "auto",
                    {"query": query, "limit": limit})
    svc = _service()
    resp = svc.users().messages().list(
        userId="me", q=query, maxResults=limit).execute()
    out: list[dict] = []
    for m in resp.get("messages", []):
        msg = svc.users().messages().get(
            userId="me", id=m["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]).execute()
        headers = {h["name"]: h["value"]
                   for h in msg.get("payload", {}).get("headers", [])}
        item = {
            "id": m["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "snippet": msg.get("snippet", ""),
        }
        out.append(item)
        store.save("gmail", "message", m["id"], item["subject"], item["snippet"])
    return out


def create_draft(to: str, subject: str, body: str) -> str:
    """Taslak oluşturur; GÖNDERMEZ. DRAFT seviyesi: otomatik + audit."""
    audit.log_event("gmail_create_draft", WORKER, "DRAFT", "auto",
                    {"to": to, "subject": subject})
    svc = _service()
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = svc.users().drafts().create(
        userId="me", body={"message": {"raw": raw}}).execute()
    return draft["id"]


def send_draft(draft_id: str) -> dict:
    """Taslağı gönderir — SEND seviyesi, alıcı/konu gösterilip ONAY istenir."""
    svc = _service()
    draft = svc.users().drafts().get(
        userId="me", id=draft_id, format="full").execute()
    payload = draft.get("message", {}).get("payload", {})
    headers = {h["name"]: h["value"] for h in payload.get("headers", [])}
    require(ActionRequest(
        worker=WORKER,
        action="gmail.send_draft",
        level="SEND",
        summary="Gmail taslağı GÖNDERİLECEK — alıcı ve konuyu kontrol edin.",
        details={
            "draft_id": draft_id,
            "to": headers.get("To", "(boş)"),
            "subject": headers.get("Subject", "(boş)"),
            "önizleme": draft.get("message", {}).get("snippet", ""),
        },
    ))
    sent = svc.users().drafts().send(userId="me", body={"id": draft_id}).execute()
    audit.log_event("gmail_sent", WORKER, "SEND", "done",
                    {"message_id": sent.get("id")})
    return sent
