# BACKLOG — Chromex

> Tek backlog kaynağıdır. Faz 3 içi işler `plans/FAZ3-SPRINTLER.md`'de
> sprintlenir; buradaki her kayıt tek satırla izlenir. “Yakında” kartı yoktur.

## Mevcut yetenek sınırları

| Alan | Yapabilir | Yapamaz |
|---|---|---|
| Güvenlik | READ/DRAFT/SEND/MODIFY/DELETE onay kapısı, audit zinciri, secret redaksiyonu | Secret'ları işletim sistemi kasasında saklama; çok kullanıcılı izin yönetimi |
| Arayüz | Terminal CLI, stdio MCP sunucusu, zamanlayıcı | Web panel, masaüstü GUI, Chrome eklentisi, REST/WebSocket daemon |
| Servisler | GitHub, Gmail, X, LinkedIn, Canva, Supabase, Vercel, Paseo/GLM | YouTube, Notion, Trello, Telegram, Mastodon, Bluesky, Reddit ve sonraki adaylar |
| Tarayıcı | Chrome CDP ile LinkedIn salt-okunur akışı | Tarayıcı üzerinden form doldurma, gönderme veya genel DOM yazma |
| Dağıtım | Yerel wheel, `v1.1.0` etiketi, GitHub Release hazırlığı | PyPI yayını, macOS/Linux kurulum doğrulaması |

## Faz 3 planlı işler

| ID | Sprint | İş | Tahmini LOC | Durum | Kabul kanıtı |
|---|---|---|---:|---|---|
| F3-001 | 5 | Faz 3 plan, backlog ve LOC senkronu | 262 | Tamamlandı (`80c7a0e`) | 126 test + geçiş kapısı + `git diff --check` |
| F3-002 | 6 | YouTube salt-okunur worker | 340 | Kod tamam, canlı doğrulama bekliyor | 120 offline test + 27 MCP tool + canlı arama bekliyor |
| F3-003 | 7 | Secret kasası ve kurulum sertleştirme | 360 | Kod tamam, canlı doğrulama bekliyor | DPAPI kasası + düz dosya taşımı + canlı GitHub bekliyor |
| F3-004 | 7 | Site bazlı güvenlik ve keşif | 350 | Kod tamam, canlı doğrulama bekliyor | 139 offline test + 28 MCP tool + pilot planı |
| F4-004 | — | Telegram oku/taslak/gönder | 230 | Faz 4 adayı | Okuma + taslak + insan onaylı SEND |
| F4-005 | — | Reddit salt-okunur | 230 | Faz 4 adayı | Gerçek sonuç + token maskesi + audit |
| F4-001 | — | Notion + Trello oku/taslak | 500 | Faz 4 adayı | Gerçek okuma + onaylı taslak + offline red testi |
| F4-002 | — | Mastodon oku/taslak/gönder | 180 | Faz 4 adayı | Okuma + taslak + insan onaylı SEND |
| F4-003 | — | Bluesky salt-okunur | 220 | Faz 4 adayı | Gerçek sonuç + token maskesi + audit |

**Faz 3 planlı toplam:** 962 LOC.
**Tavan sonrası tampon:** 1.905 LOC.

## Yetenek ekleme yöntemleri

> Aşağıdaki tablo planlama tahminleridir; kabul kanıtı sprint içinde
> offline test, canlı test ve LOC ölçümüyle kesinleşir.

| ID | Yöntem | Eklediği yetenek | LOC etkisi | Artı | Eksi | Durum |
|---|---|---|---:|---|---|---|
| Y-001 | Native API worker | YouTube; Faz 4: Telegram, Reddit, Notion, Trello, Mastodon, Bluesky | +120–300 / platform | Onay, audit, offline test ve MCP tam uyumlu | Credential, kota, API politikası | Faz 3 planlı |
| Y-002 | Resmî remote MCP adaptörü | Platformları daha az kodla çağırma | +80–180 / platform | Daha az worker kodu | Dış bağımlılık, sürüm riski, policy kontrolü zayıflar | Küçük ek olabilir |
| Y-003 | Harici local MCP köprüsü | `npx` / `uvx` ile hazır entegrasyon | +20–80 / platform | En hızlı ve en az LOC | Supply-chain riski; policygate dışına çıkabilir | Tampona sığar |
| Y-004 | CDP/Playwright salt-okunur DOM | API olmayan sitelerden veri okuma | +200–500 / akış | API gerektirmez | Kırılgan seçiciler, ToS riski | Plan dışı |
| Y-005 | Playwright tam tarayıcı yazma | Form doldurma, giriş, gönderi | +300–600 / akış | Otomasyon gücü yüksek | ToS, hesap riski, onay zorluğu | Anti-hedef |
| Y-006 | Chrome eklentisi | Oturumlu tarayıcıda kalıcı kontrol | +600–1.200 | CDP gerektirmez, kullanıcı oturumuna yakın | Onay/audit köprüsü zor, güvenlik yüzeyi büyür | Tavan aşar |
| Y-007 | Windows UI Automation | Windows uygulamalarını kontrol etme | +400–1.200 / uygulama | Gerçek masaüstü kontrolü | Windows-only, kırılgan, erişilebilirlik bağımlılığı | Tavan aşar |
| Y-008 | OS secret kasası | Token’ları `.env` yerine DPAPI/Keychain’te tutma | +260–360, -50 düz dosya köprüsü | Güvenlik ve kurulum kalitesi artar | Platforma özel kod, taşıma gerekir | Faz 3 Sprint 7 |
| Y-009 | Yerel GUI | Masaüstü arayüz | +800–2.000 | İnsan kontrolü kolaylaşır | CLI ile çift yüzey, bakım maliyeti | Tavan aşar |
| Y-010 | Web panel | Tarayıcıdan yönetim | +1.500–3.500 | Uzaktan ve görsel yönetim | Sunucu, auth, saldırı yüzeyi | Tavan aşar |
| Y-011 | Remote MCP/REST daemon | Ağ üzerinden servis etme | +400–900 | Çok istemci, uzak erişim | TLS, token, port, eşzamanlılık, audit riski | Tamponu aşar |
| Y-012 | Sürekli zamanlayıcı daemon | Tekrarlı işler | +300–700 | Otomatik çalışma | Süreç yönetimi, retry, secret ömrü | Plan dışı |
| Y-013 | Çok hesap yönetimi | Aynı serviste birden fazla profil | +500–1.200 | Kapsam genişler | İzolasyon, hesap başına policy/audit karmaşası | Ertelenmiş |
| Y-014 | Çok platform taşıma | macOS/Linux desteği | +300–800 | Kullanıcı tabanı genişler | Yol, PowerShell ve CDP farkları | Teknik borç |
| Y-015 | Mobil uygulama | iOS/Android kontrolü | +1.200–3.000 | Mobil otomasyon | Yeni stack, güvenlik modeli değişir | Anti-hedef |
| Y-016 | Plugin mimarisi | Worker’ları dinamik ekleme | +400–800, -100–300 tekrar azaltma | Uzatılabilirlik artar | Yükleyici, şema ve güvenlik denetimi | Tavan aşar |
| Y-017 | Audit HMAC/dış snapshot | Zincir silme/yeniden yazma kanıtı | +200–500 | Kurcalama kanıtı güçlenir | Anahtar yönetimi, dış depolama | Güvenlik adayı |
| Y-018 | Paketleme/dağıtım | PyPI, winget, scoop, installer | +150–400 | Kurulum kolaylaşır | Release, destek ve imza yükü | Karar bekliyor |

## Aday / ertelenmiş işler

Bu kayıtlar planlı değildir; yeni tavan veya kapsam kararı gerekir.

| ID | İş | Tahmini LOC | Zorluk | Engel |
|---|---|---:|---|---|
| A-001 | Google Drive + Calendar | 400–600 | Orta | OAuth scope yönetimi |
| A-003 | Slack workspace | 320–470 | Orta | Workspace admin onayı |
| A-005 | Instagram Graph API | 400–550 | Yüksek | Business hesap zorunluluğu |
| A-006 | Facebook Pages | 420–570 | Yüksek | App review |
| A-007 | Threads API | 350–500 | Yüksek | Erişim onayı |
| A-008 | TikTok Content API | 450–650 | Yüksek | Platform onayı ve içerik kuralları |
| A-009 | Remote MCP transport | 250–400 | Yüksek | Ağ, kimlik doğrulama ve TLS tasarımı |
| A-010 | Çok hesap yönetimi | 350–550 | Yüksek | İzolasyon, onay ve audit modeli |
| A-011 | Notion + Trello oku/taslak | 500 | Orta | Faz 4 adayı; kullanıcı kararı |
| A-012 | Mastodon oku/taslak/gönder | 180 | Orta | Faz 4 adayı; kullanıcı kararı |
| A-013 | Bluesky salt-okunur | 220 | Orta | Faz 4 adayı; kullanıcı kararı |

## Reddedilen adaylar

| ID | İş | Tahmini LOC | Red gerekçesi |
|---|---|---:|---|
| R-001 | Discord bot | 300–450 | Kullanıcı kararı: gerek yok |
| R-002 | WordPress REST | 220–350 | Kullanıcı kararı: gerek yok |

## Teknik borç

| ID | Konu | Neden açık | Önerilen çözüm |
|---|---|---|---|
| T-001 | Düz dosya secret | OAuth/Gmail geçici köprüsü hâlâ dosyaya yazıyor | Kasa kurulumu tamam; OAuth köprüsü ayrı iş |
| T-002 | Dağıtım kararı | PyPI ertelendi, Release yayını yapılmadı | Aynı karar korunur; değişirse karar kaydı açılır |
| T-003 | Platform taşınabilirliği | Windows-first kurulum ve CDP akışı var | Yeni tavan kararıyla platform matrisi yazılır |
| T-004 | Tarayıcı yazma | CDP yalnızca LinkedIn okuma için kullanılıyor | Genel DOM yazma bilinçli anti-hedef |

## Bilinçli anti-hedefler

- Web panel, masaüstü GUI veya Chrome eklentisi yazmak.
- Kırılgan genel DOM otomasyonu.
- Onay kapısını atlayan “kolay mod”.
- Çok kullanıcılı SaaS kalıbı.
- Tavan aşımıyla entegrasyon sayısını büyütmek.
