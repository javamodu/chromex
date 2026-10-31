"""workers/youtube_worker.py + CLI + MCP şema testleri — tamamen OFFLINE.

Ağ ve gerçek API anahtarı gerekmez; request_json mock'lanır. Kapsam:
- arama: alan eşleme, tür doğrulaması, limit kırpması, SQLite kaydı
- detay: istatistik eşleme, boş yanıt (video yok -> boş dict)
- oynatma listesi: video listesi eşleme
- hata sunumu: kota ve anahtar hataları tek satır, secret'sız mesaja döner
- redaksiyon: anahtar istekte var, audit ve hata yüzeyinde yok
- audit: youtube olayları zincire girer, zincir sağlam kalır
- MCP şema: üç tool kayıtlı, zorunlu alanlar ve CLI eşleşmesi
  (CLI/MCP kaydı ana ajanda entegre edilene dek bu testler atlanır)

Çalıştırma (windows-browser-automation kökünden):
python -m unittest discover -s tests -p test_youtube_worker.py
"""
from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from core import store
from core.http import HttpError
from policygate import audit, secrets

_ARAMA_YANITI = {"items": [{
    "id": {"videoId": "vid1"},
    "snippet": {"title": "Başlık", "channelTitle": "Kanal",
                "publishedAt": "2026-01-02T03:04:05Z"},
}]}

_DETAY_YANITI = {"items": [{
    "id": "vid1",
    "snippet": {"title": "Başlık", "channelTitle": "Kanal",
                "publishedAt": "2026-01-02T03:04:05Z"},
    "statistics": {"viewCount": "7", "likeCount": "5", "commentCount": "2"},
    "contentDetails": {"duration": "PT1M30S"},
}]}

_LISTE_YANITI = {"items": [{
    "snippet": {"title": "Video", "channelTitle": "Sahip",
                "resourceId": {"videoId": "vid1"}, "position": 0},
}]}


class YouTubeWorkerTestCase(unittest.TestCase):
    """Her teste izole tmp dizin: audit/store/policy + cwd (göreli yazımlar)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["STORE_DB"] = str(Path(self.tmp.name) / "results.db")
        os.environ["POLICY_FILE"] = str(Path(self.tmp.name) / "yok.json")
        os.environ["YOUTUBE_API_KEY"] = "test-youtube_api_key"
        self._cwd = os.getcwd()
        os.chdir(self.tmp.name)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "STORE_DB", "POLICY_FILE",
                    "YOUTUBE_API_KEY"):
            os.environ.pop(key, None)
        # redaksiyon kaydından test değerini temizle (test bağımsızlığı)
        secrets._REGISTERED.discard("test-youtube_api_key")


class YouTubeSearchTests(YouTubeWorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import youtube_worker
        self.worker = youtube_worker

    def test_search_alanlari_esler_ve_kaydeder(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value=_ARAMA_YANITI):
            videolar = self.worker.search("python", 5)
        self.assertEqual(videolar[0]["id"], "vid1")
        self.assertEqual(videolar[0]["title"], "Başlık")
        self.assertEqual(videolar[0]["url"],
                         "https://www.youtube.com/watch?v=vid1")
        self.assertEqual(len(store.recent("youtube", 5)), 1)

    def test_search_bos_yanit_bos_liste(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value={"items": []}):
            self.assertEqual(self.worker.search("yok"), [])

    def test_search_limit_50_tavanina_kirpilir(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value={"items": []}) as req:
            self.worker.search("x", 500)
        self.assertEqual(
            req.call_args.kwargs["params"]["maxResults"], 50)

    def test_search_gecersiz_tur_ag_cagirmaz(self):
        with mock.patch.object(self.worker, "request_json") as req:
            with self.assertRaises(ValueError):
                self.worker.search("x", tur="yok")
        req.assert_not_called()

    def test_arama_params_anahtar_icerir(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value={"items": []}) as req:
            self.worker.search("x")
        self.assertEqual(req.call_args.kwargs["params"]["q"], "x")
        self.assertEqual(req.call_args.kwargs["params"]["type"], "video")
        self.assertEqual(req.call_args.kwargs["params"]["key"],
                         "test-youtube_api_key")


class YouTubeDetailTests(YouTubeWorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import youtube_worker
        self.worker = youtube_worker

    def test_detay_alanlari_esler(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value=_DETAY_YANITI):
            detay = self.worker.video_detail("vid1")
        self.assertEqual(detay["viewCount"], "7")
        self.assertEqual(detay["duration"], "PT1M30S")
        self.assertEqual(len(store.recent("youtube", 5)), 1)

    def test_detay_bos_yanit_bos_dict(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value={"items": []}):
            self.assertEqual(self.worker.video_detail("yok"), {})


class YouTubePlaylistTests(YouTubeWorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import youtube_worker
        self.worker = youtube_worker

    def test_playlist_video_alanlari_esler(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value=_LISTE_YANITI):
            videolar = self.worker.playlist_items("pl1")
        self.assertEqual(videolar[0]["videoId"], "vid1")
        self.assertEqual(videolar[0]["title"], "Video")
        self.assertEqual(len(store.recent("youtube", 5)), 1)


class YouTubeHataTests(YouTubeWorkerTestCase):
    """Kota/anahtar hataları tek satır, secret'sız kullanıcı mesajına döner."""

    def setUp(self) -> None:
        super().setUp()
        from workers import youtube_worker
        self.worker = youtube_worker

    def test_kota_hatasi_tek_satir_mesaj(self):
        hata = HttpError(
            'GET https://www.googleapis.com/youtube/v3/search -> 403: '
            '{"error": {"errors": [{"reason": "quotaExceeded"}]}}')
        with mock.patch.object(self.worker, "request_json",
                               side_effect=hata):
            with self.assertRaises(RuntimeError) as ctx:
                self.worker.search("x")
        mesaj = str(ctx.exception)
        self.assertIn("kota", mesaj.lower())
        self.assertNotIn("quotaExceeded", mesaj)  # ham gövde sızmadı
        self.assertNotIn("\n", mesaj)

    def test_anahtar_hatasi_mesaji(self):
        hata = HttpError(
            'GET https://www.googleapis.com/youtube/v3/search -> 400: '
            '{"error": {"errors": [{"reason": "keyInvalid"}]}}')
        with mock.patch.object(self.worker, "request_json",
                               side_effect=hata):
            with self.assertRaises(RuntimeError) as ctx:
                self.worker.search("x")
        self.assertIn("YOUTUBE_API_KEY", str(ctx.exception))

    def test_genel_http_hatasi_redakte_gecer(self):
        hata = HttpError(
            "GET https://www.googleapis.com/youtube/v3/search -> 500: "
            "sunucu hatasi test-youtube_api_key")
        with mock.patch.object(self.worker, "request_json",
                               side_effect=hata):
            with self.assertRaises(RuntimeError) as ctx:
                self.worker.search("x")
        mesaj = str(ctx.exception)
        self.assertNotIn("test-youtube_api_key", mesaj)
        self.assertIn("***", mesaj)

    def test_anahtar_eksik_yonlendirici_hata(self):
        os.environ.pop("YOUTUBE_API_KEY", None)
        with mock.patch.object(self.worker, "request_json") as req:
            with self.assertRaises(RuntimeError) as ctx:
                self.worker.search("x")
        self.assertIn("YOUTUBE_API_KEY", str(ctx.exception))
        req.assert_not_called()


class YouTubeAuditRedaksiyonTests(YouTubeWorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import youtube_worker
        self.worker = youtube_worker

    def test_anahtar_audit_yuzeyinde_gizli_kalir(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value={"items": []}):
            self.worker.search("gizli-olmayan-sorgu")
        icerik = audit._audit_file().read_text(encoding="utf-8")
        self.assertIn("youtube_search", icerik)  # olay zincire girdi
        self.assertIn("gizli-olmayan-sorgu", icerik)  # sorgu audit'te durur
        self.assertNotIn("test-youtube_api_key", icerik)  # anahtar durmaz
        self.assertTrue(audit.verify_chain()[0])

    def test_detay_ve_playlist_olaylari_yazilir(self):
        with mock.patch.object(self.worker, "request_json",
                               side_effect=[_DETAY_YANITI,
                                            _LISTE_YANITI]):
            self.worker.video_detail("vid1")
            self.worker.playlist_items("pl1")
        icerik = audit._audit_file().read_text(encoding="utf-8")
        self.assertIn("youtube_video", icerik)
        self.assertIn("youtube_playlist", icerik)
        self.assertTrue(audit.verify_chain()[0])


def _youtube_cli_kayitli_mi() -> bool:
    """CLI/MCP kaydı ana ajanda entegrasyonuna kadar devre dışı olabilir."""
    from orchestrator import cli
    return any(cmd.name == "youtube-arastir" for cmd in cli.get_commands())


class YouTubeCliTests(YouTubeWorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import youtube_worker
        self.worker = youtube_worker

    @unittest.skipUnless(_youtube_cli_kayitli_mi(),
                         "youtube CLI kaydı henüz entegre edilmedi")
    def test_cli_bos_sonuc_dostu_mesaj(self):
        from orchestrator import cli
        with mock.patch.object(self.worker, "request_json",
                               return_value={"items": []}):
            buf = io.StringIO()
            with redirect_stdout(buf):
                kod = cli.main(["youtube-arastir", "x"])
        self.assertEqual(kod, 0)
        self.assertIn("sonuç bulunamadı", buf.getvalue())

    @unittest.skipUnless(_youtube_cli_kayitli_mi(),
                         "youtube CLI kaydı henüz entegre edilmedi")
    def test_cli_kota_hatasi_tek_satir_exit1(self):
        from orchestrator import cli
        hata = HttpError(
            'GET https://www.googleapis.com/youtube/v3/search -> 403: '
            '{"reason": "dailyLimitExceeded"}')
        with mock.patch.object(self.worker, "request_json",
                               side_effect=hata):
            buf = io.StringIO()
            with redirect_stdout(buf):
                kod = cli.main(["youtube-arastir", "x"])
        self.assertEqual(kod, 1)
        self.assertIn("Hata: YouTube API günlük kotası", buf.getvalue())
        self.assertNotIn("test-youtube_api_key", buf.getvalue())


class YouTubeMCPToolTests(unittest.TestCase):
    """MCP şeması: üç tool CLI kayıt tablosundan otomatik türelenmelidir."""

    def _spec(self, ad):
        from mcp_server import tools
        spec = tools.tool_by_name(ad)
        if spec is None:
            self.skipTest("youtube MCP tool kaydı henüz entegre edilmedi")
        return spec, tools

    def test_uc_youtube_toolu_kayitli(self):
        for ad, zorunlu in (("youtube-arastir", ["sorgu"]),
                            ("youtube-detay", ["video_id"]),
                            ("youtube-oynatma-listesi", ["liste_id"])):
            spec, _ = self._spec(ad)
            self.assertEqual(spec.input_schema["required"], zorunlu)
            self.assertEqual(spec.input_schema["additionalProperties"], False)
            for alan in zorunlu:
                self.assertEqual(
                    spec.input_schema["properties"][alan]["type"], "string")

    def test_arastir_sema_ve_cli_eslesmesi(self):
        spec, tools = self._spec("youtube-arastir")
        self.assertEqual(spec.input_schema["properties"]["limit"]["type"],
                         "integer")
        self.assertIn("tur", spec.input_schema["properties"])
        argv = tools.to_cli_args(spec, {"sorgu": "python", "limit": 3})
        self.assertEqual(argv, ["youtube-arastir", "python", "--limit", "3"])

    def test_bilinmeyen_arguman_red(self):
        self._spec("youtube-arastir")
        from mcp_server import tools
        sonuc = tools.execute_tool("youtube-arastir", {"sorgu": "x", "foo": 1})
        self.assertEqual(sonuc["exitCode"], 2)
        self.assertIn("bilinmeyen argüman", sonuc["stderr"])


if __name__ == "__main__":
    unittest.main()
