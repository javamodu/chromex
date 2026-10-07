"""core/ katmanının birim testleri.

Çalıştırma (proje kökünden, ek bağımlılık gerekmez):
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core import audit, policy, secrets, store
from core.approval import ActionRequest, ApprovalDenied, require


class TempEnvTestCase(unittest.TestCase):
    """Her test için audit/store yollarını geçici dizine yönlendirir."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["STORE_DB"] = str(Path(self.tmp.name) / "results.db")
        os.environ["POLICY_FILE"] = str(Path(self.tmp.name) / "yok.json")

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "STORE_DB", "POLICY_FILE"):
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
        self.assertIn("3 kayıt", msg)

    def test_kurcalama_tespit_edilir(self):
        audit.log_event("a", "test", "READ", "auto", {"marker": "ORIJINAL"})
        audit.log_event("b", "test", "READ", "auto", {})
        path = audit._audit_file()
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace("ORIJINAL", "KURCALANDI"),
                        encoding="utf-8")
        ok, msg = audit.verify_chain()
        self.assertFalse(ok)
        self.assertIn("bozuk", msg)

    def test_secret_redaksiyonu(self):
        os.environ["TEST_GIZLI"] = "cok-gizli-token-123"
        secrets.get("TEST_GIZLI")
        rec = audit.log_event("x", "test", "READ", "auto",
                              {"mesaj": "deger: cok-gizli-token-123 idi"})
        self.assertNotIn("cok-gizli-token-123", str(rec["details"]))
        self.assertIn("***", rec["details"]["mesaj"])


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


class ApprovalTests(TempEnvTestCase):
    def _req(self, level: str) -> ActionRequest:
        return ActionRequest(worker="test", action="test.islem", level=level,
                             summary="test", details={"k": "v"})

    def test_read_otomatik_gecer(self):
        require(self._req("READ"))  # exception fırlatmamalı
        ok, _ = audit.verify_chain()
        self.assertTrue(ok)

    def test_etkilesimsiz_send_reddedilir(self):
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = False
        with mock.patch("core.approval.sys.stdin", fake_stdin):
            with self.assertRaises(ApprovalDenied):
                require(self._req("SEND"))

    def test_kullanici_evet_derse_gecer(self):
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = True
        with mock.patch("core.approval.sys.stdin", fake_stdin), \
             mock.patch("builtins.input", return_value="EVET"):
            require(self._req("SEND"))  # fırlatmamalı

    def test_kucuk_harf_evet_kabul_edilmez(self):
        fake_stdin = mock.MagicMock()
        fake_stdin.isatty.return_value = True
        with mock.patch("core.approval.sys.stdin", fake_stdin), \
             mock.patch("builtins.input", return_value="evet"):
            with self.assertRaises(ApprovalDenied):
                require(self._req("SEND"))


class StoreTests(TempEnvTestCase):
    def test_kaydet_ve_listele(self):
        store.save("github", "repo", "https://ex.com", "test/repo", "içerik")
        store.save("gmail", "message", "id1", "konu", "önizleme")
        hepsi = store.recent()
        self.assertEqual(len(hepsi), 2)
        sadece_github = store.recent("github")
        self.assertEqual(len(sadece_github), 1)
        self.assertEqual(sadece_github[0][1], "github")


class _FakeResp:
    """core.http testleri için sahte requests yanıtı."""

    def __init__(self, status, payload=None, retry_after=None):
        import json as _json
        self.status_code = status
        body = _json.dumps(payload if payload is not None else {})
        self.text = body
        self.content = body.encode()
        self.headers = {"Content-Type": "application/json"}
        if retry_after:
            self.headers["Retry-After"] = retry_after

    def json(self):
        import json as _json
        return _json.loads(self.text)


class HttpRetryTests(TempEnvTestCase):
    """core.http retry/backoff — requests kurulmadan da çalışır (sahte modül)."""

    def setUp(self):
        super().setUp()
        import sys
        import types

        self._saved = {k: sys.modules.get(k) for k in ("requests", "core.http")}
        fake = types.ModuleType("requests")
        fake.RequestException = type("RequestException", (Exception,), {})
        self.queue: list = []
        self.calls: list = []

        def _request(method, url, **kwargs):
            self.calls.append((method, url))
            item = self.queue.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        fake.request = _request
        sys.modules["requests"] = fake
        sys.modules.pop("core.http", None)
        import core.http as http_mod
        self.http = http_mod
        self.fake = fake
        self._sleep = mock.patch("core.http.time.sleep").start()

    def tearDown(self):
        mock.patch.stopall()
        import sys
        for key, value in self._saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value
        super().tearDown()

    def test_500_sonra_basari(self):
        self.queue[:] = [_FakeResp(500), _FakeResp(200, {"ok": 1})]
        data = self.http.request_json("GET", "https://x/a", "test")
        self.assertEqual(data, {"ok": 1})
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self._sleep.call_count, 1)
        icerik = audit._audit_file().read_text(encoding="utf-8")
        self.assertIn("http_retry", icerik)

    def test_429_denemeler_bitince_hata(self):
        self.queue[:] = [_FakeResp(429), _FakeResp(429)]
        with self.assertRaises(self.http.HttpError):
            self.http.request_json("GET", "https://x/a", "test", max_retries=1)
        self.assertEqual(len(self.calls), 2)

    def test_ag_hatasi_sonra_basari(self):
        self.queue[:] = [self.fake.RequestException("kopma"),
                         _FakeResp(200, {"ok": 2})]
        data = self.http.request_json("GET", "https://x/a", "test")
        self.assertEqual(data, {"ok": 2})

    def test_404_retry_edilmez(self):
        self.queue[:] = [_FakeResp(404)]
        with self.assertRaises(self.http.HttpError):
            self.http.request_json("GET", "https://x/a", "test")
        self.assertEqual(len(self.calls), 1)
        self._sleep.assert_not_called()

    def test_retry_after_basligina_uyar(self):
        self.queue[:] = [_FakeResp(429, retry_after="7"), _FakeResp(200, {})]
        self.http.request_json("GET", "https://x/a", "test")
        self._sleep.assert_called_once_with(7.0)


if __name__ == "__main__":
    unittest.main()
