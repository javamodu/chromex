"""Zamanlayıcı ve `zamanla` CLI kanca testleri — offline."""
from __future__ import annotations

import json, sqlite3
from contextlib import closing
from unittest import mock

from core import store
from policygate import ApprovalDenied, audit
from test_workers import WorkerTestCase


class SchedulerTests(WorkerTestCase):
    def setUp(self):
        super().setUp()
        from workers import scheduler
        self.scheduler = scheduler

    def _job(self, **updates):
        job = {"komut": "github-arastir", "args": ["chromex"],
               "seviye": "READ", "zaman_asimi": 5}
        job.update(updates)
        path = f"{self.tmp.name}/job.json"
        with open(path, "w", encoding="utf-8") as fh: fh.write(json.dumps(job))
        return path

    def test_gecerli_is_kosar_ve_kayit_olusturur(self):
        with mock.patch.object(self.scheduler.subprocess, "run") as run:
            run.return_value = mock.Mock(returncode=0)
            self.assertEqual(self.scheduler.run_job(self._job()), 0)
        command = run.call_args.args[0]
        self.assertEqual(command[1:], ["-m", "orchestrator.cli",
                                        "github-arastir", "chromex"])
        self.assertEqual(run.call_args.kwargs["timeout"], 5)
        self.assertEqual(run.call_args.kwargs["cwd"], self.scheduler.PACKAGE_ROOT)
        records = store.recent(self.scheduler.WORKER, 1)
        self.assertEqual(records[0][1:3], (self.scheduler.WORKER, "job"))
        audit_text = audit._audit_file().read_text(encoding="utf-8")
        self.assertTrue("scheduler_job_started" in audit_text and "scheduler_job_finished" in audit_text)

    def test_send_seviyesi_reddedilir(self):
        with mock.patch.object(self.scheduler, "preflight") as pre, \
             mock.patch.object(self.scheduler, "require") as req, \
             mock.patch.object(self.scheduler.subprocess, "run") as run:
            with self.assertRaises(ApprovalDenied):
                self.scheduler.run_job(self._job(seviye="SEND"))
        self.assertFalse(pre.called or req.called or run.called)
        self.assertIn("scheduler_job_rejected", audit._audit_file().read_text(encoding="utf-8"))

    def test_kirik_json_hatasi(self):
        path = f"{self.tmp.name}/job.json"
        with open(path, "w", encoding="utf-8") as fh: fh.write("{bozuk")
        with self.assertRaises(self.scheduler.SchedulerError):
            self.scheduler.run_job(path)
        self.assertIn("scheduler_job_rejected", audit._audit_file().read_text(encoding="utf-8"))

    def test_zaman_asimi_hatasi(self):
        expired = self.scheduler.subprocess.TimeoutExpired("github-arastir", 5)
        with mock.patch.object(self.scheduler.subprocess, "run",
                               side_effect=expired):
            with self.assertRaises(TimeoutError):
                self.scheduler.run_job(self._job())
        with closing(sqlite3.connect(store._db_path())) as conn:
            content = conn.execute(
                "SELECT content FROM results WHERE source = 'scheduler'"
            ).fetchone()[0]
        self.assertEqual(content, "timeout")
        self.assertIn("scheduler_job_failed",
                      audit._audit_file().read_text(encoding="utf-8"))

    def test_cli_zamanla_komutu_kancki(self):
        from orchestrator import cli
        with mock.patch.object(self.scheduler, "run_job", return_value=0) as run:
            self.assertEqual(cli.main(["zamanla", "--dosya", "job.json"]), 0)
        run.assert_called_once_with("job.json")
