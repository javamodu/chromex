# CHANGELOG — policygate

Bu proje [semver](https://semver.org/lang/tr/) izler.

## [1.1.0] - 2026-10-29

### Eklendi
- `preflight(req)`: ag/IO oncesi erken kapi — policy-deny ve etkilesimsiz
  SEND/DELETE gibi kesin redleri `require()`'dan once yakalar; gecis sessizdir
  (cift onay/cift audit yok). Onay ekrani icin detay okumasi gereken
  akislarda (orn. taslak alicisi) agdan once cagrilir.

### Duzeltildi
- Windows'ta stdin=NUL/DEVNULL iken `isatty()` True donebiliyor; `input()`
  EOFError'u artik cokme yerine red sayiliyor (fail-closed).
- `policy.json` BOM toleransi (PS 5.1 `Set-Content -Encoding UTF8` BOM yazar;
  artik `utf-8-sig` ile okunuyor).
- HTTP retry/backoff mesajlari warning seviyesinde — uzun bekleyisler artik
  varsayilan log seviyesinde gorunur.
- HTTP audit kayitlarinda URL sorgu bolumu tamamen maskeleniyor; token gibi
  query parametreleri zincire dusmuyor.
- `gh` ve `supabase` CLI cagrilarina 60 saniyelik timeout eklendi; takilan
  surecler otomasyonu kilitleyemiyor.

## [1.0.0] - 2026-10-13

Ilk yayin: onay kapisi (READ/DRAFT/SEND/MODIFY/DELETE bes seviye),
TerminalChannel + WebhookChannel, SHA-256 hash-zincirli audit, secret
redaksiyonu, politika dosyasi (policy.json), cp1252-guvenli konsol,
stdlib-only cekirdek; `policy-gate[http]` extra'si.
