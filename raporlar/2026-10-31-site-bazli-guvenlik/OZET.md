# Site Bazlı Güvenlik ve Keşif Raporu

Tarih: 2026-10-31 · Süreç: `plans/FAZ3-SPRINTLER.md` F3-004

## Durum

**Kod tamam, canlı pilot doğrulaması bekliyor.**

Site bazlı iç tavanlar, `site-kesfet` keşif komutu, pilot adım planı ve
kullanım sayacı eklendi. Tavanlar platform garantisi değildir; hesap yasağı
riskini azaltmak için seçilmiş muhafazakâr limitlerdir.

## Uygulanan Sınırlar

Biçim: `saatlik/günlük/seri/bekleme_saniye`.

| Site | Risk | Okuma | Yazma | Gönderme | Pilot |
|---|---|---|---|---|---|
| github | orta | 60/240/10/30 | 10/40/2/300 | 5/20/1/900 | 5 adım · 300 sn |
| gmail | orta | 30/120/5/60 | 5/20/1/600 | 2/10/1/1800 | 5 adım · 600 sn |
| x | yüksek | 20/80/4/180 | 4/16/1/900 | 1/5/1/3600 | 3 adım · 900 sn |
| linkedin | yüksek | 30/120/5/120 | 5/20/1/900 | 2/8/1/1800 | 3 adım · 900 sn |
| youtube | orta | 50/200/10/60 | 5/20/1/900 | 2/10/1/1800 | 5 adım · 300 sn |
| chatgpt | yüksek | 10/50/3/300 | 2/10/1/1800 | 1/5/1/3600 | 3 adım · 1800 sn |
| canva | orta | 20/80/5/120 | 5/20/1/900 | 2/10/1/1800 | 3 adım · 900 sn |
| supabase | düşük | 60/240/10/30 | 10/40/2/300 | 5/20/1/900 | 5 adım · 300 sn |
| vercel | düşük | 60/240/10/30 | 10/40/2/300 | 5/20/1/900 | 5 adım · 300 sn |

## Çıktılar

- `windows-browser-automation/core/site_guvenlik.py` — site profilleri,
  saat/gün/seri/bekleme kontrolleri, atomik durum yazımı, pilot planı.
- `windows-browser-automation/orchestrator/cli.py` — `site-kesfet` komutu;
  dış komutlar yürütmeden önce site/eylem limit kapısından geçer.
- `windows-browser-automation/tests/test_site_guvenlik.py` — 19 offline test.
- Kullanım durumu `data/site_limits.json`; `SITE_LIMIT_STATE` ile
  yönlendirilebilir. Bozuk durum dosyası fail-closed olarak hata verir.
- İç komutlar (`site-kesfet`, `son-kayitlar`, `audit-dogrula`, `zamanla`)
  limit dışıdır; kullanıcıya sanal pilot sayacı şişirmesi yapmaz.

## Kanıtlar

| Komut | Sonuç |
|---|---|
| `python -m unittest tests.test_site_guvenlik -v` | **19 test OK, exit 0** |
| `python -m unittest discover -s tests` (wba) | **139 test OK, exit 0** |
| `python -m unittest discover -s tests` (policygate) | **41 test OK, exit 0** |
| `python -m unittest discover -s tests` (model) | **10 test OK, exit 0** |
| `python scripts/production_check.py` | **28 komut = 28 tool, exit 0** |
| `python scripts/mcp_smoke.py` | **MCP_SMOKE_OK tools=28, exit 0** |
| `git diff --check` | **exit 0** |
| `site-kesfet`, `site-kesfet linkedin`, `site-kesfet linkedin --pilot --adim 1` | **SITE_CLI_OK, exit 0** |

Ölçüm: 190 offline test · 28 MCP tool · 10.806 toplam LOC.

## Bekleyen İnsan Onayı

1. Canlı pilot: `site-kesfet <site> --pilot --adim 1`, ardından aynı sitenin
   tek READ komutu insan denetiminde koşulmalı.
2. Pilot sonucu gerçek API yanıtına göre gözlemlenip tavanlar ayarlanmalı.
3. `chatgpt` için profil hazır; worker ayrı bir sprint gerektirir.
4. Commit/push yalnızca açık kullanıcı isteğiyle yapılmalı.
