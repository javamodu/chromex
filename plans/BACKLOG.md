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
| F3-001 | 5 | Faz 3 plan, backlog ve LOC senkronu | 262 | Doğrulandı; commit bekliyor | 126 test + geçiş kapısı + `git diff --check` |
| F3-002 | 6 | YouTube salt-okunur worker | 340 | Planlandı | Gerçek arama sonucu + audit + MCP tool |
| F3-003 | 7 | Notion + Trello oku/taslak | 500 | Planlandı | Gerçek okuma + onaylı taslak + offline red testi |
| F3-004 | 8 | Telegram + Mastodon oku/taslak/gönder | 410 | Planlandı | Okuma + taslak + insan onaylı SEND |
| F3-005 | 9 | Bluesky + Reddit salt-okunur | 450 | Planlandı | Gerçek sonuç + token maskesi + audit |
| F3-006 | 10 | Secret kasası ve kurulum sertleştirme | 360 | Planlandı | Düz dosya yazmama + canlı GitHub çağrısı |

**Planlı toplam:** 2.322 LOC.  
**Tavan sonrası tampon:** 584 LOC.

## Aday / ertelenmiş işler

Bu kayıtlar planlı değildir; yeni tavan veya kapsam kararı gerekir.

| ID | İş | Tahmini LOC | Zorluk | Engel |
|---|---|---:|---|---|
| A-001 | Google Drive + Calendar | 400–600 | Orta | OAuth scope yönetimi |
| A-002 | Discord bot | 300–450 | Orta | Sunucu ve bot izinleri |
| A-003 | Slack workspace | 320–470 | Orta | Workspace admin onayı |
| A-004 | WordPress REST | 220–350 | Düşük | Uygulama parolası/kimlik doğrulama |
| A-005 | Instagram Graph API | 400–550 | Yüksek | Business hesap zorunluluğu |
| A-006 | Facebook Pages | 420–570 | Yüksek | App review |
| A-007 | Threads API | 350–500 | Yüksek | Erişim onayı |
| A-008 | TikTok Content API | 450–650 | Yüksek | Platform onayı ve içerik kuralları |
| A-009 | Remote MCP transport | 250–400 | Yüksek | Ağ, kimlik doğrulama ve TLS tasarımı |
| A-010 | Çok hesap yönetimi | 350–550 | Yüksek | İzolasyon, onay ve audit modeli |

## Teknik borç

| ID | Konu | Neden açık | Önerilen çözüm |
|---|---|---|---|
| T-001 | Düz dosya secret | OAuth/Gmail geçici köprüsü hâlâ dosyaya yazıyor | Sprint 10 secret kasası |
| T-002 | Dağıtım kararı | PyPI ertelendi, Release yayını yapılmadı | Aynı karar korunur; değişirse karar kaydı açılır |
| T-003 | Platform taşınabilirliği | Windows-first kurulum ve CDP akışı var | Yeni tavan kararıyla platform matrisi yazılır |
| T-004 | Tarayıcı yazma | CDP yalnızca LinkedIn okuma için kullanılıyor | Genel DOM yazma bilinçli anti-hedef |

## Bilinçli anti-hedefler

- Web panel, masaüstü GUI veya Chrome eklentisi yazmak.
- Kırılgan genel DOM otomasyonu.
- Onay kapısını atlayan “kolay mod”.
- Çok kullanıcılı SaaS kalıbı.
- Tavan aşımıyla entegrasyon sayısını büyütmek.
