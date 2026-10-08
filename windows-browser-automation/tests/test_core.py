"""core/ katmanının birim testleri (yalnızca store).

Onay/policy/audit/secrets testleri policygate paketindedir
(policy-gate/tests/test_policygate.py); HTTP retry testleri de v0.4'te
oraya taşındı (policy-gate/tests/test_http.py). core/http.py artık
policygate.http'e ince bir köprüdür.

Çalıştırma (proje kökünden; policygate kurulu olmalı: pip install -e ../policy-gate):
    python -m unittest discover -s tests -v
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from core import store


class TempEnvTestCase(unittest.TestCase):
    """Her test için store yolunu geçici dizine yönlendirir."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["STORE_DB"] = str(Path(self.tmp.name) / "results.db")

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("STORE_DB", None)


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


if __name__ == "__main__":
    unittest.main()