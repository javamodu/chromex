"""Secret kasası — Windows DPAPI ile yerel şifreli token deposu.

Kurallar:
- Token değerleri ASLA düz metin dosyaya yazılmaz; kasa dosyasında yalnızca
  DPAPI blob'ları (base64) bulunur ve değerler terminale basılmaz.
- Kasa bozuksa fail-closed: okuma tek satır mesajla reddedilir.
- Sıfır yeni bağımlılık: DPAPI köprüsü stdlib ctypes ile kurulur.

Dosya biçimi: {"surum": 1, "anahtarlar": {AD: base64(dpapi_blob)}}
"""
from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path

from policygate import secrets

SURUM = 1
WORKER = "kasa"


class KasaHatasi(RuntimeError):
    """Kasa yok/bozuk — kullanıcıya tek satır mesaj taşır."""


def kasa_yolu() -> Path:
    """Kasa dosyası yolu; SECRET_VAULT ile yönlendirilebilir (data/ altı)."""
    return Path(os.environ.get("SECRET_VAULT", "data/secret-kasa.json"))


def _dpapi_koruma(veri: bytes) -> bytes:
    """CryptProtectData — değeri geçerli Windows kullanıcısına bağlar."""
    if sys.platform != "win32":
        raise KasaHatasi("DPAPI yalnızca Windows'ta var; kasa kurulamaz.")
    import ctypes
    import ctypes.wintypes

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_char))]

    kaynak = _Blob(len(veri), ctypes.cast(
        ctypes.create_string_buffer(veri, len(veri)),
        ctypes.POINTER(ctypes.c_char)))
    hedef = _Blob()
    if not ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(kaynak), None, None, None, None, 0,
            ctypes.byref(hedef)):
        raise KasaHatasi("DPAPI CryptProtectData başarısız.")
    try:
        return ctypes.string_at(hedef.pbData, hedef.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(hedef.pbData)


def _dpapi_cozum(blob: bytes) -> bytes:
    """CryptUnprotectData — CryptProtectData'nın tersi."""
    if sys.platform != "win32":
        raise KasaHatasi("DPAPI yalnızca Windows'ta var; kasa okunamaz.")
    import ctypes
    import ctypes.wintypes

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_char))]

    kaynak = _Blob(len(blob), ctypes.cast(
        ctypes.create_string_buffer(blob, len(blob)),
        ctypes.POINTER(ctypes.c_char)))
    hedef = _Blob()
    if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(kaynak), None, None, None, None, 0,
            ctypes.byref(hedef)):
        raise KasaHatasi("DPAPI CryptUnprotectData başarısız.")
    try:
        return ctypes.string_at(hedef.pbData, hedef.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(hedef.pbData)


def yaz(degerler: dict[str, str], yol: Path | None = None) -> None:
    """Değerleri DPAPI ile şifreleyip kasaya yazar (geçici dosya + değiştirme)."""
    hedef = Path(yol or kasa_yolu())
    hedef.parent.mkdir(parents=True, exist_ok=True)
    govde = {
        "surum": SURUM,
        "anahtarlar": {
            ad: base64.b64encode(_dpapi_koruma(deger.encode("utf-8"))).decode("ascii")
            for ad, deger in degerler.items()
        },
    }
    gecici = hedef.with_suffix(hedef.suffix + ".tmp")
    gecici.write_text(json.dumps(govde, ensure_ascii=False, sort_keys=True),
                      encoding="utf-8")
    os.replace(gecici, hedef)


def oku(yol: Path | None = None) -> dict[str, str]:
    """Kasayı okuyup değerleri çözer.

    Kasa yoksa boş sözlük döner (taşım, kasayı ilk kez kurarken de çalışır);
    bozuk kasada KasaHatasi fırlatır — "kasa yok" durumu ayrıca
    secret-dogrula'nın dosya varlık kontrolüyle kullanıcıya bildirilir.
    """
    hedef = Path(yol or kasa_yolu())
    if not hedef.exists():
        return {}
    try:
        ham = json.loads(hedef.read_text(encoding="utf-8"))
        kayitlar = ham["anahtarlar"]
    except Exception:
        raise KasaHatasi(f"Kasa dosyası bozuk: {hedef}") from None
    degerler = {}
    for ad, blob in kayitlar.items():
        try:
            degerler[ad] = _dpapi_cozum(base64.b64decode(blob)).decode("utf-8")
        except Exception:
            raise KasaHatasi(f"Kasa anahtarı çözülemiyor: {ad}") from None
    return degerler


def yukle_env(yol: Path | None = None) -> str | None:
    """Kasadaki değerleri os.environ'a setdefault ile enjekte eder.

    Kasa yoksa sessizce None döner; bozuksa hata mesajı döner (ortama
    dokunulmaz, süreç çökmez — fail-closed ama sessiz değil).
    """
    hedef = Path(yol or kasa_yolu())
    if not hedef.exists():
        return None
    try:
        degerler = oku(hedef)
    except KasaHatasi as exc:
        return str(exc)
    for ad, deger in degerler.items():
        os.environ.setdefault(ad, deger)
        secrets.get(ad)
    return None


def duz_oku(yol: Path) -> dict[str, str]:
    """Düz metin .env dosyasındaki dolu KEY=VALUE çiftlerini okur."""
    degerler: dict[str, str] = {}
    for satir in Path(yol).read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if not satir or satir.startswith("#") or "=" not in satir:
            continue
        ad, _, deger = satir.partition("=")
        ad, deger = ad.strip(), deger.strip().strip('"').strip("'")
        if ad and deger:
            degerler[ad] = deger
    return degerler
