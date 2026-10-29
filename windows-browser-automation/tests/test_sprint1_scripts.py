"""Sprint 1 smoke ve yerel release yardımcılarının offline testleri."""
from __future__ import annotations

import importlib.util
import io
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from policygate import ApprovalDenied


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _load_module(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeClientSession:
    def __init__(self, read, write, tool_count):
        self.read = read
        self.write = write
        self.tool_count = tool_count

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def initialize(self):
        return None

    async def list_tools(self):
        tools = [
            SimpleNamespace(name=f"tool_{index}")
            for index in range(self.tool_count)
        ]
        return SimpleNamespace(tools=tools)


class FakeTransport:
    def __init__(self, tool_count):
        self.tool_count = tool_count

    async def __aenter__(self):
        return "read", "write"

    async def __aexit__(self, exc_type, exc, traceback):
        return None


def _fake_mcp(tool_count):
    module = types.ModuleType("mcp")
    module.ClientSession = lambda read, write: FakeClientSession(
        read, write, tool_count
    )
    module.StdioServerParameters = lambda **kwargs: SimpleNamespace(**kwargs)
    module.stdio_client = lambda parameters: FakeTransport(tool_count)
    return module


class McpSmokeTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_module("mcp_smoke")
        self.old_mcp = sys.modules.get("mcp")

    def tearDown(self):
        if self.old_mcp is None:
            sys.modules.pop("mcp", None)
        else:
            sys.modules["mcp"] = self.old_mcp

    def test_eksik_mcp_paketi_net_hata_verir(self):
        with mock.patch.dict(sys.modules, {"mcp": None}):
            with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(self.module.main(), 2)
        self.assertIn("missing_dependency", stdout.getvalue())

    def test_yirmi_bir_tool_basarili(self):
        sys.modules["mcp"] = _fake_mcp(21)
        with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(self.module.main(), 0)
        self.assertIn("MCP_SMOKE_OK tools=21", stdout.getvalue())

    def test_eksik_tool_sayisi_kirmizi(self):
        sys.modules["mcp"] = _fake_mcp(19)
        with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            self.assertEqual(self.module.main(), 1)
        self.assertIn("tools=19", stdout.getvalue())


class LocalReleaseTests(unittest.TestCase):
    def setUp(self):
        self.module = _load_module("local_release")
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.policy = self.repo / "policy-gate"
        self.dist = self.policy / "dist"
        self.dist.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_wheel_bulma_ve_tag_eslesmesi(self):
        wheel = self.dist / "policy_gate-1.1.0-py3-none-any.whl"
        wheel.write_bytes(b"wheel")
        self.assertEqual(self.module.find_wheel(self.policy), wheel)
        command = self.module.release_command(self.repo, wheel, "v1.1.0")
        self.assertEqual(command[:4], ["gh", "release", "create", "v1.1.0"])
        self.assertIn("--draft", command)

    def test_tag_eslesmezse_red(self):
        wheel = self.dist / "policy_gate-1.1.0-py3-none-any.whl"
        wheel.write_bytes(b"wheel")
        with self.assertRaises(ValueError):
            self.module.release_command(self.repo, wheel, "v1.0.0")

    def test_build_wheel_cagrisi(self):
        wheel = self.dist / "policy_gate-1.1.0-py3-none-any.whl"
        wheel.write_bytes(b"wheel")
        expected = [sys.executable, "-m", "build", "--wheel", str(self.policy)]
        with mock.patch.object(self.module.subprocess, "run") as run:
            self.assertEqual(self.module.build_wheel(self.repo, self.policy), wheel)
        run.assert_called_once_with(expected, cwd=self.repo, check=True)

    def test_execute_onaysiz_subprocess_cagirmaz(self):
        wheel = self.dist / "policy_gate-1.1.0-py3-none-any.whl"
        wheel.write_bytes(b"wheel")
        command = self.module.release_command(self.repo, wheel, "v1.1.0")
        with mock.patch.object(self.module, "require") as require_mock, \
             mock.patch.object(self.module.subprocess, "run") as run:
            self.module.execute_release(self.repo, wheel, "v1.1.0", command)
        require_mock.assert_called_once()
        run.assert_called_once_with(command, cwd=self.repo, check=True)

    def test_execute_reddedilince_subprocess_cagirmaz(self):
        wheel = self.dist / "policy_gate-1.1.0-py3-none-any.whl"
        wheel.write_bytes(b"wheel")
        command = self.module.release_command(self.repo, wheel, "v1.1.0")
        with mock.patch.object(
                self.module, "require",
                side_effect=ApprovalDenied("red")) as require_mock, \
             mock.patch.object(self.module.subprocess, "run") as run:
            with self.assertRaises(ApprovalDenied):
                self.module.execute_release(
                    self.repo, wheel, "v1.1.0", command)
        require_mock.assert_called_once()
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
