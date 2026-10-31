"""Secret kasası (core/kasa.py) testleri — tamamen offline.

DPAPI çağrıları deterministik sahteyle değiştirilir (gerçek DPAPI yalnızca
Windows'ta tek gidiş-dönüş testinde kullanılır). Onay kapısı mock'lanır;
ağ yok, gerçek secret yok.
"""
from __future__ import annotations

import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from policygate import ApprovalDenied, secrets

from core import kasa
from orchestrator import cli


def _sahte_koruma(veri: bytes) -> bytes:
    return b"SADE" + veri


def _sahte_cozum(blob: bytes) -> bytes:
    if not blob.startswith(b"SADE"):
        raise ValueError("sahte DPAPI blob'u bozuk")
    return blob[4:]


class KasaOrtamTestCase(unittest.TestCase):
    """Kasa, audit, policy ve çalışma dizinini geçici alana yönlendirir."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kok = Path(self.tmp.name)
        os.environ["SECRET_VAULT"] = str(self.kok / "kasa.json")
        os.environ["AUDIT_DIR"] = str(self.kok / "audit")
        os.environ["POLICY_FILE"] = str(self.kok / "yok.json")
        self._cwd = os.getcwd()
        os.chdir(self.kok)
        # LIFO: önce dizine dön, sonra geçici dizini sil
        self.addCleanup(self.tmp.cleanup)
        self.addCleanup(os.chdir, self._cwd)
        for anahtar in ("SECRET_VAULT", "AUDIT_DIR", "POLICY_FILE",
                        "GITHUB_TOKEN"):
            self.addCleanup(os.environ.pop, anahtar, None)
        for ad, yeni in (("_dpapi_koruma", _sahte_koruma),
                         ("_dpapi_cozum", _sahte_cozum)):
            yama = mock.patch.object(kasa, ad, new=yeni)
            yama.start()
            self.addCleanup(yama.stop)


class KasaYazOkuTests(KasaOrtamTestCase):
    def test_yaz_duz_metin_yazmaz_ve_geri_okunur(self):
        kasa.yaz({"GITHUB_TOKEN": "ghp_cok_gizli"})
        metin = kasa.kasa_yolu().read_text(encoding="utf-8")
        self.assertNotIn("ghp_cok_gizli", metin)
        self.assertIn("GITHUB_TOKEN", metin)  # anahtar adı görünür, değer gizli
        self.assertEqual(kasa.oku()["GITHUB_TOKEN"], "ghp_cok_gizli")

    def test_kasa_yoksa_bos_donar(self):
        # kasa yok: oku boş sözlük döner; "yok" durumu dogrula'da bildirilir
        self.assertEqual(kasa.oku(), {})
        self.assertFalse(kasa.kasa_yolu().exists())

    def test_bozuk_json_hata(self):
        kasa.kasa_yolu().write_text("{bozuk", encoding="utf-8")
        with self.assertRaises(kasa.KasaHatasi) as baglam:
            kasa.oku()
        self.assertIn("bozuk", str(baglam.exception))

    def test_bozuk_blob_hata(self):
        govde = '{"surum": 1, "anahtarlar": {"GITHUB_TOKEN": "QUJD"}}'
        kasa.kasa_yolu().write_text(govde, encoding="utf-8")
        with self.assertRaises(kasa.KasaHatasi) as baglam:
            kasa.oku()
        self.assertIn("çözülemiyor", str(baglam.exception))


class KasaYukleTests(KasaOrtamTestCase):
    def test_yukle_env_degeri_enjekte_eder(self):
        os.environ.pop("GITHUB_TOKEN", None)
        kasa.yaz({"GITHUB_TOKEN": "ghp_kasa"})
        self.assertIsNone(kasa.yukle_env())
        self.assertEqual(os.environ["GITHUB_TOKEN"], "ghp_kasa")

    def test_yukle_env_ortam_degiskeni_onecekli_gelir(self):
        os.environ["GITHUB_TOKEN"] = "envde_var"
        kasa.yaz({"GITHUB_TOKEN": "ghp_kasa"})
        kasa.yukle_env()
        self.assertEqual(os.environ["GITHUB_TOKEN"], "envde_var")

    def test_yukle_env_kasa_yoksa_sessiz(self):
        self.assertIsNone(kasa.yukle_env())

    def test_yukle_env_bozuk_kasada_env_dokunmaz(self):
        os.environ.pop("GITHUB_TOKEN", None)
        kasa.kasa_yolu().write_text("{bozuk", encoding="utf-8")
        hata = kasa.yukle_env()
        self.assertIsNotNone(hata)
        self.assertIn("bozuk", hata)
        self.assertNotIn("GITHUB_TOKEN", os.environ)


class RedaksiyonTests(KasaOrtamTestCase):
    def test_kasa_degeri_redaksiyon_kaydina_girer(self):
        kasa.yaz({"GITHUB_TOKEN": "ghp_kasa"})
        kasa.yukle_env()
        self.addCleanup(secrets._REGISTERED.discard, "ghp_kasa")
        self.assertEqual(secrets.redact("token=ghp_kasa"), "token=***")


class SecretKurTests(KasaOrtamTestCase):
    def test_kur_yazar_deger_yazmaz(self):
        with mock.patch("getpass.getpass", return_value="ghp_yeni"), \
             redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["secret-kur", "GITHUB_TOKEN"]), 0)
        self.assertNotIn("ghp_yeni", cikti.getvalue())
        self.assertNotIn("ghp_yeni",
                         kasa.kasa_yolu().read_text(encoding="utf-8"))
        self.assertEqual(kasa.oku()["GITHUB_TOKEN"], "ghp_yeni")

    def test_kur_anahtarsiz_kullanim_hatasi(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["secret-kur"]), 2)

    def test_kur_bos_cevap_mevcut_degeri_korur(self):
        kasa.yaz({"GITHUB_TOKEN": "ghp_eski"})
        with mock.patch("getpass.getpass", return_value="  "), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["secret-kur", "GITHUB_TOKEN"]), 0)
        self.assertEqual(kasa.oku()["GITHUB_TOKEN"], "ghp_eski")

    def test_kur_eof_terminal_yoksa_hata(self):
        with mock.patch("getpass.getpass", side_effect=EOFError), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["secret-kur", "GITHUB_TOKEN"]), 1)


class SecretDogrulaTests(KasaOrtamTestCase):
    def test_kasa_yok_red(self):
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["secret-dogrula"]), 1)
        self.assertIn("Kasa yok", cikti.getvalue())

    def test_saglam_kasa_tamam(self):
        kasa.yaz({"GITHUB_TOKEN": "ghp_kasa"})
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["secret-dogrula"]), 0)
        metin = cikti.getvalue()
        self.assertIn("SECRET_DOGRULA_OK", metin)
        self.assertIn("GITHUB_TOKEN", metin)
        self.assertNotIn("ghp_kasa", metin)

    def test_bos_kasa_red(self):
        kasa.yaz({})
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["secret-dogrula"]), 1)
        self.assertIn("Kasa boş", cikti.getvalue())

    def test_bozuk_kasa_red(self):
        kasa.kasa_yolu().write_text("{bozuk", encoding="utf-8")
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["secret-dogrula"]), 1)
        self.assertIn("BOZUK", cikti.getvalue())

    def test_eksik_gerekli_anahtar_red(self):
        kasa.yaz({"GITHUB_TOKEN": "ghp_kasa"})
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(
                cli.main(["secret-dogrula", "--gerekli", "X_TOKEN"]), 1)
        self.assertIn("X_TOKEN", cikti.getvalue())


class SecretTasiTests(KasaOrtamTestCase):
    def test_tasi_tasir_ve_dosyayi_siler(self):
        Path(".env").write_text(
            "# yorum\nGITHUB_TOKEN=ghp_dosyada\nBOS_ANAHTAR=\n",
            encoding="utf-8")
        with mock.patch.object(cli, "require") as onay, \
             redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["secret-tasi"]), 0)
        self.assertIn("level='DELETE'", str(onay.call_args))
        self.assertFalse(Path(".env").exists())
        self.assertEqual(kasa.oku()["GITHUB_TOKEN"], "ghp_dosyada")
        self.assertNotIn("ghp_dosyada",
                         kasa.kasa_yolu().read_text(encoding="utf-8"))
        self.assertNotIn("ghp_dosyada", cikti.getvalue())

    def test_tasi_onaysiz_dosya_ve_kasa_dokunulmaz(self):
        Path(".env").write_text("GITHUB_TOKEN=ghp_dosyada\n", encoding="utf-8")
        with mock.patch.object(cli, "require",
                               side_effect=ApprovalDenied("red")):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main(["secret-tasi"]), 3)
        self.assertTrue(Path(".env").exists())
        self.assertFalse(kasa.kasa_yolu().exists())

    def test_tasi_dosya_yok_red(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["secret-tasi", "--dosya", "yok.env"]), 1)

    def test_tasi_dolmayan_dosya_dokunulmaz(self):
        Path("bos.env").write_text("# yalnızca yorum\n", encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["secret-tasi", "--dosya", "bos.env"]), 1)
        self.assertTrue(Path("bos.env").exists())


class MainEntegrasyonTests(KasaOrtamTestCase):
    def test_main_kasa_degerini_env_yukler(self):
        kasa.yaz({"GITHUB_TOKEN": "ghp_kasa"})
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["audit-dogrula"]), 0)
        self.assertEqual(os.environ["GITHUB_TOKEN"], "ghp_kasa")

    def test_main_bozuk_kasa_uyari_verir_ve_devam_eder(self):
        kasa.kasa_yolu().write_text("{bozuk", encoding="utf-8")
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["audit-dogrula"]), 0)
        self.assertIn("Uyarı", cikti.getvalue())


@unittest.skipUnless(sys.platform == "win32",
                     "gerçek DPAPI yalnızca Windows'ta var")
class GercekDPAPITests(unittest.TestCase):
    def test_git_gelis_esit(self):
        veri = "ghp_gercek_ornek".encode("utf-8")
        self.assertEqual(kasa._dpapi_cozum(kasa._dpapi_koruma(veri)), veri)

    def test_kasa_gercek_yaz_ve_oku(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["SECRET_VAULT"] = os.path.join(tmp, "kasa.json")
            try:
                kasa.yaz({"GITHUB_TOKEN": "ghp_gercek"})
                self.assertEqual(kasa.oku()["GITHUB_TOKEN"], "ghp_gercek")
                self.assertNotIn(
                    "ghp_gercek",
                    Path(os.environ["SECRET_VAULT"]).read_text(
                        encoding="utf-8"))
            finally:
                os.environ.pop("SECRET_VAULT", None)


if __name__ == "__main__":
    unittest.main()
