"""Paseo API model yönetimi.

Bu modül, Paseo üzerinden kullanılabilen ücretsiz sağlayıcı ve modelleri tek
bir JSON kayıt defterinden yönetir. Varsayılan model `glm-5.3`'tür.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_REGISTRY_PATH = Path(__file__).with_name("models.json")


@dataclass(frozen=True)
class Model:
    id: str
    label: str
    provider: str
    free: bool = False
    default: bool = False


@dataclass(frozen=True)
class Provider:
    id: str
    label: str
    api: str
    free: bool = False
    models: tuple[Model, ...] = ()


class ModelRegistry:
    """Paseo sağlayıcı ve modellerini temsil eden kayıt defteri."""

    def __init__(self, providers: tuple[Provider, ...], default: str) -> None:
        self._providers = providers
        self._default = default
        self._models: dict[str, Model] = {}
        for provider in providers:
            for model in provider.models:
                if model.id in self._models:
                    raise ValueError(f"model kimliği tekrar ediyor: {model.id}")
                self._models[model.id] = model
        if default not in self._models:
            raise ValueError(f"varsayılan model kayıt defterinde yok: {default}")

    @classmethod
    def from_json(cls, path: Path = DEFAULT_REGISTRY_PATH) -> "ModelRegistry":
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
        except FileNotFoundError as exc:
            raise ValueError(f"model kayıt defteri bulunamadı: {path}") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"model kayıt defteri bozuk JSON: {path}") from exc
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ModelRegistry":
        default = raw.get("default")
        if not isinstance(default, str) or not default:
            raise ValueError("models.json içinde 'default' zorunludur")
        providers_raw = raw.get("providers")
        if not isinstance(providers_raw, list):
            raise ValueError("models.json içinde 'providers' listesi zorunludur")

        providers: list[Provider] = []
        for provider_raw in providers_raw:
            if not isinstance(provider_raw, dict):
                raise ValueError("her sağlayıcı bir nesne olmalı")
            provider_id = provider_raw.get("id")
            provider_label = provider_raw.get("label")
            provider_api = provider_raw.get("api")
            if not all(isinstance(value, str) and value
                       for value in (provider_id, provider_label, provider_api)):
                raise ValueError("sağlayıcı 'id', 'label' ve 'api' zorunludur")

            models_raw = provider_raw.get("models")
            if not isinstance(models_raw, list):
                raise ValueError(f"{provider_id} sağlayıcısında 'models' listesi zorunludur")
            models: list[Model] = []
            for model_raw in models_raw:
                if not isinstance(model_raw, dict):
                    raise ValueError(f"{provider_id} içindeki her model nesne olmalı")
                model_id = model_raw.get("id")
                model_label = model_raw.get("label")
                if not isinstance(model_id, str) or not model_id:
                    raise ValueError("model 'id' zorunludur")
                if not isinstance(model_label, str) or not model_label:
                    raise ValueError(f"{model_id} için 'label' zorunludur")
                models.append(Model(
                    id=model_id,
                    label=model_label,
                    provider=provider_id,
                    free=bool(model_raw.get("free", provider_raw.get("free", False))),
                    default=bool(model_raw.get("default", False)),
                ))
            providers.append(Provider(
                id=provider_id,
                label=provider_label,
                api=provider_api,
                free=bool(provider_raw.get("free", False)),
                models=tuple(models),
            ))
        return cls(tuple(providers), default)

    @property
    def default(self) -> Model:
        return self._models[self._default]

    def free_models(self) -> tuple[Model, ...]:
        return tuple(model for model in self._models.values() if model.free)

    def model(self, model_id: str) -> Model:
        try:
            return self._models[model_id]
        except KeyError as exc:
            raise ValueError(f"bilinmeyen model: {model_id}") from exc

    def providers(self) -> tuple[Provider, ...]:
        return self._providers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paseo model yönetimi")
    sub = parser.add_subparsers(dest="komut", required=True)
    sub.add_parser("list", help="tüm sağlayıcı ve modelleri listele")
    sub.add_parser("default", help="varsayılan modeli göster")
    sub.add_parser("free", help="ücretsiz modelleri listele")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = ModelRegistry.from_json()
    if args.komut == "list":
        for provider in registry.providers():
            print(f"{provider.id} — {provider.label}")
            for model in provider.models:
                suffix = " [ücretsiz]" if model.free else ""
                default = " [varsayılan]" if model.id == registry.default.id else ""
                print(f"  {model.id} — {model.label}{suffix}{default}")
    elif args.komut == "default":
        model = registry.default
        print(f"{model.id} — {model.label} ({model.provider})")
    elif args.komut == "free":
        for model in registry.free_models():
            print(f"{model.id} — {model.label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
