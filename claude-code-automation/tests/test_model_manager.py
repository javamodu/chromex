"""model_manager birim testleri — offline."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from model_manager import ModelRegistry


class ModelManagerTests(unittest.TestCase):
    def test_varsayilan_model_glm_5_3(self):
        registry = ModelRegistry.from_json()
        self.assertEqual(registry.default.id, "glm-5.3")
        self.assertTrue(registry.default.free)

    def test_ucretsiz_modeller_listelenir(self):
        registry = ModelRegistry.from_json()
        free_ids = {model.id for model in registry.free_models()}
        self.assertIn("glm-5.3", free_ids)
        self.assertIn("codefastglm53unlimited", free_ids)

    def test_saglayici_bilgisi_dogru(self):
        registry = ModelRegistry.from_json()
        provider = registry.providers()[0]
        self.assertEqual(provider.id, "paseo")
        self.assertEqual(provider.api, "paseo")
        self.assertTrue(provider.free)

    def test_bilinmeyen_model_hata_verir(self):
        registry = ModelRegistry.from_json()
        with self.assertRaises(ValueError):
            registry.model("olmayan-model")

    def test_bozuk_json_hata_verir(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "models.json"
            path.write_text("{bozuk", encoding="utf-8")
            with self.assertRaises(ValueError):
                ModelRegistry.from_json(path)

    def test_eksik_default_hata_verir(self):
        raw = {"providers": []}
        with self.assertRaises(ValueError):
            ModelRegistry.from_dict(raw)

    def test_tekrar_eden_model_kimligi_hata_verir(self):
        raw = {
            "default": "glm-5.3",
            "providers": [
                {
                    "id": "paseo",
                    "label": "Paseo",
                    "api": "paseo",
                    "free": True,
                    "models": [
                        {"id": "glm-5.3", "label": "GLM 5.3", "free": True},
                        {"id": "glm-5.3", "label": "GLM 5.3 Again", "free": True},
                    ],
                }
            ],
        }
        with self.assertRaises(ValueError):
            ModelRegistry.from_dict(raw)


if __name__ == "__main__":
    unittest.main()
