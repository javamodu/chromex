"""core/ katmanının birim testleri (store + http köprüsü).

Onay/policy/audit/secrets birim testleri v0.2 cutover ile policygate
paketine taşındı (policy-gate/tests/test_policygate.py); bu dosya yalnızca
wba'ya özgü kalan core modüllerini kapsar.

Çalıştırma (proje kökünden; policygate kurulu olmalı: pip install -e ../policy-gate):
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from policygate import audit, secrets

from core import store


class TempEnvTestCase(unittest.TestCase):
    """Her test için audit/store yollarını geçici dizine yönlendirir."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["STORE_DB"] = str(Path(self.tmp.name) / "results.db")

    def tearDown(self) -> None:
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "STORE_DB"):
            os.environ.pop(key, None)


class StoreTests(TempEnvTestCase):
    def test_kaydet_ve_listele(self):
        store.save("github", "repo", "https://ex.com", "test/repo", "içerik")
        store.save("gmail", "message", "id1", "konu", "önizleme")
        hepsi = store.recent()
        self.assertEqual(len(hepsi), 2)
        sadece_github = store.recent("github")
        self.assertEqual(len(sadece_github), 1)
        self.assertEqual(sadece_github[0][1], "github")

    def test_limit_kelepcesi(self):
        for i in range(3):
            store.save("github", "repo", f"r{i}", "t", "c")
        self.assertEqual(len(store.recent(limit=-5)), 1)     # alt sınır: 1
        self.assertEqual(len(store.recent(limit=99999)), 3)  # üst sınır: 1000


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

    def test_json_olmayan_2xx_hata_verir(self):
        resp = _FakeResp(200)
        resp.headers = {"Content-Type": "text/html"}
        self.queue[:] = [resp]
        with self.assertRaises(self.http.HttpError):
            self.http.request_json("GET", "https://x/a", "test")

    def test_govdesiz_2xx_ham_yanit_dondurur(self):
        resp = _FakeResp(204)
        resp.content = b""
        self.queue[:] = [resp]
        self.assertIs(self.http.request_json("DELETE", "https://x/a", "test"),
                      resp)

    def test_hata_govdesinde_secret_maskelenir(self):
        os.environ["HTTP_TEST_TOKEN"] = "super-gizli-deger-9"
        secrets.get("HTTP_TEST_TOKEN")
        resp = _FakeResp(500)
        resp.text = "sunucu hatasi: super-gizli-deger-9 sizdi"
        resp.content = resp.text.encode()
        self.queue[:] = [resp]
        with self.assertRaises(self.http.HttpError) as ctx:
            self.http.request_json("GET", "https://x/a", "test", max_retries=0)
        self.assertNotIn("super-gizli-deger-9", str(ctx.exception))
        self.assertIn("***", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()