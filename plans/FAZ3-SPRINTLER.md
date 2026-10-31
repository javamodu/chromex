# FAZ 3 — SPRINTLER

> Kaynak sırası: `ANAYASA.md`, `AGENTS.md`, `DESIGN_MANIFESTO.md`.
> Faz 3 yalnızca bu dosyadan açılır; adaylar `plans/BACKLOG.md`'den seçilir.

## Kapsam

Faz 3, mevcut çekirdeğin üzerine **YouTube ve secret kasası** ekler. Her iş
dikey keskinlik ile yazılır: API/CLI worker + policygate onayı + offline test
+ MCP tool + canlı doğrulama. Telegram, Reddit, Notion, Trello, Mastodon ve
Bluesky Faz 4 adaylarına aktarılır. Web panel, Chrome eklentisi, masaüstü GUI
ve genel DOM kazıma çerçevesi kapsam dışıdır.

## Başlangıç durumu

| Ölçüt | Değer |
|---|---:|
| Offline test | 190 (policygate 41 + wba 139 + model 10) |
| MCP tool | 28 |
| Sürüm | v1.1.0 |
| Faz 2 geçiş kapısı | `scripts/gecis_kapisi.ps1` ile tamamlandı |
| Güncel toplam LOC | 10.806 |

## LOC bütçesi

| Sprint | Kod | Doküman | Yapılandırma/destek | Toplam |
|---|---:|---:|---:|---:|
| 5 — Faz 3 kayıt senkronu | 0 | 262 | 0 | 262 |
| 6 — YouTube salt-okunur | 230 | 80 | 30 | 340 |
| 7 — Secret ve kurulum sertleştirme (eski Sprint 9) | 260 | 70 | 30 | 360 |
| **Gerçekleşen artış** | **996** | **3** | **21** | **1.020** |

Backlog yöntem tablosu sonrası güncel kullanım **10.806 LOC**'dir. Kalan
tampon **1.194 LOC**'dur.
kalır.
Kategori dağılımı:

| Tür | Tavan | Mevcut | Plan | Kalan |
|---|---:|---:|---:|---:|
| Toplam | 12.000 | 10.806 | 1.397 | 1.194 |
| Kod | 7.000 | 6.608 | 1.504 | 392 |
| Doküman | 4.500 | 3.894 | -129 | 606 |
| Yapılandırma/destek | 500 | 304 | 22 | 196 |

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

**Durum:** Kod tamamlandı; canlı YouTube doğrulaması insan onayı bekliyor.

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

## Sprint 7 — Secret ve kurulum sertleştirme

**Durum:** Kod tamamlandı; canlı GitHub doğrulaması insan onayı bekliyor.

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

## Faz 4 adayları

Kullanıcı kararıyla Faz 3 kapsamından çıkarıldı; yeni tavan/kapsam kararı
beklenir:

- Notion + Trello salt-okunur/taslak
- Mastodon oku/taslak/gönder
- Bluesky salt-okunur
- Telegram oku/taslak/gönder
- Reddit salt-okunur

## Faz 3 dışı

Aşağıdakiler yeni tavan kararı olmadan açılamaz:

- Web panel veya masaüstü GUI
- Chrome eklentisi
- Genel DOM yazma çerçevesi
- Instagram, Facebook Pages, Threads, TikTok
- Çok kullanıcılı hesap yönetimi
- PyPI yayını
