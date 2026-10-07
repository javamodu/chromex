"""Tek giriş noktası.

Kullanım (proje kökünden):
    python -m orchestrator.cli <komut> [seçenekler]

Tüm komutlar policy + audit katmanından geçer. Dış etki yaratan komutlar
(gmail-gonder, vercel-iptal, supabase mutasyonları) terminalde onay ister.
"""
from __future__ import annotations

import argparse
import json

from core import audit, secrets, store
from core.approval import ApprovalDenied


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="otomasyon",
        description="API-öncelikli araştırma otomasyonu (onay + audit katmanlı)",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("github-arastir", help="GitHub repo araması")
    s.add_argument("sorgu")
    s.add_argument("--limit", type=int, default=10)

    s = sub.add_parser("github-issues", help="Bir reponun issue listesi")
    s.add_argument("repo", help="ör. microsoft/playwright-cli")
    s.add_argument("--state", default="open")
    s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("github-pr", help="Pull request aç (gh; onay ister)")
    s.add_argument("--title", required=True)
    s.add_argument("--govde", default="")
    s.add_argument("--base", default="main")
    s.add_argument("--head", default=None)
    s.add_argument("--draft", action="store_true")

    s = sub.add_parser("gmail-ara", help="Gmail'de ara (READ)")
    s.add_argument("sorgu", help='ör. "from:github.com is:unread"')
    s.add_argument("--limit", type=int, default=10)

    s = sub.add_parser("gmail-taslak", help="E-posta taslağı oluştur (GÖNDERMEZ)")
    s.add_argument("--to", required=True)
    s.add_argument("--konu", required=True)
    s.add_argument("--govde", required=True)

    s = sub.add_parser("gmail-gonder", help="Taslağı GÖNDER (onay ister)")
    s.add_argument("draft_id")

    s = sub.add_parser("x-bookmarks", help="X yer işaretlerini çek (ÜCRETLİ API)")
    s.add_argument("--limit", type=int, default=50)

    sub.add_parser("x-token-yenile", help="X OAuth2 access token yenile")

    sub.add_parser("linkedin-profil", help="Kendi LinkedIn profilin (READ)")

    s = sub.add_parser("linkedin-paylas",
                       help="LinkedIn'de metin paylaş (SEND, onay ister)")
    s.add_argument("--metin", required=True)
    s.add_argument("--gorunurluk", default="PUBLIC",
                   choices=["PUBLIC", "CONNECTIONS"])

    sub.add_parser("linkedin-token-yenile",
                   help="LinkedIn OAuth2 access token yenile")

    s = sub.add_parser("linkedin-akis",
                       help="Açık oturumdan akış oku (tarayıcı, CDP, READ)")
    s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("linkedin-ara",
                       help="Açık oturumda arama oku (tarayıcı, CDP, READ)")
    s.add_argument("sorgu")
    s.add_argument("--tur", default="people",
                   choices=["people", "posts", "jobs", "companies"])
    s.add_argument("--limit", type=int, default=10)

    s = sub.add_parser("canva-export", help="Canva tasarımını dışa aktar")
    s.add_argument("design_id")
    s.add_argument("--format", default="pdf",
                   choices=["pdf", "jpg", "png", "gif", "pptx", "mp4"])

    s = sub.add_parser("supabase-sorgu", help="PostgREST salt-okunur sorgu")
    s.add_argument("tablo")
    s.add_argument("--select", default="*")
    s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("vercel-durum", help="Son deployment'lar")
    s.add_argument("--app")
    s.add_argument("--limit", type=int, default=10)

    s = sub.add_parser("vercel-log", help="Deployment build olayları")
    s.add_argument("deployment_id")

    s = sub.add_parser("vercel-iptal", help="Deployment iptal (onay ister)")
    s.add_argument("deployment_id")

    s = sub.add_parser("son-kayitlar", help="Sonuç deposundaki son kayıtlar")
    s.add_argument("--kaynak", default=None)
    s.add_argument("--limit", type=int, default=20)

    sub.add_parser("audit-dogrula", help="Audit hash zincirini doğrula")

    return p


def dispatch(args: argparse.Namespace) -> int:
    if args.cmd == "github-arastir":
        from workers import github_worker
        _print(github_worker.search_repos(args.sorgu, args.limit))

    elif args.cmd == "github-issues":
        from workers import github_worker
        _print(github_worker.repo_issues(args.repo, args.state, args.limit))

    elif args.cmd == "github-pr":
        from workers import github_worker
        url = github_worker.create_pr(args.title, args.govde, args.base,
                                      args.head, draft=args.draft)
        print(f"PR açıldı: {url}")

    elif args.cmd == "gmail-ara":
        from workers import gmail_worker
        _print(gmail_worker.search(args.sorgu, args.limit))

    elif args.cmd == "gmail-taslak":
        from workers import gmail_worker
        draft_id = gmail_worker.create_draft(args.to, args.konu, args.govde)
        print(f"Taslak oluşturuldu: {draft_id}")
        print(f"Göndermek için: python -m orchestrator.cli gmail-gonder {draft_id}")

    elif args.cmd == "gmail-gonder":
        from workers import gmail_worker
        sent = gmail_worker.send_draft(args.draft_id)
        print(f"Gönderildi: {sent.get('id')}")

    elif args.cmd == "x-bookmarks":
        from workers import x_bookmarks_worker
        items = x_bookmarks_worker.fetch_bookmarks(args.limit)
        print(f"{len(items)} yer işareti kaydedildi → data/results.db")

    elif args.cmd == "x-token-yenile":
        from workers import x_bookmarks_worker
        x_bookmarks_worker.refresh_access_token()

    elif args.cmd == "linkedin-profil":
        from workers import linkedin_worker
        _print(linkedin_worker.me())

    elif args.cmd == "linkedin-paylas":
        from workers import linkedin_worker
        post_id = linkedin_worker.create_post(args.metin, args.gorunurluk)
        print(f"Paylaşıldı: {post_id}")

    elif args.cmd == "linkedin-token-yenile":
        from workers import linkedin_worker
        linkedin_worker.refresh_access_token()

    elif args.cmd == "linkedin-akis":
        from workers import linkedin_browser
        _print(linkedin_browser.feed(args.limit))

    elif args.cmd == "linkedin-ara":
        from workers import linkedin_browser
        _print(linkedin_browser.search(args.sorgu, args.limit, args.tur))

    elif args.cmd == "canva-export":
        from workers import canva_worker
        for path in canva_worker.export_design(args.design_id, args.format):
            print(path)

    elif args.cmd == "supabase-sorgu":
        from workers import supabase_worker
        _print(supabase_worker.query_table(args.tablo, args.select, args.limit))

    elif args.cmd == "vercel-durum":
        from workers import vercel_worker
        _print(vercel_worker.list_deployments(args.app, args.limit))

    elif args.cmd == "vercel-log":
        from workers import vercel_worker
        _print(vercel_worker.deployment_events(args.deployment_id))

    elif args.cmd == "vercel-iptal":
        from workers import vercel_worker
        _print(vercel_worker.cancel_deployment(args.deployment_id))

    elif args.cmd == "son-kayitlar":
        for row in store.recent(args.kaynak, args.limit):
            print(" | ".join(str(x) for x in row))

    elif args.cmd == "audit-dogrula":
        ok, msg = audit.verify_chain()
        print(("SAĞLAM — " if ok else "BOZUK — ") + msg)
        return 0 if ok else 1

    return 0


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
