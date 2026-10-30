# LOC Tavanı Artırımı ve Platform Matrisi — 2026-10-30

## Özet

LOC tavanı **9.000’den 12.000’e** çıkarıldı. Amaç, Faz 3 platform
entegrasyonlarına yer açmak; kapsam ve güvenlik ilkeleri değişmedi.

## Yeni Tavan

| Tür | Eski tavan | Yeni tavan | Artış |
|---|---:|---:|---:|
| Toplam | 9.000 | 12.000 | +3.000 |
| Kod | 5.000 | 7.000 | +2.000 |
| Doküman | 3.500 | 4.500 | +1.000 |
| Destek | 300 | 500 | +200 |

## Mevcut Kullanım

| Tür | Mevcut | Yeni tavan | Kalan |
|---|---:|---:|---:|
| Toplam | 8.688 | 12.000 | 3.312 |
| Kod | 4.991 | 7.000 | 2.009 |
| Doküman | 3.408 | 4.500 | 1.092 |
| Destek | 289 | 500 | 211 |

## Hazır Platformlar

| Platform | Arayüz | Ücretsiz? | LOC | Zorluk | Engel / risk |
|---|---|---|---:|---|---|
| GitHub | gh CLI + REST + MCP | Evet | 124 | Düşük | Rate limit |
| Gmail | Google API + MCP | Kişisel | 139 | Orta | OAuth, sensitive scope |
| LinkedIn | API + CDP | Evet | 295 | Orta/Yüksek | API sınırlı, CDP riski |
| Canva | Connect API | Doğrulanmalı | 93 | Orta | Plan/API erişimi |
| Supabase | API + read-only MCP | Free tier | 67 | Düşük | service_role dikkat |
| Vercel | API + remote MCP | Hobby | 75 | Düşük | İzinler |
| X/Twitter | Resmî API | Hayır | 71 | Düşük | Ücretli API |
| Paseo/GLM | Paseo CLI | Evet | 154 | Orta | CLI kimlik doğrulama |

## Faz 3 Adayları

| Platform | Arayüz | Ücretsiz? | Tahmini LOC | Zorluk | Engel |
|---|---|---|---:|---|---|
| YouTube | Data API | Kota içinde | 180–260 | Orta | OAuth, kota |
| Google Drive/Calendar | Google API | Kişisel | 180–260 | Orta | OAuth scope |
| Notion | REST | Kişisel | 160–220 | Orta | İzinler |
| Trello | REST | Free tier | 140–200 | Düşük | Token |
| Mastodon | REST | Evet | 100–150 | Düşük | Instance politikası |
| Bluesky | AT Protocol | Evet | 140–200 | Orta | Protokol |
| Telegram | Bot API | Evet | 120–180 | Düşük | Bot yetkileri |
| Discord | Bot API | Evet | 180–240 | Orta | Sunucu izinleri |
| Slack | Web API | Free workspace | 180–240 | Orta | Admin onayı |
| WordPress | REST | Evet | 120–180 | Düşük | Kimlik doğrulama |
| Reddit | OAuth | Koşullu | 140–200 | Orta | API politikası |
| Instagram | Graph API | Business | 220–300 | Yüksek | Kişisel hesap yok |
| Facebook Pages | Graph API | Pages | 220–300 | Yüksek | App review |
| Threads | API | Koşullu | 180–240 | Yüksek | Erişim |
| TikTok | Content API | Koşullu | 240–320 | Yüksek | Onay, kurallar |

## Karar

- Tavan artışı yalnızca yeni platform alanı içindir.
- Güvenlik, onay kapısı, audit ve offline test kuralları değişmez.
- Aşım olursa iş bölünür veya iptal edilir.
