"""workers/ + orchestrator birim testleri — tamamen OFFLINE.

Ağ, gh CLI, Google API, Playwright ve gerçek token'lar gerekmez; hepsi
mock'lanır. Kapsananlar:
- github: gh/REST yolları, PR ayıklama, create_pr onayı
- gmail: arama, taslak (göndermez), send_draft onayı
- x: sayfalama, token yenileme (terminale basılmaz)
- linkedin: userinfo, create_post onayı + gövde, görünürlük doğrulaması
- linkedin_browser: giriş doğrulamaları (tarayıcısız)
- canva: async export akışı, failed durumu
- supabase: PostgREST parametreleri, CLI mutasyon onayı
- vercel: listeleme, cancel onayı
- orchestrator.cli: audit-dogrula, son-kayitlar

Çalıştırma (proje kökünden): python -m unittest discover -s tests -v
"""
from __future__ import annotations

import base64
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from core import audit, store
from core.approval import ApprovalDenied

_ENV_VARS = [
    "GITHUB_TOKEN", "X_ACCESS_TOKEN", "X_USER_ID", "X_CLIENT_ID",
    "X_REFRESH_TOKEN", "LINKEDIN_ACCESS_TOKEN", "LINKEDIN_CLIENT_ID",
    "LINKEDIN_CLIENT_SECRET", "LINKEDIN_REFRESH_TOKEN", "CANVA_ACCESS_TOKEN",
    "SUPABASE_URL", "SUPABASE_ANON_KEY", "VERCEL_TOKEN",
]


class WorkerTestCase(unittest.TestCase):
    """Her teste izole tmp dizin: audit/store/policy + cwd (göreli yazımlar)."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["STORE_DB"] = str(Path(self.tmp.name) / "results.db")
        os.environ["POLICY_FILE"] = str(Path(self.tmp.name) / "yok.json")
        for name in _ENV_VARS:
            os.environ[name] = f"test-{name.lower()}"
        self._cwd = os.getcwd()
        os.chdir(self.tmp.name)

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "STORE_DB", "POLICY_FILE", *_ENV_VARS):
            os.environ.pop(key, None)


class GitHubWorkerTests(WorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import github_worker
        self.worker = github_worker

    def test_search_repos_gh_yolu(self):
        fake = json.dumps([{"fullName": "a/b", "description": "d",
                            "stargazersCount": 5, "url": "https://github.com/a/b"}])
        with mock.patch.object(self.worker, "_gh_available", return_value=True), \
             mock.patch.object(self.worker.subprocess, "run") as run:
            run.return_value = mock.Mock(stdout=fake, returncode=0)
            items = self.worker.search_repos("test", 5)
        self.assertEqual(items[0]["fullName"], "a/b")
        self.assertEqual(len(store.recent("github", 5)), 1)

    def test_search_repos_rest_fallback(self):
        payload = {"items": [{"full_name": "x/y", "description": None,
                              "stargazers_count": 3,
                              "html_url": "https://github.com/x/y"}]}
        with mock.patch.object(self.worker, "_gh_available", return_value=False), \
             mock.patch.object(self.worker, "request_json", return_value=payload):
            items = self.worker.search_repos("test")
        self.assertEqual(items[0]["fullName"], "x/y")
        self.assertEqual(items[0]["stargazersCount"], 3)

    def test_repo_issues_pr_ayiklar(self):
        payload = [
            {"number": 1, "title": "bug", "html_url": "u1", "state": "open"},
            {"number": 2, "title": "pr", "html_url": "u2", "state": "open",
             "pull_request": {}},
        ]
        with mock.patch.object(self.worker, "request_json", return_value=payload):
            issues = self.worker.repo_issues("a/b")
        self.assertEqual([i["number"] for i in issues], [1])

    def test_create_pr_onay_reddedilince_gh_calismaz(self):
        with mock.patch.object(self.worker, "_gh_available", return_value=True), \
             mock.patch.object(self.worker, "require",
                               side_effect=ApprovalDenied("red")), \
             mock.patch.object(self.worker.subprocess, "run") as run:
            with self.assertRaises(ApprovalDenied):
                self.worker.create_pr("başlık", head="feature")
        run.assert_not_called()

    def test_create_pr_onayla_url_dondurur(self):
        captured = {}
        with mock.patch.object(self.worker, "_gh_available", return_value=True), \
             mock.patch.object(self.worker, "require",
                               side_effect=lambda r: captured.update(level=r.level)), \
             mock.patch.object(self.worker.subprocess, "run") as run:
            run.return_value = mock.Mock(
                stdout="https://github.com/a/b/pull/1\n", stderr="", returncode=0)
            url = self.worker.create_pr("başlık", head="feature")
        self.assertEqual(url, "https://github.com/a/b/pull/1")
        self.assertEqual(captured["level"], "MODIFY")


def _gmail_svc(list_payload: dict, get_payload: dict) -> mock.MagicMock:
    svc = mock.MagicMock()
    msgs = svc.users.return_value.messages.return_value
    msgs.list.return_value.execute.return_value = list_payload
    msgs.get.return_value.execute.return_value = get_payload
    return svc


class GmailWorkerTests(WorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import gmail_worker
        self.worker = gmail_worker

    def test_search_metadata_esler(self):
        svc = _gmail_svc(
            {"messages": [{"id": "m1"}]},
            {"payload": {"headers": [
                {"name": "From", "value": "a@b.c"},
                {"name": "Subject", "value": "Konu"},
                {"name": "Date", "value": "Pzt"}]},
             "snippet": "önizleme"},
        )
        with mock.patch.object(self.worker, "_service", return_value=svc):
            out = self.worker.search("is:unread", 5)
        self.assertEqual(out[0]["subject"], "Konu")
        self.assertEqual(out[0]["from"], "a@b.c")
        self.assertEqual(len(store.recent("gmail", 5)), 1)

    def test_create_draft_gondermez(self):
        svc = mock.MagicMock()
        drafts = svc.users.return_value.drafts.return_value
        drafts.create.return_value.execute.return_value = {"id": "d1"}
        with mock.patch.object(self.worker, "_service", return_value=svc):
            draft_id = self.worker.create_draft("a@b.c", "Konu", "Gövde")
        self.assertEqual(draft_id, "d1")
        drafts.send.assert_not_called()
        raw = drafts.create.call_args.kwargs["body"]["message"]["raw"]
        decoded = base64.urlsafe_b64decode(raw).decode()
        self.assertIn("a@b.c", decoded)
        self.assertIn("Konu", decoded)

    def test_send_draft_onaysiz_gondermez(self):
        svc = mock.MagicMock()
        drafts = svc.users.return_value.drafts.return_value
        drafts.get.return_value.execute.return_value = {
            "message": {"payload": {"headers": [
                {"name": "To", "value": "a@b.c"},
                {"name": "Subject", "value": "K"}]}, "snippet": "x"}}
        with mock.patch.object(self.worker, "_service", return_value=svc), \
             mock.patch.object(self.worker, "require",
                               side_effect=ApprovalDenied("red")):
            with self.assertRaises(ApprovalDenied):
                self.worker.send_draft("d1")
        drafts.send.assert_not_called()

    def test_send_draft_onayla_gonderir(self):
        captured = {}
        svc = mock.MagicMock()
        drafts = svc.users.return_value.drafts.return_value
        drafts.get.return_value.execute.return_value = {
            "message": {"payload": {"headers": [
                {"name": "To", "value": "a@b.c"},
                {"name": "Subject", "value": "K"}]}, "snippet": "x"}}
        drafts.send.return_value.execute.return_value = {"id": "s1"}
        with mock.patch.object(self.worker, "_service", return_value=svc), \
             mock.patch.object(self.worker, "require",
                               side_effect=lambda r: captured.update(level=r.level)):
            sent = self.worker.send_draft("d1")
        self.assertEqual(sent["id"], "s1")
        self.assertEqual(captured["level"], "SEND")


class XWorkerTests(WorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import x_bookmarks_worker
        self.worker = x_bookmarks_worker

    def test_bookmarks_sayfalama_birlesir(self):
        page1 = {"data": [{"id": "1", "text": "a"}], "meta": {"next_token": "n1"}}
        page2 = {"data": [{"id": "2", "text": "b"}], "meta": {}}
        with mock.patch.object(self.worker, "request_json",
                               side_effect=[page1, page2]) as req:
            items = self.worker.fetch_bookmarks(10)
        self.assertEqual([i["id"] for i in items], ["1", "2"])
        self.assertEqual(req.call_count, 2)
        self.assertEqual(
            req.call_args_list[1].kwargs["params"]["pagination_token"], "n1")

    def test_refresh_token_terminale_basilmaz(self):
        resp = mock.Mock()
        resp.json.return_value = {"access_token": "YENI-GIZLI-TOKEN",
                                  "refresh_token": "R2", "expires_in": 7200}
        with mock.patch("requests.post", return_value=resp), \
             redirect_stdout(io.StringIO()) as buf:
            token = self.worker.refresh_access_token()
        self.assertEqual(token, "YENI-GIZLI-TOKEN")
        self.assertNotIn("YENI-GIZLI-TOKEN", buf.getvalue())
        content = Path("data/x_tokens.env").read_text(encoding="utf-8")
        self.assertIn("X_ACCESS_TOKEN=YENI-GIZLI-TOKEN", content)


class LinkedInWorkerTests(WorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import linkedin_worker
        self.worker = linkedin_worker

    def test_me_profil_esler(self):
        with mock.patch.object(self.worker, "request_json", return_value={
                "sub": "u1", "name": "Ada", "email": "a@b.c", "picture": "p"}):
            prof = self.worker.me()
        self.assertEqual(prof["id"], "u1")
        self.assertEqual(prof["ad"], "Ada")

    def test_create_post_onay_red(self):
        with mock.patch.object(self.worker, "me", return_value={"id": "u1"}), \
             mock.patch.object(self.worker, "require",
                               side_effect=ApprovalDenied("red")), \
             mock.patch.object(self.worker, "request_json") as req:
            with self.assertRaises(ApprovalDenied):
                self.worker.create_post("merhaba")
        req.assert_not_called()

    def test_create_post_basarili(self):
        captured = {}
        with mock.patch.object(self.worker, "me", return_value={"id": "u1"}), \
             mock.patch.object(self.worker, "require",
                               side_effect=lambda r: captured.update(level=r.level)), \
             mock.patch.object(self.worker, "request_json",
                               return_value={"id": "urn:li:ugcPost:9"}) as req:
            post_id = self.worker.create_post("merhaba", "connections")
        self.assertEqual(post_id, "urn:li:ugcPost:9")
        self.assertEqual(captured["level"], "SEND")
        body = req.call_args.kwargs["json_body"]
        self.assertEqual(body["author"], "urn:li:person:u1")
        self.assertEqual(
            body["visibility"]["com.linkedin.ugc.MemberNetworkVisibility"],
            "CONNECTIONS")
        self.assertEqual(req.call_args.kwargs["max_retries"], 0)

    def test_create_post_gecersiz_gorunurluk_ag_cagirmaz(self):
        with mock.patch.object(self.worker, "me") as me_mock:
            with self.assertRaises(ValueError):
                self.worker.create_post("x", "HERKESE")
        me_mock.assert_not_called()


class LinkedInBrowserTests(WorkerTestCase):
    def test_search_gecersiz_tur(self):
        from workers import linkedin_browser
        with self.assertRaises(ValueError):
            linkedin_browser.search("x", kind="yok")

    def test_tarayici_yoksa_net_runtimeerror(self):
        # playwright kurulu değilse VEYA CDP kapalıysa: ikisi de RuntimeError
        from workers import linkedin_browser
        with self.assertRaises(RuntimeError):
            linkedin_browser.feed(1)


class CanvaWorkerTests(WorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import canva_worker
        self.worker = canva_worker

    def test_export_basarili_indirir(self):
        start = {"job": {"id": "j1"}}
        done = {"job": {"status": "success", "urls": ["https://cdn/f.pdf"]}}
        resp = mock.Mock(content=b"PDFBYTES")
        with mock.patch.object(self.worker, "request_json",
                               side_effect=[start, done]), \
             mock.patch.object(self.worker, "POLL_SANIYE", 0), \
             mock.patch("requests.get", return_value=resp):
            paths = self.worker.export_design("d1", "pdf", out_dir="data/canva")
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].read_bytes(), b"PDFBYTES")
        self.assertTrue(str(paths[0]).endswith("d1-0.pdf"))

    def test_export_failed_runtimeerror(self):
        start = {"job": {"id": "j1"}}
        failed = {"job": {"status": "failed", "error": "bozuk"}}
        with mock.patch.object(self.worker, "request_json",
                               side_effect=[start, failed]), \
             mock.patch.object(self.worker, "POLL_SANIYE", 0):
            with self.assertRaises(RuntimeError):
                self.worker.export_design("d1")


class SupabaseWorkerTests(WorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import supabase_worker
        self.worker = supabase_worker

    def test_query_params_ve_header(self):
        with mock.patch.object(self.worker, "request_json",
                               return_value=[{"id": 1}]) as req:
            out = self.worker.query_table("tablo", "id,name", 5,
                                          {"status": "eq.active"})
        self.assertEqual(out, [{"id": 1}])
        args, kwargs = req.call_args
        self.assertIn("/rest/v1/tablo", args[1])
        self.assertEqual(kwargs["params"]["status"], "eq.active")
        self.assertEqual(kwargs["headers"]["apikey"], "test-supabase_anon_key")

    def test_cli_mutasyon_onay_ister(self):
        with mock.patch.object(self.worker.shutil, "which",
                               return_value="/usr/bin/supabase"), \
             mock.patch.object(self.worker, "require",
                               side_effect=ApprovalDenied("red")), \
             mock.patch.object(self.worker.subprocess, "run") as run:
            with self.assertRaises(ApprovalDenied):
                self.worker.cli(["db", "push"])
        run.assert_not_called()

    def test_cli_readonly_onaysiz_calisir(self):
        with mock.patch.object(self.worker.shutil, "which",
                               return_value="/usr/bin/supabase"), \
             mock.patch.object(self.worker, "require") as require_mock, \
             mock.patch.object(self.worker.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0, stdout="ok", stderr="")
            out = self.worker.cli(["status"])
        require_mock.assert_not_called()
        self.assertEqual(out, "ok")


class VercelWorkerTests(WorkerTestCase):
    def setUp(self) -> None:
        super().setUp()
        from workers import vercel_worker
        self.worker = vercel_worker

    def test_list_deployments_esler(self):
        payload = {"deployments": [{"uid": "d1", "name": "app",
                                    "readyState": "READY", "url": "u",
                                    "createdAt": 123}]}
        with mock.patch.object(self.worker, "request_json", return_value=payload):
            items = self.worker.list_deployments("app", 5)
        self.assertEqual(items[0]["state"], "READY")
        self.assertEqual(items[0]["created"], 123)

    def test_cancel_onay_reddedilince_cagrilmaz(self):
        with mock.patch.object(self.worker, "require",
                               side_effect=ApprovalDenied("red")), \
             mock.patch.object(self.worker, "request_json") as req:
            with self.assertRaises(ApprovalDenied):
                self.worker.cancel_deployment("d1")
        req.assert_not_called()

    def test_cancel_onayla_patch_atar(self):
        captured = {}
        with mock.patch.object(self.worker, "require",
                               side_effect=lambda r: captured.update(level=r.level)), \
             mock.patch.object(self.worker, "request_json",
                               return_value={"ok": 1}) as req:
            out = self.worker.cancel_deployment("d1")
        self.assertEqual(out, {"ok": 1})
        self.assertEqual(captured["level"], "MODIFY")
        self.assertEqual(req.call_args.args[0], "PATCH")
        self.assertIn("/v12/deployments/d1/cancel", req.call_args.args[1])


class CliTests(WorkerTestCase):
    def test_audit_dogrula_bos_zincir(self):
        from orchestrator.cli import main
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["audit-dogrula"]), 0)

    def test_son_kayitlar(self):
        store.save("github", "repo", "u", "t", None)
        from orchestrator.cli import main
        with redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(main(["son-kayitlar"]), 0)
        self.assertIn("github", buf.getvalue())


class CoreLogTests(WorkerTestCase):
    def test_seviye_env_den_okunur(self):
        os.environ["OTOMASYON_LOG"] = "DEBUG"
        from core import log
        self.assertEqual(log.get("test.modul").level, 10)  # logging.DEBUG
        os.environ.pop("OTOMASYON_LOG", None)

    def test_handler_tekil_ve_tekrarli_cagri_ayni(self):
        from core import log
        first, second = log.get("x.y"), log.get("x.y")
        self.assertIs(first, second)
        self.assertEqual(len(first.handlers), 1)


class AuditBridgeParityTests(WorkerTestCase):
    """claude-code-automation/audit_bridge.py (taşınabilir kopya) ile
    core/audit.py AYNI zincir formatını üretmeli; iki taraf da karşı
    tarafın kayıtlarını doğrulayabilmeli."""

    def _bridge(self):
        import importlib.util
        path = (Path(self._cwd).parent
                / "claude-code-automation" / "audit_bridge.py")
        spec = importlib.util.spec_from_file_location("audit_bridge", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_karsilikli_zincir_dogrulama(self):
        bridge = self._bridge()
        audit.log_event("core_olay", "test", "READ", "auto", {"n": 1})
        bridge.log("bridge_olay", {"n": 2})
        audit.log_event("core_olay_2", "test", "READ", "auto", {"n": 3})
        ok, msg = audit.verify_chain()
        self.assertTrue(ok, msg)
        ok_b, msg_b = bridge.verify()
        self.assertTrue(ok_b, msg_b)
        lines = (audit._audit_file().read_text(encoding="utf-8")
                 .strip().splitlines())
        self.assertEqual([json.loads(l)["seq"] for l in lines], [1, 2, 3])
