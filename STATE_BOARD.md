# STATE_BOARD — chromex

## Aktif iş
Sprint 1 kod kanıtı tamam. Taslak GitHub Release oluşturulmadı: depo
`PUBLIC`, kullanıcı dağıtım istemiyor; yalnızca yerel wheel hazır.

## Son damgalar
- 2026-10-29 · `c928653` · Sprint 1: policygate 1.1.0 wheel üretildi ve kuruldu, gerçek MCP smoke 20 tool exit 0, 105 test yeşil; PyPI workflow kaldırıldı, release komutu taslak modda.
- 2026-10-29 · `586112b` · SSOT çekirdeği kuruldu: ANAYASA, tasarım manifestosu, sözlük, ajan kuralları ve Faz 2 sprint planı; sert LOC tavanı 9.000 (mevcut 7.816); 99 test yeşil.
- 2026-10-29 · `ae7532e` · API model yönetimi eklendi: `glm-5.3` varsayılan, `codefastglm53unlimited` ücretsiz model olarak kayıt defterine alındı; 7 offline test yeşil (toplam 99).
- 2026-10-29 · `4392b91` · Keskin kılıç seti: policygate 36/36 + wba 56/56 test yeşil (toplam 92); HTTP URL redaksiyonu, subprocess timeout, kamu CLI registry ve v1.1.0 senkronu tamam
- 2026-10-25 · Sprint 2: `mcp_server/` adaptörü kuruldu — 20 CLI komutu MCP tool'ı, `MCPApprovalChannel` fail-closed onay köprüsü, `chromex-mcp` giriş noktası, `[mcp]` optional extra; testler 35+53=88 yeşil
- 2026-10-12 · İskelet kuruldu (L1+L5+plans+kararlar+raporlar).
- 2026-10-14 · Gece vardiyası: 2 subagent (CLI insan-testi + drift/plugin) → QA raporu %100 kapandı: 5/5 P1 (EOF fail-closed, tek-satır hata, cp1252, preflight kapısı, google import guardu) + 6/6 işlevsel P2 (BOM toleransı, retry görünürlüğü, exit 3, boş-sonuç mesajı, ok karakterleri, arg help'leri); testler 35+42=77 yeşil; plugin iskeleti kuruldu (.claude-plugin + skills/chromex-sozlesme)

## Bekleyen onaylar
Yok. PyPI ertelendi; GitHub Release yayını bilinçli yapılmadı (depo `PUBLIC`).
