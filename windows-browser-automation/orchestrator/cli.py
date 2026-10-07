"""Tek giriş noktası.

Kullanım (proje kökünden):
    python -m orchestrator.cli <komut> [seçenekler]
(paket kurulduysa kısaca: otomasyon <komut>)

Tüm komutlar policy + audit katmanından geçer. Dış etki yaratan komutlar
(gmail-gonder, vercel-iptal, linkedin-paylas) terminalde onay ister.

Yeni komut eklemek: aşağıya @command ile bir handler yaz — argparse tanımı
ve dispatch tablosu registry'den otomatik derlenir; ikinci bir yerde
(eski if/elif zinciri gibi) eşleme tutmak gerekmez.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any, Callable

from core import audit, secrets, store
from core.approval import ApprovalDenied

Handler = Callable[[argparse.Namespace], "int | None"]
ArgSpec = tuple[tuple[str, dict[str, Any]], ...]


@dataclass(frozen=True)
class Command:
    name: str
    help: str
    handler: Handler
    args: ArgSpec


_COMMANDS: list[Command] = []


def command(name: str, help: str, args: ArgSpec = ()):
    """Komut kaydedici: handler'ı registry'ye ekler."""
    def deco(fn: Handler) -> Handler:
        _COMMANDS.append(Command(name, help, fn, args))
        return fn
    return deco


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


# --- GitHub ---------------------------------------------------------------

@command("github-arastir", "GitHub repo araması",
         (("sorgu", {}), ("--limit", {"type": int, "default": 10})))
def _github_arastir(args):
    from workers import github_worker
    _print(github_worker.search_repos(args.sorgu, args.limit))


@command("github-issues", "Bir reponun issue listesi",
         (("repo", {"help": "ör. microsoft/playwright-cli"}),
          ("--state", {"default": "open"}),
          ("--limit", {"type": int, "default": 20})))
def _github_issues(args):
    from workers import github_worker
    _print(github_worker.repo_issues(args.repo, args.state, args.limit))


@command("github-pr", "Pull request aç (gh; onay ister)",
         (("--title", {"required": True}),
          ("--govde", {"default": ""}),
          ("--base", {"default": "main"}),
          ("--head", {"default": None}),
          ("--draft", {"action": "store_true"})))
def _github_pr(args):
    from workers import github_worker
    url = github_worker.create_pr(args.title, args.govde, args.base,
                                  args.head, draft=args.draft)
    print(f"PR açıldı: {url}")


# --- Gmail ----------------------------------------------------------------

@command("gmail-ara", "Gmail'de ara (READ)",
         (("sorgu", {"help": 'ör. "from:github.com is:unread"'}),
          ("--limit", {"type": int, "default": 10})))
def _gmail_ara(args):
    from workers import gmail_worker
    _print(gmail_worker.search(args.sorgu, args.limit))


@command("gmail-taslak", "E-posta taslağı oluştur (GÖNDERMEZ)",
         (("--to", {"required": True}),
          ("--konu", {"required": True}),
          ("--govde", {"required": True})))
def _gmail_taslak(args):
    from workers import gmail_worker
    draft_id = gmail_worker.create_draft(args.to, args.konu, args.govde)
    print(f"Taslak oluşturuldu: {draft_id}")
    print(f"Göndermek için: python -m orchestrator.cli gmail-gonder {draft_id}")


@command("gmail-gonder", "Taslağı GÖNDER (onay ister)", (("draft_id", {}),))
def _gmail_gonder(args):
    from workers import gmail_worker
    sent = gmail_worker.send_draft(args.draft_id)
    print(f"Gönderildi: {sent.get('id')}")


# --- X (Twitter) ----------------------------------------------------------

@command("x-bookmarks", "X yer işaretlerini çek (ÜCRETLİ API)",
         (("--limit", {"type": int, "default": 50}),))
def _x_bookmarks(args):
    from workers import x_bookmarks_worker
    items = x_bookmarks_worker.fetch_bookmarks(args.limit)
    print(f"{len(items)} yer işareti kaydedildi → data/results.db")


@command("x-token-yenile", "X OAuth2 access token yenile")
def _x_token_yenile(args):
    from workers import x_bookmarks_worker
    x_bookmarks_worker.refresh_access_token()


# --- LinkedIn -------------------------------------------------------------

@command("linkedin-profil", "Kendi LinkedIn profilin (READ)")
def _linkedin_profil(args):
    from workers import linkedin_worker
    _print(linkedin_worker.me())


@command("linkedin-paylas", "LinkedIn'de metin paylaş (SEND, onay ister)",
         (("--metin", {"required": True}),
          ("--gorunurluk", {"default": "PUBLIC",
                            "choices": ["PUBLIC", "CONNECTIONS"]})))
def _linkedin_paylas(args):
    from workers import linkedin_worker
    post_id = linkedin_worker.create_post(args.metin, args.gorunurluk)
    print(f"Paylaşıldı: {post_id}")


@command("linkedin-token-yenile", "LinkedIn OAuth2 access token yenile")
def _linkedin_token_yenile(args):
    from workers import linkedin_worker
    linkedin_worker.refresh_access_token()


@command("linkedin-akis", "Açık oturumdan akış oku (tarayıcı, CDP, READ)",
         (("--limit", {"type": int, "default": 20}),))
def _linkedin_akis(args):
    from workers import linkedin_browser
    _print(linkedin_browser.feed(args.limit))


@command("linkedin-ara", "Açık oturumda arama oku (tarayıcı, CDP, READ)",
         (("sorgu", {}),
          ("--tur", {"default": "people",
                     "choices": ["people", "posts", "jobs", "companies"]}),
          ("--limit", {"type": int, "default": 10})))
def _linkedin_ara(args):
    from workers import linkedin_browser
    _print(linkedin_browser.search(args.sorgu, args.limit, args.tur))


# --- Canva ----------------------------------------------------------------

@command("canva-export", "Canva tasarımını dışa aktar",
         (("design_id", {}),
          ("--format", {"default": "pdf",
                        "choices": ["pdf", "jpg", "png", "gif", "pptx", "mp4"]})))
def _canva_export(args):
    from workers import canva_worker
    for path in canva_worker.export_design(args.design_id, args.format):
        print(path)


# --- Supabase / Vercel ----------------------------------------------------

@command("supabase-sorgu", "PostgREST salt-okunur sorgu",
         (("tablo", {}),
          ("--select", {"default": "*"}),
          ("--limit", {"type": int, "default": 20})))
def _supabase_sorgu(args):
    from workers import supabase_worker
    _print(supabase_worker.query_table(args.tablo, args.select, args.limit))


@command("vercel-durum", "Son deployment'lar",
         (("--app", {}), ("--limit", {"type": int, "default": 10})))
def _vercel_durum(args):
    from workers import vercel_worker
    _print(vercel_worker.list_deployments(args.app, args.limit))


@command("vercel-log", "Deployment build olayları", (("deployment_id", {}),))
def _vercel_log(args):
    from workers import vercel_worker
    _print(vercel_worker.deployment_events(args.deployment_id))


@command("vercel-iptal", "Deployment iptal (onay ister)",
         (("deployment_id", {}),))
def _vercel_iptal(args):
    from workers import vercel_worker
    _print(vercel_worker.cancel_deployment(args.deployment_id))


# --- Yerel ----------------------------------------------------------------

@command("son-kayitlar", "Sonuç deposundaki son kayıtlar",
         (("--kaynak", {"default": None}),
          ("--limit", {"type": int, "default": 20})))
def _son_kayitlar(args):
    for row in store.recent(args.kaynak, args.limit):
        print(" | ".join(str(x) for x in row))


@command("audit-dogrula", "Audit hash zincirini doğrula")
def _audit_dogrula(args):
    ok, msg = audit.verify_chain()
    print(("SAĞLAM — " if ok else "BOZUK — ") + msg)
    return 0 if ok else 1


# --- Derleme + çalıştırma -------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="otomasyon",
        description="API-öncelikli araştırma otomasyonu (onay + audit katmanlı)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    for cmd in _COMMANDS:
        s = sub.add_parser(cmd.name, help=cmd.help)
        for arg_name, kwargs in cmd.args:
            s.add_argument(arg_name, **kwargs)
    return p


def dispatch(args: argparse.Namespace) -> int:
    for cmd in _COMMANDS:
        if cmd.name == args.cmd:
            return cmd.handler(args) or 0
    return 2  # argparse required=True yakalar; burası savunma amaçlı


def main(argv: list[str] | None = None) -> int:
    secrets.load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args)
    except ApprovalDenied as exc:
        print(f"\nİşlem iptal edildi: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
