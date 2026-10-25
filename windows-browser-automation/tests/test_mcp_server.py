"""MCP adaptörü testleri — offline, gerçek `mcp` paketi gerekmez."""
from __future__ import annotations

import inspect
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from policygate import ActionRequest, ApprovalDenied, approval, audit

from mcp_server import server, tools
from mcp_server.approval import MCPApprovalChannel


class MCPToolTests(unittest.TestCase):
    def test_yirmi_tool_tanimlanir(self):
        self.assertEqual(len(tools.TOOLS), 20)
        self.assertEqual(len({tool.name for tool in tools.TOOLS}), 20)

    def test_schema_ve_cli_eslesmesi(self):
        spec = tools.tool_by_name("github-arastir")
        self.assertIsNotNone(spec)
        self.assertEqual(spec.input_schema["required"], ["sorgu"])
        self.assertEqual(spec.input_schema["properties"]["limit"]["type"], "integer")
        argv = tools.to_cli_args(spec, {"sorgu": "python", "limit": 3})
        self.assertEqual(argv, ["github-arastir", "python", "--limit", "3"])

    def test_store_true_ve_none_eslesmesi(self):
        spec = tools.tool_by_name("github-pr")
        argv = tools.to_cli_args(
            spec,
            {
                "title": "baslik",
                "govde": "govde",
                "base": "dev",
                "head": None,
                "draft": True,
            },
        )
        self.assertEqual(
            argv,
            ["github-pr", "--title", "baslik", "--govde", "govde",
             "--base", "dev", "--draft"],
        )

    def test_execute_tool_cli_main_cagirir(self):
        with mock.patch.object(tools.cli, "main", return_value=0) as main:
            result = tools.execute_tool(
                "github-arastir", {"sorgu": "python", "limit": 3}
            )
        self.assertEqual(result["exitCode"], 0)
        self.assertEqual(
            main.call_args.args[0], ["github-arastir", "python", "--limit", "3"]
        )

    def test_execute_tool_secret_redakte(self):
        os.environ['CHROMEX_TEST_SECRET'] = 'GIZLI-TOKEN'
        tools.secrets.get('CHROMEX_TEST_SECRET')
        try:
            with mock.patch.object(
                tools.cli,
                'main',
                side_effect=lambda argv: print('token=GIZLI-TOKEN'),
            ):
                result = tools.execute_tool(
                    'github-arastir', {'sorgu': 'python'}
                )
        finally:
            os.environ.pop('CHROMEX_TEST_SECRET', None)
            tools.secrets._REGISTERED.discard('GIZLI-TOKEN')
        self.assertNotIn('GIZLI-TOKEN', result['stdout'])
        self.assertIn('***', result['stdout'])

    def test_execute_tool_bilinmeyen_arguman_red(self):
        result = tools.execute_tool("github-arastir", {"sorgu": "x", "foo": 1})
        self.assertEqual(result["exitCode"], 2)
        self.assertIn("bilinmeyen argüman", result["stderr"])


class MCPApprovalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        os.environ["AUDIT_DIR"] = str(Path(self.tmp.name) / "audit")
        os.environ["POLICY_FILE"] = str(Path(self.tmp.name) / "yok.json")
        self._cwd = os.getcwd()
        os.chdir(self.tmp.name)

    def tearDown(self):
        approval.set_channel(approval.TerminalChannel())
        os.chdir(self._cwd)
        self.tmp.cleanup()
        for key in ("AUDIT_DIR", "POLICY_FILE"):
            os.environ.pop(key, None)

    def test_mcp_onay_red_audit_yazar(self):
        req = ActionRequest(
            worker="mcp",
            action="gmail.send_draft",
            level="SEND",
            summary="test gönderimi",
            details={"draft_id": "d1"},
        )
        approval.set_channel(
            MCPApprovalChannel(lambda _: False),
            allow_non_interactive=True,
        )
        with self.assertRaises(ApprovalDenied):
            approval.require(req)
        path = Path(os.environ["AUDIT_DIR"]) / "audit.jsonl"
        self.assertTrue(path.exists())
        self.assertIn("action_user_rejected", path.read_text(encoding="utf-8"))
        self.assertTrue(audit.verify_chain()[0])

    def test_callback_hatasi_red_sayilir(self):
        channel = MCPApprovalChannel(
            lambda _: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        req = ActionRequest(
            worker="mcp", action="test", level="SEND", summary="test"
        )
        self.assertFalse(channel.ask(req))

    def test_varsayilan_callback_red(self):
        req = ActionRequest(worker="mcp", action="test", level="SEND", summary="test")
        self.assertFalse(MCPApprovalChannel().ask(req))


class FakeMCPServer:
    def __init__(self, name):
        self.name = name
        self.registered = []

    def tool(self):
        def decorator(fn):
            self.registered.append((fn.__name__, fn.__doc__, fn))
            return fn

        return decorator


class MCPServerTests(unittest.TestCase):
    def test_register_tools_imza_ve_cagri(self):
        fake = FakeMCPServer("test")
        server.register_tools(fake)
        self.assertEqual(len(fake.registered), 20)
        name, description, fn = fake.registered[0]
        self.assertEqual(name, "github-arastir")
        self.assertEqual(description, "GitHub repo araması")
        signature = inspect.signature(fn)
        self.assertIn("sorgu", signature.parameters)
        self.assertIs(signature.parameters["limit"].annotation, int)
        with mock.patch.object(
            server, "execute_tool", return_value={"exitCode": 0}
        ) as exec_tool:
            result = fn(sorgu="python", limit=3)
        self.assertEqual(result["exitCode"], 0)
        self.assertEqual(exec_tool.call_args.args, ("github-arastir",))
        self.assertEqual(
            exec_tool.call_args.kwargs, {"sorgu": "python", "limit": 3}
        )

    def test_create_server_eksik_mcp_paketinde_yonlendirir(self):
        with mock.patch.dict(sys.modules, {"mcp": None}):
            with self.assertRaises(RuntimeError) as ctx:
                server.create_server()
        self.assertIn("chromex-otomasyon[mcp]", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
