# FAZ 3 — SPRINTLER

> Kaynak sırası: `ANAYASA.md`, `AGENTS.md`, `DESIGN_MANIFESTO.md`.
> Faz 3 yalnızca bu dosyadan açılır; adaylar `plans/BACKLOG.md`'den seçilir.

## Kapsam

Faz 3, mevcut çekirdeğin üzerine yeni platformlar ekler. Her platform
dikey keskinlik ile yazılır: API/CLI worker + policygate onayı + offline test
+ MCP tool + canlı doğrulama. Web panel, Chrome eklentisi, masaüstü GUI ve
genel DOM kazıma çerçevesi kapsam dışıdır.

## Başlangıç durumu

| Ölçüt | Değer |
|---|---:|
| Offline test | 126 (policygate 41 + wba 75 + model 10) |
| MCP tool | 21 |
| Sürüm | v1.1.0 |
| Faz 2 geçiş kapısı | `scripts/gecis_kapisi.ps1` ile tamamlandı |
| Güncel toplam LOC | 9.356 |

## LOC bütçesi

| Sprint | Kod | Doküman | Yapılandırma/destek | Toplam |
|---|---:|---:|---:|---:|
| 5 — Faz 3 kayıt senkronu | 0 | 262 | 0 | 262 |
| 6 — YouTube salt-okunur | 230 | 80 | 30 | 340 |
| 7 — Notion + Trello salt-okunur/taslak | 360 | 100 | 40 | 500 |
| 8 — Telegram + Mastodon oku/taslak/gönder | 280 | 90 | 40 | 410 |
| 9 — Bluesky + Reddit salt-okunur | 320 | 90 | 40 | 450 |
| 10 — Secret ve kurulum sertleştirme | 260 | 70 | 30 | 360 |
| **Plan toplamı** | **1.450** | **692** | **180** | **2.322** |

Sprint 5 sonrası güncel kullanım **9.356 LOC**'dir. Kalan sprintler
uygulanırsa tahmini toplam **11.416 LOC** olur; tampon **584 LOC** kalır.
Kategori dağılımı:

| Tür | Tavan | Mevcut | Plan | Kalan |
|---|---:|---:|---:|---:|
| Toplam | 12.000 | 9.356 | 2.060 | 584 |
| Kod | 7.000 | 5.092 | 1.450 | 458 |
| Doküman | 4.500 | 3.984 | 430 | 86 |
| Yapılandırma/destek | 500 | 280 | 180 | 40 |

## Sprint kuralları

1. Sprint açılmadan önce LOC tahmini ve kabul testi bu dosyaya yazılır.
2. Her sprint tek konu ve tek çıktı kümesi ile kapanır.
3. Offline testler `exit 0` olmadan sprint kapanamaz.
4. Her sprintte en az bir canlı doğrulama komutu koşulur ve rapora yazılır.
5. SEND/MODIFY/DELETE canlı testi yalnızca insan onayıyla koşar.
6. Yeni worker doğrudan `policygate` onay ve audit katmanını kullanır.
7. Sprint kapanışında `STATE_BOARD.md`'e commit hash'li damga atılır.

## Sprint 5 — Faz 3 kayıt senkronu

**Hedef:** Faz 3'ü belgeli, tek kaynaklı ve ölçülebilir hâle getirmek.

**Çıktılar**
- `plans/FAZ3-SPRINTLER.md` bu dosya.
- `plans/BACKLOG.md` tek backlog kaynağı.
- `ANAYASA.md`, `AGENTS.md`, `README.md` ve `STATE_BOARD.md` senkronu.
- 9.000/12.000 LOC tavan çelişkisinin giderilmesi.

**Doğrulama**
```powershell
cd policy-gate; python -m unittest discover -s tests
cd ..\windows-browser-automation; python -m unittest discover -s tests
cd ..; powershell -NoProfile -ExecutionPolicy Bypass -File scripts\gecis_kapisi.ps1
git diff --check
```

**Kabul**
- Faz 3 planı ve backlog diskte kalıcıdır.
- LOC tablosu 12.000 tavanıyla eşleşir.
- 126 offline test, geçiş kapısı ve `git diff --check` `exit 0` verir.

## Sprint 6 — YouTube salt-okunur worker

**Hedef:** YouTube Data API ile arama, video detayı ve oynatma listesi okuma.

**İşler**
- `workers/youtube_worker.py`: API-first, üç salt-okunur komut.
- `youtube-arastir`, `youtube-detay`, `youtube-oynatma-listesi` CLI komutları.
- Aynı üç komut MCP tool olarak kaydedilir.
- Kota ve OAuth hataları tek satır, secret'sız kullanıcı mesajına döner.
- Offline testler: boş yanıt, hata, redaksiyon, audit, MCP şema.

**Canlı doğrulama**
```powershell
python -m orchestrator.cli youtube-arastir "chromex" --limit 5
python -m orchestrator.cli youtube-detay VIDEO_KIMLIGI
python -m orchestrator.cli audit-dogrula
```

**Kabul**
- Gerçek API'den en az bir arama sonucu SQLite'a yazılır.
- Sorgu/istek audit zincirine girer; API anahtarı çıktıda görünmez.
- `mcp_smoke.py` yeni tool sayısını listeler.
- Offline test sayacı CI, kök README ve wba README ile senkron olur.

## Sprint 7 — Notion + Trello salt-okunur/taslak

**Hedef:** Kişisel bilgi yönetimi panosunu güvenli biçimde okumak.

**İşler**
- Notion: sayfa arama, veritabanı sorgulama, sayfa oluşturma `DRAFT`.
- Trello: pano/kart/liste okuma ve kart taslağı oluşturma.
- Her dış etki `ActionRequest` + `preflight()` + `require()` akışından geçer.
- Offline testler: izin hatası, etik doğrulama, rate limit, audit.

**Canlı doğrulama**
```powershell
python -m orchestrator.cli notion-arastir "chromex"
python -m orchestrator.cli trello-panolar
python -m orchestrator.cli trello-taslak PANO_KIMLIGI "Faz 3 test kartı"
```

**Kabul**
- Notion ve Trello okuma sonuçları gerçek servis yanıtından gelir.
- Taslak oluşturma etkileşimli terminalde onay ister.
- Etkileşimsiz ortamda taslak/red testi `exit 3` döner.

## Sprint 8 — Telegram + Mastodon oku/taslak/gönder

**Hedef:** Mesaj platformlarında okuma, taslak ve onaylı gönderim.

**İşler**
- Telegram Bot API: mesaj okuma ve birebir `SEND` mesajı.
- Mastodon REST: timeline okuma, taslak kaydetme, `SEND` gönderi.
- SEND etkileşimsiz oturumda her zaman reddedilir.
- Offline testler: onay, red, karakter sınırı, hata, redaksiyon, audit.

**Canlı doğrulama**
```powershell
python -m orchestrator.cli telegram-mesajlar --limit 10
python -m orchestrator.cli mastodon-taslak "Faz 3 canlı doğrulama"
python -m orchestrator.cli mastodon-gonder TASLAK_KIMLIGI
```

**Kabul**
- Okuma komutları gerçek servis yanıtını döner.
- Taslak kaydı audit'e girer; gönderim açık insan onayı ister.
- İnsan onayı verilmezse hiçbir dış mesaj gitmez.

## Sprint 9 — Bluesky + Reddit salt-okunur

**Hedef:** Protokol ve OAuth çeşitliliğini güvenli okuma alanında genişletmek.

**İşler**
- Bluesky AT Protocol ile profil ve gönderi arama.
- Reddit OAuth ile subreddit ve gönderi okuma.
- Rate limit ve protokol hataları kullanıcıya tek satır mesajla iner.
- Offline testler: kimlik doğrulama, limit, boş sonuç, hata, audit.

**Canlı doğrulama**
```powershell
python -m orchestrator.cli bluesky-ara "chromex" --limit 10
python -m orchestrator.cli reddit-gonderiler "chromex" --limit 10
```

**Kabul**
- Her iki platformdan en az bir gerçek kayıt döner.
- Token çıktıda ve audit gövdesinde maskelenir.
- Yazma yetkisi istenmez; worker salt-okunur kalır.

## Sprint 10 — Secret ve kurulum sertleştirme

**Hedef:** Kurulum sürtünmesini azaltıp secret depolamayı dosyadan çıkarmak.

**İşler**
- Windows DPAPI veya eşdeğer yerel secret store köprüsü.
- `.env` yükleme ve doğrulama adımlarının tek kurulum komutuna bağlanması.
- Eski düz dosya token geçişi için açık taşım/kaldır komutu.
- Offline testler: secret yok, bozuk kasa, taşım, silme, redaksiyon.

**Canlı doğrulama**
```powershell
python -m orchestrator.cli secret-kur
python -m orchestrator.cli secret-dogrula
python -m orchestrator.cli github-arastir "chromex" --limit 1
```

**Kabul**
- Yeni token düz metin dosyaya yazılmaz.
- Kurulum kontrolü tek komutla `exit 0` döner.
- Mevcut GitHub canlı çağrısı secret kasası üzerinden çalışır.

## Faz 3 dışı

Aşağıdakiler yeni tavan kararı olmadan açılamaz:

- Web panel veya masaüstü GUI
- Chrome eklentisi
- Genel DOM yazma çerçevesi
- Instagram, Facebook Pages, Threads, TikTok
- Çok kullanıcılı hesap yönetimi
- PyPI yayını
