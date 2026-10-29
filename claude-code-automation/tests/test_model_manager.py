"""model_manager birim testleri — offline."""
from __future__ import annotations
import io, json, subprocess, tempfile, unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
from model_manager import PASEO_COMMAND, ModelRegistry, ask_model, main
def _result(stdout: str = "", stderr: str = "", returncode: int = 0):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)
class ModelManagerTests(unittest.TestCase):
    def test_varsayilan_model_glm_5_3(self):
        model = ModelRegistry.from_json().default
        self.assertEqual((model.id, model.api), ("glm-5.3", "claude-glm"))
        self.assertTrue(model.free)
    def test_ucretsiz_modeller_listelenir(self):
        free_ids = {model.id for model in ModelRegistry.from_json().free_models()}
        self.assertTrue({"glm-5.3", "glm-5.2", "codefastglm53unlimited"}.issubset(free_ids))
    def test_saglayici_bilgisi_dogru(self):
        providers = {provider.id: provider for provider in ModelRegistry.from_json().providers()}
        self.assertEqual((providers["claude-glm"].api, providers["glm53u-codex"].api), ("claude-glm", "glm53u-codex"))
        self.assertTrue(providers["claude-glm"].free)
    def test_bilinmeyen_model_hata_verir(self):
        with redirect_stderr(io.StringIO()) as stderr:
            self.assertEqual(main(["sor", "test", "--model", "olmayan-model"]), 1)
        self.assertIn("bilinmeyen model", stderr.getvalue())
    def test_bozuk_json_hata_verir(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "models.json"
            path.write_text("{bozuk", encoding="utf-8")
            self.assertRaises(ValueError, ModelRegistry.from_json, path)
    def test_eksik_default_hata_verir(self):
        self.assertRaises(ValueError, ModelRegistry.from_dict, {"providers": []})
    def test_tekrar_eden_model_kimligi_hata_verir(self):
        raw = {"default": "glm-5.3", "providers": [{
            "id": "p", "label": "P", "api": "p", "free": True,
            "models": [{"id": "glm-5.3", "label": "GLM"}, {"id": "glm-5.3", "label": "Again"}],
        }]}
        self.assertRaises(ValueError, ModelRegistry.from_dict, raw)
    def test_sor_kayitli_modeli_yapistirir_ve_yanit_doner(self):
        captured = {}
        def runner(command, **kwargs):
            captured.update(command=command, kwargs=kwargs)
            return _result(json.dumps({"yanit": "hazır"}))
        self.assertEqual(ask_model(ModelRegistry.from_json().default, "hazır mı?", runner), "hazır")
        self.assertEqual((captured["command"][0], captured["command"][5]), (PASEO_COMMAND, "claude-glm"))
        self.assertIn("glm-5.3", captured["command"])
        self.assertTrue(captured["kwargs"]["capture_output"])
    def test_sor_hatasinda_secret_redakte_edilir(self):
        secret = "PASEO_API_KEY=gizli-deger-123"
        runner = lambda *args, **kwargs: _result(stderr=secret, returncode=1)
        with self.assertRaises(RuntimeError) as context:
            ask_model(ModelRegistry.from_json().default, "test", runner)
        self.assertNotIn("gizli-deger-123", str(context.exception))
        self.assertIn("***", str(context.exception))
    def test_sor_gecersiz_yanit_hata_verir(self):
        with redirect_stderr(io.StringIO()), patch("model_manager.ask_model", return_value="yanıt"):
            self.assertEqual(main(["sor", "test"]), 0)
        with self.assertRaises(RuntimeError):
            ask_model(ModelRegistry.from_json().default, "test", lambda *args, **kwargs: _result('{"yanit": 12}'))
if __name__ == "__main__":
    unittest.main()
