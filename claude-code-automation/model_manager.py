"""Paseo model yönetimi ve güvenli soru komutu."""
from __future__ import annotations
import argparse, json, re, shutil, subprocess, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
DEFAULT_REGISTRY_PATH = Path(__file__).with_name("models.json")
PASEO_COMMAND = shutil.which("paseo") or "paseo"
OUTPUT_SCHEMA = '{"type":"object","required":["yanit"],"properties":{"yanit":{"type":"string"}}}'
Runner = Callable[..., subprocess.CompletedProcess[str]]
_SECRETS = (
    re.compile(r"(?i)(paseo[_-]?api[_-]?key\s*[=:]\s*)[^\s]+"),
    re.compile(r"(?i)(authorization\s*:\s*Bearer\s+)[^\s]+"),
)
@dataclass(frozen=True)
class Model:
    id: str; label: str; provider: str; api: str; run_id: str; free: bool = False
@dataclass(frozen=True)
class Provider:
    id: str; label: str; api: str; free: bool = False; models: tuple[Model, ...] = ()
def _redact(text: str) -> str:
    for pattern in _SECRETS:
        text = pattern.sub(r"\1***", text)
    return text
def _console_safe(text: str) -> str:
    return text.encode("cp1252", errors="replace").decode("cp1252")
def _text(raw: dict[str, Any], key: str, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{context} '{key}' zorunludur")
    return value
class ModelRegistry:
    """Paseo sağlayıcı ve modellerini temsil eden kayıt defteri."""
    def __init__(self, providers: tuple[Provider, ...], default: str) -> None:
        self._providers = providers
        self._models: dict[str, Model] = {}
        for provider in providers:
            for model in provider.models:
                if model.id in self._models:
                    raise ValueError(f"model kimliği tekrar ediyor: {model.id}")
                self._models[model.id] = model
        if default not in self._models:
            raise ValueError(f"varsayılan model kayıt defterinde yok: {default}")
        self._default = default
    @classmethod
    def from_json(cls, path: Path = DEFAULT_REGISTRY_PATH) -> "ModelRegistry":
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise ValueError(f"model kayıt defteri okunamadı: {path}") from exc
        return cls.from_dict(raw)
    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "ModelRegistry":
        default = raw.get("default")
        providers_raw = raw.get("providers")
        if not isinstance(default, str) or not default:
            raise ValueError("models.json içinde 'default' zorunludur")
        if not isinstance(providers_raw, list):
            raise ValueError("models.json içinde 'providers' listesi zorunludur")
        providers: list[Provider] = []
        for provider_raw in providers_raw:
            if not isinstance(provider_raw, dict):
                raise ValueError("her sağlayıcı bir nesne olmalı")
            provider_id = _text(provider_raw, "id", "sağlayıcı")
            provider_label = _text(provider_raw, "label", "sağlayıcı")
            provider_api = _text(provider_raw, "api", "sağlayıcı")
            models_raw = provider_raw.get("models")
            if not isinstance(models_raw, list):
                raise ValueError(f"{provider_id} için 'models' listesi zorunludur")
            models = tuple(
                Model(
                    _text(model_raw, "id", "model"),
                    _text(model_raw, "label", "model"),
                    provider_id,
                    provider_api,
                    _text(model_raw, "run_id", "model") if "run_id" in model_raw else _text(model_raw, "id", "model"),
                    bool(model_raw.get("free", provider_raw.get("free", False))),
                )
                for model_raw in models_raw
                if isinstance(model_raw, dict)
            )
            if len(models) != len(models_raw):
                raise ValueError(f"{provider_id} içindeki her model nesne olmalı")
            providers.append(Provider(provider_id, provider_label, provider_api, bool(provider_raw.get("free", False)), models))
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
def ask_model(model: Model, question: str, runner: Runner = subprocess.run) -> str:
    """Kayıtlı modelle araçsız, plan modunda tek soru sorar."""
    command = [
        PASEO_COMMAND, "run", "--title", "Chromex model sorusu",
        "--provider", model.api, "--model", model.run_id, "--mode", "plan",
        "--wait-timeout", "180s", "--output-schema", OUTPUT_SCHEMA, "--json",
        f"Araç kullanma. Yalnızca şu soruya yanıt ver: {question}",
    ]
    result = runner(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=210, check=False)
    if result.returncode != 0:
        raw = f"{result.stdout}\n{result.stderr}".strip()
        raise RuntimeError(_redact(raw or "Paseo çağrısı başarısız oldu."))
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Paseo geçerli JSON döndürmedi.") from exc
    if not isinstance(data, dict) or not isinstance(data.get("yanit"), str):
        raise RuntimeError(_redact(result.stdout))
    if "error" in data:
        raise RuntimeError(_redact(str(data["error"])))
    return data["yanit"]
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Paseo model yönetimi")
    sub = parser.add_subparsers(dest="komut", required=True)
    sub.add_parser("list", help="tüm sağlayıcı ve modelleri listele")
    sub.add_parser("default", help="varsayılan modeli göster")
    sub.add_parser("free", help="ücretsiz modelleri listele")
    sor = sub.add_parser("sor", help="varsayılan modelle güvenli soru sor")
    sor.add_argument("soru", help="modele gönderilecek soru")
    sor.add_argument("--model", help="kayıtlı model kimliği")
    return parser
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        registry = ModelRegistry.from_json()
        if args.komut == "list":
            for provider in registry.providers():
                print(f"{provider.id} — {provider.label}")
                for model in provider.models:
                    free = " [ücretsiz]" if model.free else ""
                    default = " [varsayılan]" if model.id == registry.default.id else ""
                    print(f"  {model.id} — {model.label}{free}{default}")
        elif args.komut == "default":
            model = registry.default
            print(f"{model.id} — {model.label} ({model.provider})")
        elif args.komut == "free":
            for model in registry.free_models():
                print(f"{model.id} — {model.label}")
        else:
            model = registry.model(args.model or registry.default.id)
            print(_console_safe(ask_model(model, args.soru)))
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(_console_safe(_redact(str(exc))), file=sys.stderr)
        return 1
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
