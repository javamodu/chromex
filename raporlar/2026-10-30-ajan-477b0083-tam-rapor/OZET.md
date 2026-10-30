# Chromex Tam Rapor — 2026-10-30 (ajan 477b0083)

> Kaynaklar: `ANAYASA.md`, `AGENTS.md`, `DESIGN_MANIFESTO.md`, `GLOSSARY.md`,
> `README.md`, `STATE_BOARD.md`, `plans/FAZ2-SPRINTLER.md`, bileşen README'leri,
> `raporlar/2026-10-30-loc-tavani-artirimi/OZET.md`. Uydurma yok; her iddia
> ya bu dosyalardan ya da açık analizden çıkar.

## Anlık durum (kanıt kültürü gereği)

- Son commit: `65623dc` "Sprint 4 kanit raporu ve durum damgasi".
- Testler: 126 offline (policygate 41 + wba 75 + model yönetimi 10); CI 4/4 yeşil.
- Çalışma ağacında commit'lenmemiş LOC tavanı artışı (9.000→12.000) var;
  gerekçesi `raporlar/2026-10-30-loc-tavani-artirimi/OZET.md`'de belgeli
  (Faz 3 platform alanı; güvenlik kuralları değişmez).

## 1. Amaç — neden başladı

ANAYASA'nın kendi ifadesi: **"her şeyi yazmak değil; en kritik acıyı en az
kodla çözmek"**. Başlangıç (oluşturma 2026-08-06, iskelet 2026-10-12) üç somut
acının birleşimi:

1. **Ajan çağında kontrol kaybı** — kodlama ajanları AFK çalıştırılırken
   "ajan prompt injection ile neyi siler, kime gönderir?" sorusu cevapsızdı.
   Çözüm: onay kapısı + fail-closed + audit zinciri.
2. **Kanıtsız "yaptım" iddiaları** — yeşil test ≠ çalışan sistem (sözlükteki
   `Fake-green` terimi bunun için var). Kültür: "exit 0 + test yeşil +
   commit hash".
3. **SaaS dashboard kazımanın kırılganlığı** — API-first omurga; API'nin
   yetmediği yerde yalnızca salt-okunur CDP okuma.

## 2. Hedefler

| Hedef | Kanıt |
|---|---|
| Küçük, keskin, kanıtlı, güvenlik-önce çekirdek | LOC tavanı disiplini (12.000 yeni tavan, 8.688 mevcut) |
| Dış etkili her işlemde insan onayı | 5 seviye: READ/DRAFT/SEND/MODIFY/DELETE; DELETE asla `auto` |
| Kurcalamaya dayanıklı kanıt zinciri | SHA-256 hash zinciri, `audit-dogrula`, paketler arası parite testi |
| Faz 2 ürünleşme kanıtı | 4/4 sprint kapandı; canlı doğrulama her sprint'te zorunlu |
| Ajan döngüsünü durdurmadan sürdürme | ralph.sh + rate-limit toleransı + Paseo `glm-5.3` canlı çağrı |

## 3. Stack

- **Dil:** Python 3.11+ (policygate çekirdeği **stdlib-only, sıfır bağımlılık**;
  yeni bağımlılık yalnızca optional extra), bash (ralph.sh).
- **Veri:** SQLite (`data/results.db`); JSONL audit zinciri + `audit.lock`
  (Windows msvcrt / POSIX fcntl çapraz-platform kilit).
- **Tarayıcı:** Chrome ayrı profil + CDP `127.0.0.1:9222` (yalnız localhost);
  Playwright CLI; Chrome 136+ debug port kısıtına ayrı `user-data-dir` cevabı.
- **Protokol:** MCP — `chromex-mcp` 21 tool; `MCPApprovalChannel` fail-closed.
- **CLI'lar:** gh, supabase, vercel (dashboard otomasyonu yerine).
- **Model:** Paseo CLI; varsayılan `glm-5.3`, kayıt defteri `models.json`.
- **CI:** GitHub Actions; Windows cp1252 dersleri üretime yansımış.
- **İzolasyon:** Docker sandbox (node:22-bookworm), tek kullanımlık branch.

## 4. Kimin acısını çözer

| Kim | Acı | Çözüm |
|---|---|---|
| Ajanını AFK çalıştıran solo geliştirici | Ajan yıkıcı işlem yapar, iz bırakmaz | Onay kapısı + fail-closed + audit |
| Windows'ta yaşayan güçlü kullanıcı | Araçlar macOS/Linux varsayar | Windows-first, cp1252-güvenli çıktı, PowerShell setup |
| Araştırma otomasyonu kuran kişi | Dashboard kazıma kırılgan; hesap kısıtı | API-first; CDP yalnız API'nin yetmediği yerde, salt-okunur |
| Güvenlik kodunu kopyalayan geliştirici | Kopya çekirdek sürüklenir | policygate tek kaynak paket (wheel + editable) |
| Yeşil teste güvenen ekipler | Fake-green | Canlı doğrulama zorunlu sprint kuralı + `production_check.py` |

Hedef persona net: tek kullanıcı, Windows, Claude Code + Paseo kullanan,
kontrolü elden bırakmak istemeyen geliştirici. Çok-kullanıcılı senaryo
bilinçli olarak Faz 3 dışı.

## 5. Yetenekler (kanıtlı)

- **9 worker:** GitHub (ara/issue/PR), Gmail (ara/taslak/gönder), X bookmarks
  (resmi ücretli API), LinkedIn (profil/paylaş API; akış/arama CDP salt-okunur),
  Canva export (pdf/jpg/png/gif/pptx/mp4), Supabase (salt-okunur), Vercel
  (durum/log/iptal), dosya tabanlı zamanlayıcı (READ/DRAFT ile sınırlı), Blender.
- **Onay kapısı:** tam detay gösterimi, birebir `EVET`; etkileşimsiz oturumda
  SEND/DELETE otomatik RED.
- **Audit:** her karar + her HTTP isteği hash zincirinde; URL query tamamen
  maskeli; secret redaksiyonu `***`; zincir tek karakter değişikliğini yakalar.
- **Dayanıklılık:** 429/5xx'te üstel backoff + jitter + `Retry-After`;
  60 sn subprocess timeout; BOM toleransı; EOF fail-closed.
- **MCP:** 21 tool; tek sahip kuralı; gerçek istemciyle smoke testi.
- **Ajan döngüsü:** ralph.sh (Reçete C), native `/goal` (A), Task Master (B);
  `sor` komutu kayıt dışı modeli reddeder, hata çıktısı maskeli.
- **Sürüm:** policygate v1.1.0 wheel + taslak GitHub Release (yayınlama
  bilinçli olarak insan onayında; PyPI ertelendi).

## 6. Rakip karşılaştırması

| Boyut | **Chromex** | Playwright/Selenium (raw) | browser-use / Skyvern | Power Automate / UI.Vision | n8n / Zapier |
|---|---|---|---|---|---|
| Onay kapısı (5 seviye, fail-closed) | Var | Yok | Kısmen | Yok | İnsan onay adımı eklenebilir |
| Kurcalamaya dayanıklı audit zinciri | Var, SHA-256 | Yok | Yok | Zayıf | Zayıf |
| API-öncelikli | Var | Hayır (DOM odaklı) | Hayır (görsel/vizyon) | Hayır (UI-kazıma) | Konektör bazlı |
| MCP / ajan-öncelikli | 21 tool | Ayrı MCP paketleri | MCP'ye bağlanır | Yok | n8n MCP var |
| Deterministik + tekrarlanabilir | Var | Var | Hayır (LLM her koşuda değişir; token maliyeti) | Var | Var |
| Windows + açık Chrome oturumu (CDP) | Ayrı profil + 127.0.0.1 | Kısmen | Hayır | Var | Hayır |
| Ajan döngüsü + rate-limit dayanıklılığı | ralph + auto-retry | Yok | Yok | Yok | Yok |
| Kurulum çabası | Orta (setup + elle OAuth) | Düşük | Orta | Düşük | Düşük (bulut) |
| Bakım riski | Düşük (az kod, tavan) | Orta | Yüksek (UI/hesap değişimi) | Yüksek (seçici kırılması) | Orta (bulut fiyat) |
| Dağıtım/ekosistem | Zayıf (PyPI ertelendi, tek kullanıcı) | Devasa | Büyüyen | Kurumsal | Devasa |

**Konumlandırma:** rakiplerin hiçbiri "ajan çağı için lokal onay + audit
çekirdeği" satmıyor; hepsi ya otomasyonu (kütüphaneler) ya ajanı
(browser-use) yapıyor. Chromex'in gerçek nişi aradaki **güvenlik katmanı**;
policygate bağımsız paketlenmiş haliyle bu boş köşe taşı.

## 7. Metriklerle puanlama (kendi rubrikam)

| Metrik | Ağırlık | Puan | Gerekçe |
|---|---:|---:|---|
| Güvenlik & onay mimarisi | %20 | 9 | Fail-closed, DELETE asla auto, zincir, secret+URL maskesi. Eksik: onay kanalı pratikte yalnız terminal |
| Kanıt/test disiplini | %15 | 9 | 126 offline + CI 4/4 + canlı sprint doğrulaması + production_check. Mock ağırlıklı ama fake-green karşıtı kültür oturmuş |
| Kod ekonomisi | %10 | 8 | ~5.000 kod LOC'a 9 worker + MCP + çekirdek; registry desenli CLI. Tavan artışı Faz 3'e alan açar |
| Yetenek kapsamı | %15 | 7 | 9 worker + 21 MCP tool gerçek. Genel scraping, masaüstü genişletmesi, panel bilinçli yok |
| Kullanılabilirlik/kurulum | %10 | 6 | setup.ps1 var; ama OAuth credential + elle login + "tek sahip kuralı" elle adımlar; X ücretli, LinkedIn kısıtlı |
| Dokümantasyon & SSOT | %10 | 9 | 7 katlı hiyerarşi, sözlük, sprint damgaları; bu boyutta nadir |
| Taşınabilirlik/dağıtım | %10 | 4 | PyPI ertelendi, release manuel, Windows-first, Linux/macOS planı yok |
| Ölçeklenebilirlik | %5 | 5 | Çok-süreç audit kiliti var; tek kullanıcı, zamanlayıcı tek seferlik; tavan artışı henüz commit'lenmemiş |
| Farklılaşma | %5 | 8 | "Onay + audit çekirdeği" nişi gerçekten boş; parite testiyle iki paket tek zincire bağlı |
| **Ağırlıklı toplam** | %100 | **7,6 / 10** | |

## 8. Güçlü / eksik yönler

**Güçlü:**
- Ajan otomasyonuna lokal onay + kurcalamaya dayanıklı audit katmanı —
  pazarda boş kalan niş.
- Test ve kanıt kültürü: offline 126 test, canlı doğrulama zorunluluğu,
  fake-green'a karşı açık terminoloji.
- LOC disiplini: az kodla uçtan uca çalışan dikey keskinlik.
- SSOT hiyerarşisi: çelişkide ANAYASA kazanır; dersler kalıcı kayıta geçer.
- policygate'in bağımsız, stdlib-only, yeniden kullanılabilir paket olması.

**Eksik:**
- Dağıtım: PyPI ertelendi; GitHub Release yayını insan onayında bekliyor;
  depo `PUBLIC` ama kurulum yerel wheel üzerinden.
- Taşınabilirlik: Windows-first; Linux/macOS yol haritası yok.
- Kurulum sürtünmesi: OAuth credential indirme, hedef sitelere elle login,
  MCP "tek sahip kuralı" — ilk kurulum dakikalar değil saat ölçeğinde.
- Hacim sınırları: LinkedIn ToS riski, X API ücretli, Gmail sensitive scope.
- Tavan artışı belgeli ama commit'lenmemiş; süreç olarak açık uç.

## 9. Sonuç

Chromex, "ajan çağında güvenlik önce" tezini kodla ispatlayan bir çekirdek:
**kişisel üretim aracı olarak 7,6/10** — güvenlik ve disiplin boyutunda
pazardaki çoğu araçtan iyi; **ürün olarak 4-5/10** — dağıtım, çoklu platform
ve kurulum kolaylığı bilinçli olarak feda edilmiş. ANAYASA'nın "küçük ve
keskin" sözüne sadakat puanı artırıyor; büyüme kararı (12.000 tavan, Faz 3
platform matrisi) insan onayıyla ve belgeli verilmiş. Sıradaki en yüksek
getirili adım: tavan artışını commit'lemek ve dağıtım kararını (GitHub
Release yayını) netleştirmek — teknik borç değil, kararı bekleyen iki açık
uç.
