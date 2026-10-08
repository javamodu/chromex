"""policygate birim testleri — tamamen offline, stdlib-only.

Çalıştırma (policy-gate/ içinden):
    $env:PYTHONPATH = "src"; python -m unittest discover -s tests -v
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from policygate import approval, audit, policy, secrets
from policygate.approval import (ActionRequest, ApprovalDenied,
                                 TerminalChannel, WebhookChannel, require,
                                 set_channel)


class TempEnvTestCase(unittest.TestCase):
    """Her test için audit/policy yollarını geçici dizine yönlendirir."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["POLICY_FILE"] = str(Path(self.tmp.name) / "yok.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "POLICY_FILE"):
            os.environ.pop(key, None)


class AuditTests(TempEnvTestCase):
    def test_zincir_eklenir_ve_dogrulanir(self):
        audit.log_event("a", "test", "READ", "auto", {"n": 1})
        audit.log_event("b", "test", "READ", "auto", {"n": 2})
        rec = audit.log_event("c", "test", "SEND", "approved",
                              {"marker": "ORIJINAL"})
        self.assertEqual(rec["seq"], 3)
        ok, msg = audit.verify_chain()
        self.assertTrue(ok, msg)

    def test_kurcalama_tespit_edilir(self):
        audit.log_event("a", "test", "READ", "auto", {"marker": "ORIJINAL"})
        audit.log_event("b", "test", "READ", "auto", {})
        path = audit._audit_file()
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("ORIJINAL", "KURCALANDI"),
                        encoding="utf-8")
        ok, msg = audit.verify_chain()
        self.assertFalse(ok)

    def test_secret_redaksiyonu(self):
        os.environ["TEST_GIZLI"] = "cok-gizli-token-123"
        secrets.get("TEST_GIZLI")
        rec = audit.log_event("x", "test", "READ", "auto",
                              {"mesaj": "deger: cok-gizli-token-123 idi"})
        self.assertNotIn("cok-gizli-token-123", str(rec["details"]))
        self.assertIn("***", rec["details"]["mesaj"])

    def test_kuyruk_okuma_ile_seq_dogru(self):
        for i in range(25):
            rec = audit.log_event(f"e{i}", "test", "READ", "auto", {})
        self.assertEqual(rec["seq"], 25)
        ok, msg = audit.verify_chain()
        self.assertTrue(ok, msg)


class PolicyTests(TempEnvTestCase):
    def test_varsayilanlar(self):
        self.assertEqual(policy.decision_for("READ", "x"), "auto")
        self.assertEqual(policy.decision_for("SEND", "x"), "ask")

    def test_delete_asla_auto_olamaz(self):
        pol = {"levels": {"DELETE": "auto"}, "always_deny": []}
        self.assertEqual(policy.decision_for("DELETE", "x", pol), "ask")

    def test_always_deny(self):
        pol = {"levels": {"READ": "auto"}, "always_deny": ["tehlikeli.islem"]}
        self.assertEqual(policy.decision_for("READ", "tehlikeli.islem", pol),
                         "deny")

    def test_bozuk_json_guvenli_varsayilana_duser(self):
        dosya = Path(os.environ["POLICY_FILE"])
        dosya.write_text("{bozuk json...", encoding="utf-8")
        self.assertEqual(policy.load(), policy.DEFAULT_POLICY)
        dosya.write_text("[1, 2, 3]", encoding="utf-8")
        pol = policy.load()
        self.assertEqual(pol, policy.DEFAULT_POLICY)
        self.assertEqual(policy.decision_for("DELETE", "x", pol), "ask")

    def test_sema_gecersiz_girdiler_atlanir(self):
        Path(os.environ["POLICY_FILE"]).write_text(json.dumps(
            {"levels": {"SEND": "auto", "HACK": "auto", "READ": "ucur"}}),
            encoding="utf-8")
        pol = policy.load()
        self.assertEqual(pol["levels"]["SEND"], "auto")   # geçerli uygulanır
        self.assertNotIn("HACK", pol["levels"])           # bilinmeyen seviye
        self.assertEqual(pol["levels"]["READ"], "auto")   # "ucur" atlandı

    def test_sema_non_interactive_default_dogrulamasi(self):
        Path(os.environ["POLICY_FILE"]).write_text(
            json.dumps({"non_interactive_default": "belki"}), encoding="utf-8")
        self.assertEqual(policy.load()["non_interactive_default"], "deny")

    def test_sema_always_deny_liste_degilse_yok_sayilir(self):
        Path(os.environ["POLICY_FILE"]).write_text(
            json.dumps({"always_deny": "hepsi"}), encoding="utf-8")
        self.assertEqual(policy.load()["always_deny"], [])


class ApprovalTests(TempEnvTestCase):
    def _req(self, level: str) -> ActionRequest:
        return ActionRequest(worker="test", action="test.islem", level=level,
                             summary="test", details={"k": "v"})

    def test_read_otomatik_gecer(self):
        require(self._req("READ"))
        ok, _ = audit.verify_chain()
        self.assertTrue(ok)

    def test_etkilesimsiz_send_reddedilir(self):
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = False
        with mock.patch("policygate.approval.sys.stdin", fake_stdin):
            with self.assertRaises(ApprovalDenied):
                require(self._req("SEND"))

    def test_etkilesimsiz_kritik_seviye_auto_ayarinda_bile_reddedilir(self):
        Path(os.environ["POLICY_FILE"]).write_text(
            json.dumps({"non_interactive_default": "auto"}), encoding="utf-8")
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = False
        with mock.patch("policygate.approval.sys.stdin", fake_stdin):
            for seviye in ("SEND", "DELETE"):
                with self.assertRaises(ApprovalDenied, msg=seviye):
                    require(self._req(seviye))
            require(self._req("MODIFY"))  # MODIFY'de auto ayarı geçerli kalır

    def test_kullanici_evet_derse_gecer(self):
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = True
        with mock.patch("policygate.approval.sys.stdin", fake_stdin), \
             mock.patch("builtins.input", return_value="EVET"):
            require(self._req("SEND"))

    def test_kucuk_harf_evet_kabul_edilmez(self):
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = True
        with mock.patch("policygate.approval.sys.stdin", fake_stdin), \
             mock.patch("builtins.input", return_value="evet"):
            with self.assertRaises(ApprovalDenied):
                require(self._req("SEND"))

    def test_cp1252_konsolda_banner_cokmez(self):
        # Windows CI/konsol cp1252'dir; Türkçe banner UnicodeEncodeError
        # fırlatmamalı (ASCII katlama devreye girer).
        class CP1252Yazici:
            encoding = "cp1252"

            def write(self, s):
                s.encode("cp1252")  # katlanmamış karakterde gerçek konsol gibi patlar

            def flush(self):
                pass

        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = True
        with mock.patch("policygate.approval.sys.stdin", fake_stdin), \
             mock.patch("policygate.approval.sys.stdout", CP1252Yazici()), \
             mock.patch("builtins.input", return_value="EVET"):
            require(self._req("SEND"))  # fırlatmamalı


class _FakeChannel:
    def __init__(self, cevap: bool) -> None:
        self.cevap = cevap
        self.istekler: list = []

    def ask(self, req):
        self.istekler.append(req)
        return self.cevap


class KanalTests(TempEnvTestCase):
    """v0.3: onay kanalı soyutlaması (webhook/bot köprüleri)."""

    def tearDown(self) -> None:
        set_channel(TerminalChannel())  # kanalı sıfırla
        super().tearDown()

    def _req(self, level: str) -> ActionRequest:
        return ActionRequest(worker="test", action="test.islem", level=level,
                             summary="test")

    def test_kanal_flag_olmadan_etkilesimsizde_sorulmaz(self):
        kanal = _FakeChannel(True)
        set_channel(kanal)  # allow_non_interactive=False (varsayılan)
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = False
        with mock.patch("policygate.approval.sys.stdin", fake_stdin):
            with self.assertRaises(ApprovalDenied):
                require(self._req("SEND"))
        self.assertEqual(kanal.istekler, [])  # kanal hiç çağrılmadı

    def test_kanal_flag_ile_etkilesimsizde_sorulur(self):
        kanal = _FakeChannel(True)
        set_channel(kanal, allow_non_interactive=True)
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = False
        with mock.patch("policygate.approval.sys.stdin", fake_stdin):
            require(self._req("SEND"))  # fırlatmamalı
        self.assertEqual(len(kanal.istekler), 1)

    def test_kanal_redderse_denied(self):
        set_channel(_FakeChannel(False), allow_non_interactive=True)
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = False
        with mock.patch("policygate.approval.sys.stdin", fake_stdin):
            with self.assertRaises(ApprovalDenied):
                require(self._req("MODIFY"))

    def test_webhook_approve_true_onaylar(self):
        kanal = WebhookChannel("https://ornek.test/onay")
        yanit = mock.MagicMock()
        yanit.__enter__.return_value.read.return_value = b'{"approve": true}'
        with mock.patch("urllib.request.urlopen", return_value=yanit):
            self.assertTrue(kanal.ask(self._req("SEND")))

    def test_webhook_hata_verirse_red(self):
        kanal = WebhookChannel("https://ornek.test/onay", timeout=1)
        with mock.patch("urllib.request.urlopen", side_effect=OSError("kapalı")):
            self.assertFalse(kanal.ask(self._req("SEND")))


if __name__ == "__main__":
    unittest.main()
