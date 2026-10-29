# SÖZLÜK — Chromex

## Temel

| Terim | Anlamı |
|---|---|
| SSOT | Tek doğru kaynak; aynı bilgi tek yerde yaşar |
| Fail-closed | Hata/şüphe durumunda sistem kapanır, işlem reddedilir |
| Audit zinciri | Her kayıt önceki kaydın SHA-256 hash’ini taşır |
| Onay kapısı | SEND/MODIFY/DELETE gibi dış etkili işlemler için insan onayı ister |
| Preflight | Ağ/IO öncesi kesin redleri yakalar |
| LOC | Satır sayısı; tavan takibi için kullanılır |
| Sprint | Belirli çıktı ve testlerle sınırlı kısa iş paketi |

## Mimari

| Terim | Anlamı |
|---|---|
| policygate | Onay, audit, policy, secret, log ve HTTP çekirdeği |
| wba | `windows-browser-automation` alt sistemi |
| MCP | Model Context Protocol; CLI komutlarını tool’a çevirir |
| CDP | Chrome DevTools Protocol; açık tarayıcı oturumuna bağlanır |
| CLI registry | Komutların tek tablodan derlendiği yapı |
| Tool spec | Bir CLI komutunun MCP şemasına karşılığı |

## Süreç

| Terim | Anlamı |
|---|---|
| Handoff | Görev devri ve bağlam aktarımı |
| STATE_BOARD | Son 3 damganın rolling window’u |
| DERSLER | Negatif bilgi defteri |
| Trusted publisher | PyPI yayını için OIDC tabanlı yetkilendirme |
| Fake-green | Testlerin yeşil görünmesine rağmen gerçek senaryoyu kanıtlamaması |
| Offline test | Ağ/servis çağrısı gerektirmeyen test |
