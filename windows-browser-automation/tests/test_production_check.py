"""Üretim öncesi doğrulayıcı testleri — tamamen offline."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from policygate import audit


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "production_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("production_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProductionCheckTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_module()
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["POLICY_FILE"] = str(Path(self.tmp.name) / "yok.json")

    def tearDown(self):
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "POLICY_FILE"):
            os.environ.pop(key, None)

    def test_policy_kurallari_gecerli(self):
        self.assertIn("DELETE/SEND/MODIFY", self.module.check_policy())

    def test_audit_bozuksa_red(self):
        audit.log_event("test", "test", "READ", "auto", {"value": "eski"})
        path = audit._audit_file()
        text = path.read_text(encoding="utf-8").replace("eski", "yeni")
        path.write_text(text, encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.module.check_audit()

    def test_registry_cli_ve_mcp_eslesir(self):
        message = self.module.check_registry()
        self.assertIn("20 komut = 20 tool", message)

    def test_main_basarili(self):
        with redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(self.module.main(), 0)
        self.assertIn("PRODUCTION_CHECK_OK", stdout.getvalue())
