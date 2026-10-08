# policygate

AI ajanları ve otomasyon betikleri için **onay kapısı + audit zinciri** —
tek dosyalık kopyala-yapıştır güvenlik yerine, pip ile kurulan küçük bir
kütüphane. Sıfır bağımlılık: yalnızca Python standart kütüphanesi.

## Sorun

Bir ajana "şu işleri yap" dediğinizde ajan API çağırır, e-posta gönderir,
deployment iptal eder. Çoğu ajan çerçevesinde bu çağrılar **denetimsizdir**:
ne onay vardır ne de sonradan "kim neyi ne zaman yaptı" sorusunun kanıtı.

## Çözüm

```python
from policygate import ActionRequest, require

require(ActionRequest(
    worker="gmail", action="gmail.send", level="SEND",
    summary="ahmet@ornek.com'a teklif e-postası gönderilecek",
    details={"konu": "Teklif", "boyut": "2.1 KB"},
))
# → policy'ye bakılır, gerekirse terminalde TAM detay gösterilir,
#   yalnızca birebir 'EVET' onay sayılır, karar hash zincirine yazılır.
```

## Beş seviye

| Seviye | Örnek | Varsayılan |
|---|---|---|
| READ | arama, listeleme | auto |
| DRAFT | taslak oluşturma | auto |
| MODIFY | dağıtım iptali | ask |
| SEND | e-posta/post gönderme | ask |
| DELETE | silme | ask (asla auto olamaz) |

Kurallar:
- `always_deny` listesi her şeyin üstündedir.
- Etkileşimsiz oturumda (pipe/cron/CI) SEND ve DELETE **her zaman reddedilir**;
  diğerleri `non_interactive_default` ayarına bakar (varsayılan: deny).
- Bozuk/eksik `policy.json` → güvenli varsayılanlara düşülür (fail-safe).

## Audit zinciri

Her karar `audit/audit.jsonl` dosyasına, bir önceki kaydın SHA-256 hash'iyle
zincirlenerek yazılır. Sonradan kurcalama `verify_chain()` ile tespit edilir:

```python
from policygate import verify_chain
ok, mesaj = verify_chain()   # (True, "Zincir sağlam: 42 kayıt.")
```

- Çok-süreç eşzamanlı yazım `audit.lock` ile güvenli (Windows/POSIX).
- Ekleme maliyeti sabittir; dosya kuyruğu okunarak seq/hash türetilir.
- Bilinen secret değerler (`secrets.get` ile okunmuş) kayda `***` maskeli girer.

## Yapılandırma

`config/policy.json` (veya `POLICY_FILE` ortam değişkeni):

```json
{
  "levels": {"READ": "auto", "DRAFT": "auto", "SEND": "ask",
             "MODIFY": "ask", "DELETE": "ask"},
  "non_interactive_default": "deny",
  "always_deny": ["prod.db_reset"]
}
```

Ortam değişkenleri: `POLICY_FILE`, `AUDIT_DIR`, `OTOMASYON_LOG`.

## Onay kanalları

Varsayılan kanal terminaldir (tam detay + birebir 'EVET'). Gömülü
uygulamalar veya bot köprüleri kendi kanalını takabilir:

```python
from policygate import WebhookChannel, set_channel

# Onayları Slack/mobil köprüye sor (cron'da SEND/DELETE için de):
set_channel(WebhookChannel("https://bot.ornek.com/onay"),
            allow_non_interactive=True)
```

Webhook yanıtı JSON `{"approve": true}` olmalı; ağ hatası red sayılır
(fail-closed) ve kararlar kanal adıyla audit zincirine yazılır.

## Opsiyonel HTTP yardımcısı

`pip install "policygate[http]"` → retry/backoff + secret maskeli hatalar
üreten `policygate.http.request_json` kullanılabilir (requests ister).

## Durum

**1.0.0 — yayına hazır.** `windows-browser-automation` bu paketi doğrudan
kullanıyor (v0.2 cutover tamam). PyPI yayını için kalan manuel adımlar:
paket adı müsaitlik kontrolü, trusted publisher tanımı, gerçek repo URL'si
— bkz. `../docs/policy-gate-taslak.md`.
