# STATE_BOARD — chromex

## Aktif iş
- bekci raporu: raporlar/takip-sozlesme/2026-10-30.md (untracked — commit bekliyor)
Sprint 4 kod ve canlı koşum tamam: `model_manager.py sor` gerçek `glm-5.3`
çağrısı, kayıt dışı model reddi, secret redaksiyonu ve yapılandırılmış
yanıt şeması eklendi. 41+75+10=126 test, 21 MCP tool ve üretim kontrolü yeşil.

## Son damgalar
- 2026-10-30 · `v1.1.0` · Faz 2 geçiş kapısı kilit etiketi oluşturuldu; kullanıcı yetenek testi bekleniyor.
- 2026-10-30 · `e01207c` · Ajan 477b0083 tam raporu `raporlar/2026-10-30-ajan-477b0083-tam-rapor/OZET.md` altına yazıldı.
- 2026-10-30 · LOC tavanı 9.000→12.000; kod 7.000, doküman 4.500, destek 500 olarak güncellendi; platform matrisi raporu `raporlar/2026-10-30-loc-tavani-artirimi/OZET.md` altına eklendi.
- 2026-10-30 · `de66f6a` · Sprint 4 kapanışı: Paseo CLI üzerinden `glm-5.3` canlı çağrı, 126 offline test, 21 MCP tool ve üretim kontrolü exit 0.
- 2026-10-30 · `b470d37` · Sprint 2 kod kapanışı: `request_bytes`, Canva onay/atomik indirme, audit seq+silme denetimi, release onayı ve `production_check.py` eklendi; 41+70+7=118 test, wheel kurulumu, 20 tool MCP smoke ve üretim kontrolü exit 0.
- 2026-10-29 · `06f2832` · Sprint 1 kapanış: CI run `40924683743` 4/4 success; gerçek MCP smoke 20 tool, policygate wheel kurulumu `1.1.0`, 105 test yeşil.
- 2026-10-29 · `c928653` · Sprint 1: policygate 1.1.0 wheel üretildi ve kuruldu, gerçek MCP smoke 20 tool exit 0, 105 test yeşil; PyPI workflow kaldırıldı, release komutu taslak modda.
- 2026-10-29 · `586112b` · SSOT çekirdeği kuruldu: ANAYASA, tasarım manifestosu, sözlük, ajan kuralları ve Faz 2 sprint planı; sert LOC tavanı 9.000 (mevcut 7.816); 99 test yeşil.
- 2026-10-29 · `ae7532e` · API model yönetimi eklendi: `glm-5.3` varsayılan, `codefastglm53unlimited` ücretsiz model olarak kayıt defterine alındı; 7 offline test yeşil (toplam 99).
- 2026-10-29 · `4392b91` · Keskin kılıç seti: policygate 36/36 + wba 56/56 test yeşil (toplam 92); HTTP URL redaksiyonu, subprocess timeout, kamu CLI registry ve v1.1.0 senkronu tamam
- 2026-10-25 · Sprint 2: `mcp_server/` adaptörü kuruldu — 20 CLI komutu MCP tool'ı, `MCPApprovalChannel` fail-closed onay köprüsü, `chromex-mcp` giriş noktası, `[mcp]` optional extra; testler 35+53=88 yeşil
- 2026-10-12 · İskelet kuruldu (L1+L5+plans+kararlar+raporlar).
- 2026-10-14 · Gece vardiyası: 2 subagent (CLI insan-testi + drift/plugin) → QA raporu %100 kapandı: 5/5 P1 (EOF fail-closed, tek-satır hata, cp1252, preflight kapısı, google import guardu) + 6/6 işlevsel P2 (BOM toleransı, retry görünürlüğü, exit 3, boş-sonuç mesajı, ok karakterleri, arg help'leri); testler 35+42=77 yeşil; plugin iskeleti kuruldu (.claude-plugin + skills/chromex-sozlesme)

## Bekleyen onaylar
Yok. PyPI ertelendi; GitHub Release yayını bilinçli yapılmadı (depo `PUBLIC`).
