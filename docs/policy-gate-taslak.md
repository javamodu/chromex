# policygate — Bağımsız pip Paketi Taslağı

**Durum:** v1.0.0 yayına hazır — v0.2/v0.3/v0.4 tamamlandı (29+35 test OK);
kalan yalnızca manuel PyPI adımları (aşağıda).
**Tarih:** 2026-10-08

## Neden?

Chromex'in asıl farklılaştırıcı parçası worker'lar değil, **güvenlik çekirdeği**:
onay kapısı + policy + audit zinciri + secret redaksiyonu. Bu çekirdek
`windows-browser-automation/core/` içinde gömülü; başka projelerin kullanması
için kopyala-yapıştır gerekiyor. Paketleşirse:

1. Her ajan projesi `pip install policy-gate` ile aynı güvenlik katmanını alır.
2. Zincir formatı tek yerden yönetilir (drift riski biter).
3. Chromex "kullanıcı" konumuna geçer; paket kendi başına değer üretir.

## Kapsam

| Modül | Dahil? | Not |
|---|---|---|
| approval.py | ✅ | 5 seviye, tam-detay EVET, fail-closed non-interactive |
| audit.py | ✅ | SHA-256 zincir, çapraz-platform kilit, kuyruk okuma |
| policy.py | ✅ | fail-safe yükleme, DELETE asla auto olamaz |
| secrets.py | ✅ | redaksiyon kaydı + .env yükleyici |
| log.py | ✅ | OTOMASYON_LOG seviyeli stderr logu |
| http.py | ❌ | `requests` bağımlı — stdlib-only vaadini bozar; `policygate[http]` extrası ileride değerlendirilebilir |
| store.py | ❌ | Chromex'e özgü araştırma deposu |

**Sert kısıt:** zincir formatı değişmez — `claude-code-automation/audit_bridge.py`
ve mevcut `windows-browser-automation` audit dosyalarıyla birebir uyum.

## Rakip/Fark Analizi

| Yaklaşım | Onay kapısı | Audit kanıtı | Bağımlılık |
|---|---|---|---|
| LangChain / LangGraph | insan onayı callback'i var, zorunlu değil | yok | ağır |
| OpenAI Agents SDK | guardrail (içerik odaklı) | yok | SDK |
| MCP | sunucu bazlı, standart onay katmanı yok | yok | protokol |
| n8n / Zapier | workflow onayı adım olarak var | platform logu | SaaS |
| **policygate** | 5 seviye + fail-closed + tam-detay EVET | SHA-256 zincir, kurcalama kanıtı | **sıfır** |

Zayıf yanlar (dürüst not): tek dil (Python), UI yok, tek-kullanıcılı terminal
onayı (webhook/Slack onayı yol haritasında).

## Migrasyon Planı (windows-browser-automation)

1. `pip install -e ./policy-gate` (CI'a da aynı adım eklenir).
2. `core/{approval,audit,policy,secrets,log}.py` ince shim'e döner:
   `from policygate.approval import *  # noqa: F401,F403` — geriye uyumlu.
3. Testler aynen geçmeli (import yolları `core.*` kalabilir, shim üzerinden).
4. v0.2'de shim'ler silinir, doğrudan `policygate.*` import'una geçilir.

## Yol Haritası

- **v0.1** ✅ iskelet, testler, editable install
- **v0.2** ✅ wba cutover: shim'siz doğrudan import; CI iki paketli
- **v0.3** ✅ onay kanalı soyutlaması: ApprovalChannel protokolü,
  TerminalChannel, WebhookChannel (fail-closed), set_channel
- **v0.4** ✅ `py.typed`, policy şema doğrulaması, `policygate[http]` extra
  (http modülü pakete taşındı; wba'ya ince köprü kaldı)
- **v1.0** ✅ yayın hazırlığı: LICENSE (MIT), publish-policygate.yml
  (trusted publisher), sürüm 1.0.0

Kalan MANUEL adımlar (hesap/izin gerektirir):
1. ~~Paket adı kontrolü~~ ✅ `policygate` doluydu → `policy-gate` alındı (müsait)
2. PyPI projesinde bu repo + publish-policygate.yml + "pypi" environment
   ile trusted publisher tanımı (pending publisher: proje adı policy-gate)
3. ~~pyproject.toml'a gerçek repo URL'si~~ ✅ javamodu/chromex
4. GitHub Release aç → otomatik yayın
