"""Site bazlı güvenlik sınırları ve pilot deneme testleri — OFFLINE."""
from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core import site_guvenlik
from orchestrator import cli


class SiteGuvenlikTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["POLICY_FILE"] = str(Path(self.tmp.name) / "yok.json")
        os.environ["SITE_LIMIT_STATE"] = str(
            Path(self.tmp.name) / "site_limits.json")
        self._cwd = os.getcwd()
        os.chdir(self.tmp.name)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "POLICY_FILE", "SITE_LIMIT_STATE"):
            os.environ.pop(key, None)


class ProfilTests(SiteGuvenlikTestCase):
    def test_ornek_siteler_profili_yuklenir(self):
        for site in ("linkedin", "x", "youtube", "chatgpt"):
            profil = site_guvenlik.profil_al(site)
            self.assertEqual(profil.site, site)
            self.assertGreater(profil.okuma.saatlik, 0)
            self.assertGreater(profil.yazma.saatlik, 0)
            self.assertGreater(profil.gonderme.saatlik, 0)

    def test_bilinmeyen_site_hata_verir(self):
        with self.assertRaises(ValueError):
            site_guvenlik.profil_al("bilinmeyen-site")

    def test_site_listesi_alfebetik_sirali(self):
        self.assertEqual(site_guvenlik.siteler(), sorted(site_guvenlik.siteler()))

    def test_kesfet_ozet_verir(self):
        sonuc = site_guvenlik.kesfet()
        self.assertIn("siteler", sonuc)
        adlar = {kayit["site"] for kayit in sonuc["siteler"]}
        self.assertTrue({"linkedin", "x", "youtube", "chatgpt"} <= adlar)


class LimitTests(SiteGuvenlikTestCase):
    def _durum_yaz(self, durum: dict) -> None:
        yol = Path(os.environ["SITE_LIMIT_STATE"])
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text(json.dumps(durum), encoding="utf-8")

    def test_bozuk_durum_fail_closed_olarak_hata_verir(self):
        Path(os.environ["SITE_LIMIT_STATE"]).write_text(
            "{bozuk", encoding="utf-8")
        with self.assertRaises(ValueError):
            site_guvenlik.kontrol_et("linkedin", "okuma")

    def test_izinli_adim_sayaci_artar(self):
        sonuc = site_guvenlik.kontrol_et("linkedin", "okuma")
        self.assertTrue(sonuc["izinli"])
        self.assertEqual(sonuc["durum"]["saat_sayisi"], 1)
        self.assertEqual(sonuc["durum"]["gun_sayisi"], 1)

    def test_bekleme_suresi_asilinca_red(self):
        an = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
        site_guvenlik.kontrol_et("linkedin", "okuma", simdi=an)
        sonuc = site_guvenlik.kontrol_et(
            "linkedin", "okuma", simdi=an + timedelta(seconds=1))
        self.assertFalse(sonuc["izinli"])
        self.assertEqual(sonuc["neden"], "bekleme_suresi")

    def test_seri_limiti_asilinca_red(self):
        sonuc = site_guvenlik.kontrol_et("linkedin", "okuma", adet=6)
        self.assertFalse(sonuc["izinli"])
        self.assertEqual(sonuc["neden"], "seri_limiti")

    def test_saat_limiti_asilinca_red(self):
        an = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
        durum = {
            "linkedin": {
                "okuma": {
                    "saat": an.strftime("%Y-%m-%dT%H"),
                    "saat_sayisi": 29,
                    "gun": an.strftime("%Y-%m-%d"),
                    "gun_sayisi": 29,
                    "son": (an - timedelta(hours=1)).isoformat(),
                }
            }
        }
        self._durum_yaz(durum)
        sonuc = site_guvenlik.kontrol_et("linkedin", "okuma", adet=2, simdi=an)
        self.assertFalse(sonuc["izinli"])
        self.assertEqual(sonuc["neden"], "saat_limiti")

    def test_gun_limiti_asilinca_red(self):
        an = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
        durum = {
            "x": {
                "okuma": {
                    "saat": an.strftime("%Y-%m-%dT%H"),
                    "saat_sayisi": 0,
                    "gun": an.strftime("%Y-%m-%d"),
                    "gun_sayisi": 79,
                    "son": (an - timedelta(days=1)).isoformat(),
                }
            }
        }
        self._durum_yaz(durum)
        sonuc = site_guvenlik.kontrol_et("x", "okuma", adet=2, simdi=an)
        self.assertFalse(sonuc["izinli"])
        self.assertEqual(sonuc["neden"], "gun_limiti")

    def test_saat_degismince_sayac_sifirlanir(self):
        an = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)
        site_guvenlik.kontrol_et("x", "okuma", simdi=an)
        sonuc = site_guvenlik.kontrol_et(
            "x", "okuma", simdi=an + timedelta(hours=1))
        self.assertTrue(sonuc["izinli"])
        self.assertEqual(sonuc["durum"]["saat_sayisi"], 1)


class PilotTests(SiteGuvenlikTestCase):
    def test_pilot_plani_uretir(self):
        plan = site_guvenlik.pilot_plani("linkedin")
        self.assertEqual(len(plan), 3)
        self.assertEqual(plan[0]["bekleme_saniye"], 0)
        self.assertGreater(plan[1]["bekleme_saniye"], 0)

    def test_pilot_izinli_adim_donuturur(self):
        sonuc = site_guvenlik.pilot("youtube", "okuma", 1)
        self.assertTrue(sonuc["izinli"])
        self.assertEqual(sonuc["durum"]["saat_sayisi"], 1)

    def test_pilot_adim_asimi_red(self):
        sonuc = site_guvenlik.pilot("x", "okuma", 4)
        self.assertFalse(sonuc["izinli"])
        self.assertEqual(sonuc["neden"], "pilot_adim_limiti")


class KomutEslemeTests(SiteGuvenlikTestCase):
    def test_dis_komutlar_site_ve_eylem_donuturur(self):
        self.assertEqual(
            site_guvenlik.komut_haritasi("youtube-arastir"),
            ("youtube", "okuma"),
        )
        self.assertEqual(
            site_guvenlik.komut_haritasi("linkedin-paylas"),
            ("linkedin", "gonderme"),
        )
        self.assertEqual(
            site_guvenlik.komut_haritasi("github-pr"),
            ("github", "yazma"),
        )

    def test_ic_komutlar_limit_disi_kalir(self):
        for komut in ("site-kesfet", "son-kayitlar", "audit-dogrula", "zamanla"):
            self.assertIsNone(site_guvenlik.komut_haritasi(komut))


class CliTests(SiteGuvenlikTestCase):
    def test_site_keşfet_listesi_yazdirir(self):
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["site-kesfet"]), 0)
        self.assertIn("linkedin", cikti.getvalue())
        self.assertIn("chatgpt", cikti.getvalue())

    def test_site_keşfet_profil_yazdirir(self):
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(cli.main(["site-kesfet", "linkedin"]), 0)
        self.assertIn("risk", cikti.getvalue())
        self.assertIn("pilot", cikti.getvalue())

    def test_site_keşfet_pilot_adimi_kosar(self):
        with redirect_stdout(io.StringIO()) as cikti:
            self.assertEqual(
                cli.main(["site-kesfet", "youtube", "--pilot", "--adim", "1"]),
                0,
            )
        self.assertIn("izinli", cikti.getvalue())


if __name__ == "__main__":
    unittest.main()
