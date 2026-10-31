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
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from core import kasa, site_guvenlik, store
from policygate import ActionRequest, ApprovalDenied, audit, require, secrets

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


def get_commands() -> tuple[Command, ...]:
    """Kamu CLI komut kayıt tablosu (MCP adaptörü gibi tüketiciler için)."""
    return tuple(_COMMANDS)


def _print(obj) -> None:
    if isinstance(obj, (list, dict)) and not obj:
        print("(sonuç bulunamadı)")  # ham "[]"/"{}" hata sanılıyor
        return
    text = json.dumps(obj, ensure_ascii=False, indent=2, default=str)
    try:
        print(text)
    except UnicodeEncodeError:
        # cp1252 gibi sınırlı konsollar: ASCII-kaçışlı çıktıya düş
        print(json.dumps(obj, ensure_ascii=True, indent=2, default=str))


# --- GitHub ---------------------------------------------------------------

@command("github-arastir", "GitHub repo araması",
         (("sorgu", {"help": 'ör. "language:python otomasyon"'}),
          ("--limit", {"type": int, "default": 10, "help": "en fazla kayıt"})))
def _github_arastir(args):
    from workers import github_worker
    _print(github_worker.search_repos(args.sorgu, args.limit))


@command("github-issues", "Bir reponun issue listesi",
         (("repo", {"help": "ör. microsoft/playwright-cli"}),
          ("--state", {"default": "open", "help": "open | closed | all"}),
          ("--limit", {"type": int, "default": 20, "help": "en fazla kayıt"})))
def _github_issues(args):
    from workers import github_worker
    _print(github_worker.repo_issues(args.repo, args.state, args.limit))


@command("github-pr", "Pull request aç (gh; onay ister)",
         (("--title", {"required": True, "help": "PR başlığı"}),
          ("--govde", {"default": "", "help": "PR açıklaması (markdown)"}),
          ("--base", {"default": "main", "help": "hedef dal"}),
          ("--head", {"default": None, "help": "kaynak dal (boş: mevcut dal)"}),
          ("--draft", {"action": "store_true", "help": "taslak PR olarak aç"})))
def _github_pr(args):
    from workers import github_worker
    url = github_worker.create_pr(args.title, args.govde, args.base,
                                  args.head, draft=args.draft)
    print(f"PR açıldı: {url}")


# --- Gmail ----------------------------------------------------------------

@command("gmail-ara", "Gmail'de ara (READ)",
         (("sorgu", {"help": 'ör. "from:github.com is:unread"'}),
          ("--limit", {"type": int, "default": 10, "help": "en fazla kayıt"})))
def _gmail_ara(args):
    from workers import gmail_worker
    _print(gmail_worker.search(args.sorgu, args.limit))


@command("gmail-taslak", "E-posta taslağı oluştur (GÖNDERMEZ)",
         (("--to", {"required": True, "help": "alıcı e-posta adresi"}),
          ("--konu", {"required": True, "help": "e-posta konusu"}),
          ("--govde", {"required": True, "help": "e-posta gövdesi"})))
def _gmail_taslak(args):
    from workers import gmail_worker
    draft_id = gmail_worker.create_draft(args.to, args.konu, args.govde)
    print(f"Taslak oluşturuldu: {draft_id}")
    print(f"Göndermek için: python -m orchestrator.cli gmail-gonder {draft_id}")


@command("gmail-gonder", "Taslağı GÖNDER (onay ister)", (("draft_id", {"help": "taslak kimliği (gmail-taslak çıktısı)"}),))
def _gmail_gonder(args):
    from workers import gmail_worker
    sent = gmail_worker.send_draft(args.draft_id)
    print(f"Gönderildi: {sent.get('id')}")


# --- X (Twitter) ----------------------------------------------------------

@command("x-bookmarks", "X yer işaretlerini çek (ÜCRETLİ API)",
         (("--limit", {"type": int, "default": 50, "help": "en fazla kayıt"}),))
def _x_bookmarks(args):
    from workers import x_bookmarks_worker
    items = x_bookmarks_worker.fetch_bookmarks(args.limit)
    print(f"{len(items)} yer işareti kaydedildi -> data/results.db")


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
         (("--metin", {"required": True, "help": "paylaşılacak metin"}),
          ("--gorunurluk", {"default": "PUBLIC", "help": "kimler görsün",
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
         (("--limit", {"type": int, "default": 20, "help": "en fazla kayıt"}),))
def _linkedin_akis(args):
    from workers import linkedin_browser
    _print(linkedin_browser.feed(args.limit))


@command("linkedin-ara", "Açık oturumda arama oku (tarayıcı, CDP, READ)",
         (("sorgu", {"help": "arama ifadesi"}),
          ("--tur", {"default": "people", "help": "arama türü",
                     "choices": ["people", "posts", "jobs", "companies"]}),
          ("--limit", {"type": int, "default": 10, "help": "en fazla kayıt"})))
def _linkedin_ara(args):
    from workers import linkedin_browser
    _print(linkedin_browser.search(args.sorgu, args.limit, args.tur))


# --- Canva ----------------------------------------------------------------

@command("canva-export", "Canva tasarımını dışa aktar",
         (("design_id", {"help": "Canva tasarım kimliği"}),
          ("--format", {"default": "pdf", "help": "dışa aktarma biçimi",
                        "choices": ["pdf", "jpg", "png", "gif", "pptx", "mp4"]})))
def _canva_export(args):
    from workers import canva_worker
    for path in canva_worker.export_design(args.design_id, args.format):
        print(path)


# --- Supabase / Vercel ----------------------------------------------------

@command("supabase-sorgu", "PostgREST salt-okunur sorgu",
         (("tablo", {"help": "tablo adı"}),
          ("--select", {"default": "*", "help": "sütun listesi (PostgREST)"}),
          ("--limit", {"type": int, "default": 20, "help": "en fazla kayıt"})))
def _supabase_sorgu(args):
    from workers import supabase_worker
    _print(supabase_worker.query_table(args.tablo, args.select, args.limit))


@command("vercel-durum", "Son deployment'lar",
         (("--app", {"help": "uygulama adı filtresi"}),
          ("--limit", {"type": int, "default": 10, "help": "en fazla kayıt"})))
def _vercel_durum(args):
    from workers import vercel_worker
    _print(vercel_worker.list_deployments(args.app, args.limit))


@command("vercel-log", "Deployment build olayları", (("deployment_id", {"help": "deployment kimliği (dpl_...)"}),))
def _vercel_log(args):
    from workers import vercel_worker
    _print(vercel_worker.deployment_events(args.deployment_id))


@command("vercel-iptal", "Deployment iptal (onay ister)",
         (("deployment_id", {"help": "deployment kimliği (dpl_...)"}),))
def _vercel_iptal(args):
    from workers import vercel_worker
    _print(vercel_worker.cancel_deployment(args.deployment_id))


# --- YouTube ----------------------------------------------------------------

@command("youtube-arastir", "YouTube araması (READ)",
         (("sorgu", {"help": 'ör. "chromex otomasyon"'}),
          ("--limit", {"type": int, "default": 10, "help": "en fazla kayıt (1-50)"}),
          ("--tur", {"default": None, "help": "arama türü",
                     "choices": ["video", "channel", "playlist"]})))
def _youtube_arastir(args):
    from workers import youtube_worker
    _print(youtube_worker.search(args.sorgu, args.limit, args.tur or "video"))


@command("youtube-detay", "Video detayı: istatistikler + süre (READ)",
         (("video_id", {"help": "11 karakterli YouTube video kimliği"}),))
def _youtube_detay(args):
    from workers import youtube_worker
    _print(youtube_worker.video_detail(args.video_id))


@command("youtube-oynatma-listesi", "Oynatma listesi videoları (READ)",
         (("liste_id", {"help": "oynatma listesi kimliği (PL...)"}),
          ("--limit", {"type": int, "default": 25, "help": "en fazla kayıt (1-50)"})))
def _youtube_oynatma_listesi(args):
    from workers import youtube_worker
    _print(youtube_worker.playlist_items(args.liste_id, args.limit))


# --- Secret kasası --------------------------------------------------------

@command("secret-kur", "Secret'ları DPAPI kasasına etkileşimli yaz",
         (("anahtarlar", {"nargs": "*", "default": [],
                          "help": "yazılacak anahtar adları (adaylar: .env.example)"}),))
def _secret_kur(args):
    import getpass

    if not args.anahtarlar:
        print("Anahtar ad(lar)ı gerekli. Örnek: "
              "python -m orchestrator.cli secret-kur GITHUB_TOKEN")
        return 2
    mevcut: dict[str, str] = {}
    try:
        mevcut = kasa.oku()
    except kasa.KasaHatasi as exc:
        if kasa.kasa_yolu().exists():
            print(f"Uyarı: {exc} — kasa sıfırlanarak yeniden kurulacak.")
    for ad in args.anahtarlar:
        try:
            deger = getpass.getpass(f"{ad} değeri (boş bırak = atla): ")
        except EOFError:
            print("Etkileşimli terminal gerekli — secret-kur'u elle çalıştırın.")
            return 1
        if deger.strip():
            mevcut[ad] = deger.strip()
    kasa.yaz(mevcut)
    audit.log_event("secret_kur", kasa.WORKER, "MODIFY", "done",
                    {"anahtarlar": sorted(mevcut)})
    print(f"Kasa güncellendi: {kasa.kasa_yolu()} — {len(mevcut)} anahtar "
          "(değerler terminale basılmaz).")
    return 0


@command("secret-dogrula", "Secret kasası ve kurulum doğrulaması",
         (("--gerekli", {"nargs": "*", "default": [],
                         "help": "zorunlu anahtar adları"}),))
def _secret_dogrula(args):
    yol = kasa.kasa_yolu()
    if not yol.exists():
        print(f"Kasa yok: {yol} — önce secret-kur çalıştırın.")
        return 1
    try:
        degerler = kasa.oku()
    except kasa.KasaHatasi as exc:
        print(f"BOZUK — {exc}")
        return 1
    if not degerler:
        print(f"Kasa boş: {yol} — secret-kur ile anahtar ekleyin.")
        return 1
    for ad in sorted(degerler):
        print(f"{ad}: {len(degerler[ad])} karakter — çözüldü")
    eksik = [ad for ad in args.gerekli if ad not in degerler]
    if eksik:
        print(f"Eksik zorunlu anahtarlar: {', '.join(sorted(eksik))}")
        return 1
    if Path(".env").exists():
        print("Uyarı: düz metin .env hâlâ duruyor — secret-tasi ile kasaya "
              "taşıyın.")
    audit.log_event("secret_dogrula", kasa.WORKER, "READ", "auto",
                    {"anahtar_sayisi": len(degerler)})
    print("SECRET_DOGRULA_OK")
    return 0


@command("secret-tasi", "Düz metin .env değerlerini kasaya taşı, dosyayı SİL (onay ister)",
         (("--dosya", {"default": ".env", "help": "taşınacak düz metin dosya"}),))
def _secret_tasi(args):
    yol = Path(args.dosya)
    if not yol.exists():
        print(f"Dosya yok: {yol}")
        return 1
    degerler = kasa.duz_oku(yol)
    if not degerler:
        print(f"{yol} içinde taşınacak dolu anahtar yok.")
        return 1
    try:
        birlesik = {**kasa.oku(), **degerler}
    except kasa.KasaHatasi as exc:
        print(f"Hata: hedef kasa okunamıyor — {exc}")
        return 1
    require(ActionRequest(
        worker=kasa.WORKER, action="kasa.duz_dosya_sil", level="DELETE",
        summary=f"{yol} içindeki {len(degerler)} değer kasaya taşındıktan "
                "sonra düz metin dosya SİLİNECEK.",
        details={"dosya": str(yol), "taşınan_anahtarlar": sorted(degerler)},
    ))
    kasa.yaz(birlesik)
    kasa.oku()  # geri okuma: taşınan değerler gerçekten çözülüyor (kanıt)
    yol.unlink()
    audit.log_event("secret_tasi", kasa.WORKER, "DELETE", "done",
                    {"dosya": str(yol), "anahtarlar": sorted(degerler)})
    print(f"{len(degerler)} anahtar kasaya taşındı; {yol} silindi.")
    return 0


# --- Site güvenliği --------------------------------------------------------

@command("site-kesfet", "Site güvenlik profilini, limitleri ve pilot planını göster",
         (("site", {"nargs": "?", "default": None,
                    "help": "site adı (ör. linkedin, x, youtube, chatgpt)"}),
          ("--pilot", {"action": "store_true",
                       "help": "pilot adımını simüle et (ağ çağrısı yapılmaz)"}),
          ("--eylem", {"choices": ["okuma", "yazma", "gonderme"],
                       "default": "okuma", "help": "pilot eylemi"}),
          ("--adim", {"type": int, "default": 1,
                      "help": "pilot adım sayısı"})))
def _site_kesfet(args):
    if args.site is None:
        _print(site_guvenlik.kesfet())
        return 0
    if args.pilot:
        sonuc = site_guvenlik.pilot(args.site, args.eylem, args.adim)
        _print(sonuc)
        return 0 if sonuc["izinli"] else 1
    _print(site_guvenlik.kesfet(args.site))
    return 0


# --- Yerel ----------------------------------------------------------------

@command("son-kayitlar", "Sonuç deposundaki son kayıtlar",
         (("--kaynak", {"default": None, "help": "kaynak filtresi (ör. github, x)"}),
          ("--limit", {"type": int, "default": 20, "help": "en fazla kayıt"})))
def _son_kayitlar(args):
    for row in store.recent(args.kaynak, args.limit):
        print(" | ".join(str(x) for x in row))


@command("audit-dogrula", "Audit hash zincirini doğrula")
def _audit_dogrula(args):
    ok, msg = audit.verify_chain()
    print(("SAĞLAM — " if ok else "BOZUK — ") + msg)
    return 0 if ok else 1


@command("zamanla", "Dosyadaki işi tek seferlik çalıştır",
         (("--dosya", {"required": True, "help": "JSON iş tanımı"}),))
def _zamanla(args):
    from workers import scheduler
    return scheduler.run_job(args.dosya)


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
            harita = site_guvenlik.komut_haritasi(args.cmd)
            if harita is not None:
                site, eylem = harita
                sonuc = site_guvenlik.kontrol_et(site, eylem)
                if not sonuc["izinli"]:
                    print(f"Hata: {sonuc['mesaj']}")
                    return 1
            return cmd.handler(args) or 0
    return 2  # argparse required=True yakalar; burası savunma amaçlı


def main(argv: list[str] | None = None) -> int:
    # cp1252 gibi sınırlı kod sayfalı konsollarda Türkçe çıktı çökmesin
    # (AGENTS.md kuralı): kodlama değişmez, yazım hatası '?' katlanmasına döner.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    # Kasa değerleri env'e setdefault ile girer: öncelik süreç env > kasa > .env.
    # Bozuk kasa süreci çökertmez (fail-closed) ama tek satır uyarıyla görünür.
    kasa_hatasi = kasa.yukle_env()
    if kasa_hatasi:
        print(f"Uyarı: {kasa_hatasi} — kasayı yoksayıyorum.")
    secrets.load_dotenv()
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args)
    except ApprovalDenied as exc:
        print(f"\nİşlem iptal edildi: {exc}")
        return 3  # kullanici/politika reddi: argparse usage hatasindan (2) ayrik
    except KeyboardInterrupt:
        print("\nİptal edildi (Ctrl+C).")
        return 130
    except Exception as exc:
        # İş hataları (env eksik, CDP kapalı, HTTP 4xx, eksik modül) zaten
        # yönlendirici mesaj taşır; traceback yalnızca CHROMEX_DEBUG ile.
        if os.environ.get("CHROMEX_DEBUG"):
            traceback.print_exc()
        else:
            print(f"\nHata: {exc}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
