# policygate — Bağımsız pip Paketi Taslağı

**Durum:** taslak (v0.1.0 iskeleti `policy-gate/` altında çalışır durumda, 13 test OK)
**Tarih:** 2026-10-08

## Neden?

Chromex'in asıl farklılaştırıcı parçası worker'lar değil, **güvenlik çekirdeği**:
onay kapısı + policy + audit zinciri + secret redaksiyonu. Bu çekirdek
`windows-browser-automation/core/` içinde gömülü; başka projelerin kullanması
için kopyala-yapıştır gerekiyor. Paketleşirse:

1. Her ajan projesi `pip install policygate` ile aynı güvenlik katmanını alır.
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

- **v0.1** (bu taslak): iskelet, 13 test, editable install OK
- **v0.2**: wba cutover (shim → doğrudan import), CI'da iki paket matrisi
- **v0.3**: onay kanalı soyutlaması (terminal dışı: webhook/Slack callback)
- **v0.4**: `py.typed`, policy şema doğrulaması, `policygate[http]` extra
- **v1.0**: PyPI yayını — önce: PyPI'da `policygate` adı müsait mi kontrolü,
  LICENSE dosyası (MIT önerisi), gerçek repo URL'si, `publish.yml` (trusted publisher)

Tahmini ek iş: v1.0'a kadar ~300-400 satır (CI publish, docs, typing, kanal
soyutlaması hariç; kanal soyutlaması +150-200 satır).