"""Site bazlı güvenli kullanım sınırları ve pilot deneme planı.

Bu tavanlar platform garantisi değildir; hesap yasağı riskini düşürmek için
muhafazakâr biçimde seçilmiş iç limitlerdir. Her site için okuma, yazma ve
gonderme eylemleri ayrı ayrı sınırlandırılır.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from policygate import audit


@dataclass(frozen=True)
class EylemLimiti:
    saatlik: int
    gunluk: int
    seri: int
    bekleme_saniye: int


@dataclass(frozen=True)
class SiteProfili:
    site: str
    risk: str
    okuma: EylemLimiti
    yazma: EylemLimiti
    gonderme: EylemLimiti
    pilot_adim: int
    pilot_aralik_saniye: int


PROFILLER: dict[str, SiteProfili] = {
    "github": SiteProfili(
        "github", "orta",
        EylemLimiti(60, 240, 10, 30),
        EylemLimiti(10, 40, 2, 300),
        EylemLimiti(5, 20, 1, 900), 5, 300,
    ),
    "gmail": SiteProfili(
        "gmail", "orta",
        EylemLimiti(30, 120, 5, 60),
        EylemLimiti(5, 20, 1, 600),
        EylemLimiti(2, 10, 1, 1800), 5, 600,
    ),
    "x": SiteProfili(
        "x", "yüksek",
        EylemLimiti(20, 80, 4, 180),
        EylemLimiti(4, 16, 1, 900),
        EylemLimiti(1, 5, 1, 3600), 3, 900,
    ),
    "linkedin": SiteProfili(
        "linkedin", "yüksek",
        EylemLimiti(30, 120, 5, 120),
        EylemLimiti(5, 20, 1, 900),
        EylemLimiti(2, 8, 1, 1800), 3, 900,
    ),
    "youtube": SiteProfili(
        "youtube", "orta",
        EylemLimiti(50, 200, 10, 60),
        EylemLimiti(5, 20, 1, 900),
        EylemLimiti(2, 10, 1, 1800), 5, 300,
    ),
    "chatgpt": SiteProfili(
        "chatgpt", "yüksek",
        EylemLimiti(10, 50, 3, 300),
        EylemLimiti(2, 10, 1, 1800),
        EylemLimiti(1, 5, 1, 3600), 3, 1800,
    ),
    "canva": SiteProfili(
        "canva", "orta",
        EylemLimiti(20, 80, 5, 120),
        EylemLimiti(5, 20, 1, 900),
        EylemLimiti(2, 10, 1, 1800), 3, 900,
    ),
    "supabase": SiteProfili(
        "supabase", "düşük",
        EylemLimiti(60, 240, 10, 30),
        EylemLimiti(10, 40, 2, 300),
        EylemLimiti(5, 20, 1, 900), 5, 300,
    ),
    "vercel": SiteProfili(
        "vercel", "düşük",
        EylemLimiti(60, 240, 10, 30),
        EylemLimiti(10, 40, 2, 300),
        EylemLimiti(5, 20, 1, 900), 5, 300,
    ),
}

_SEVIYELER = {"okuma": "READ", "yazma": "MODIFY", "gonderme": "SEND"}
_IC_KOMUTLAR = {"site-kesfet", "son-kayitlar", "audit-dogrula", "zamanla"}


def siteler() -> list[str]:
    return sorted(PROFILLER)


def profil_al(site: str) -> SiteProfili:
    try:
        return PROFILLER[site]
    except KeyError as exc:
        raise ValueError(f"Bilinmeyen site: {site}") from exc


def _durum_yolu() -> Path:
    return Path(os.environ.get("SITE_LIMIT_STATE", "data/site_limits.json"))


def _durum_oku() -> dict[str, Any]:
    yol = _durum_yolu()
    if not yol.exists():
        return {}
    try:
        return json.loads(yol.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Site limit durumu okunamadi") from exc


def _durum_yaz(durum: dict[str, Any]) -> None:
    yol = _durum_yolu()
    yol.parent.mkdir(parents=True, exist_ok=True)
    gecici = yol.with_suffix(yol.suffix + ".tmp")
    gecici.write_text(
        json.dumps(durum, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )
    os.replace(gecici, yol)


def pilot_plani(site: str, eylem: str = "okuma") -> list[dict[str, Any]]:
    profil = profil_al(site)
    return [
        {
            "adim": adim,
            "eylem": eylem,
            "bekleme_saniye": 0 if adim == 1 else profil.pilot_aralik_saniye,
        }
        for adim in range(1, profil.pilot_adim + 1)
    ]


def kesfet(site: str | None = None) -> dict[str, Any]:
    if site is None:
        return {
            "siteler": [
                {
                    "site": ad,
                    "risk": PROFILLER[ad].risk,
                    "okuma_saatlik": PROFILLER[ad].okuma.saatlik,
                    "yazma_saatlik": PROFILLER[ad].yazma.saatlik,
                    "gonderme_saatlik": PROFILLER[ad].gonderme.saatlik,
                }
                for ad in siteler()
            ]
        }
    profil = profil_al(site)
    return {
        "site": site,
        "risk": profil.risk,
        "limitler": {
            "okuma": asdict(profil.okuma),
            "yazma": asdict(profil.yazma),
            "gonderme": asdict(profil.gonderme),
        },
        "pilot": pilot_plani(site),
        "durum": _durum_oku().get(site, {}),
    }


def kontrol_et(
    site: str,
    eylem: str,
    adet: int = 1,
    simdi: datetime | None = None,
) -> dict[str, Any]:
    if eylem not in _SEVIYELER:
        raise ValueError(f"Geçersiz eylem: {eylem}")
    if adet < 1:
        raise ValueError("Adet en az 1 olmalı")

    profil = profil_al(site)
    limit = getattr(profil, eylem)
    an = simdi or datetime.now(timezone.utc)
    durum = _durum_oku()
    site_durumu = durum.get(site, {})
    eylem_durumu = site_durumu.get(eylem, {})

    saat_anahtari = an.strftime("%Y-%m-%dT%H")
    gun_anahtari = an.strftime("%Y-%m-%d")
    if eylem_durumu.get("saat") != saat_anahtari:
        eylem_durumu["saat"] = saat_anahtari
        eylem_durumu["saat_sayisi"] = 0
    if eylem_durumu.get("gun") != gun_anahtari:
        eylem_durumu["gun"] = gun_anahtari
        eylem_durumu["gun_sayisi"] = 0

    son = eylem_durumu.get("son")
    if son:
        son_an = datetime.fromisoformat(son)
        gecen_sure = (an - son_an).total_seconds()
        if gecen_sure < limit.bekleme_saniye:
            return _ret(
                False, "bekleme_suresi",
                f"{site}/{eylem} için {limit.bekleme_saniye} saniye bekleme var",
                eylem_durumu, limit,
            )

    if adet > limit.seri:
        return _ret(
            False, "seri_limiti",
            f"{site}/{eylem} için tek istekte en fazla {limit.seri} adım var",
            eylem_durumu, limit,
        )
    if eylem_durumu["saat_sayisi"] + adet > limit.saatlik:
        return _ret(
            False, "saat_limiti",
            f"{site}/{eylem} saatlik tavanı {limit.saatlik}",
            eylem_durumu, limit,
        )
    if eylem_durumu["gun_sayisi"] + adet > limit.gunluk:
        return _ret(
            False, "gun_limiti",
            f"{site}/{eylem} günlük tavanı {limit.gunluk}",
            eylem_durumu, limit,
        )

    eylem_durumu["saat_sayisi"] += adet
    eylem_durumu["gun_sayisi"] += adet
    eylem_durumu["son"] = an.isoformat()
    site_durumu[eylem] = eylem_durumu
    durum[site] = site_durumu
    _durum_yaz(durum)

    audit.log_event(
        "site_limit", site, _SEVIYELER[eylem], "auto",
        {
            "eylem": eylem,
            "adet": adet,
            "saat_sayisi": eylem_durumu["saat_sayisi"],
            "gun_sayisi": eylem_durumu["gun_sayisi"],
        },
    )
    return _ret(True, None, None, eylem_durumu, limit)


def pilot(
    site: str,
    eylem: str = "okuma",
    adim: int = 1,
) -> dict[str, Any]:
    profil = profil_al(site)
    if adim < 1 or adim > profil.pilot_adim:
        return {
            "izinli": False,
            "neden": "pilot_adim_limiti",
            "mesaj": f"{site} için en fazla {profil.pilot_adim} pilot adımı var",
            "pilot": pilot_plani(site, eylem),
        }
    sonuc = kontrol_et(site, eylem, adim)
    sonuc["pilot"] = pilot_plani(site, eylem)
    return sonuc


def komut_haritasi(komut: str) -> tuple[str, str] | None:
    if komut in _IC_KOMUTLAR:
        return None
    site = komut.split("-", 1)[0]
    if site not in PROFILLER:
        return None
    if komut.endswith((
        "arastir", "issues", "ara", "bookmarks", "profil", "akis",
        "durum", "log", "detay", "oynatma-listesi", "dogrula", "sorgu",
    )):
        return site, "okuma"
    if komut.endswith((
        "taslak", "pr", "export", "token-yenile", "kur", "tasi",
    )):
        return site, "yazma"
    if komut.endswith(("gonder", "paylas", "iptal")):
        return site, "gonderme"
    return None


def _ret(
    izinli: bool,
    neden: str | None,
    mesaj: str | None,
    durum: dict[str, Any],
    limit: EylemLimiti,
) -> dict[str, Any]:
    return {
        "izinli": izinli,
        "neden": neden,
        "mesaj": mesaj,
        "durum": durum,
        "limit": asdict(limit),
    }
