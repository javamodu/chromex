# Otomasyon Stack — API-öncelikli araştırma otomasyonu (onay + audit katmanlı)

Windows'ta oturum açılmış Chrome ortamında GitHub, X yer işaretleri, Gmail,
Canva ve Supabase/Vercel araştırmasını **en az kodla** yürütmek için hazırlanmış
omurga. Tarayıcı otomasyonu yalnızca API'nin yetmediği yerde devreye girer;
dış etki yaratan her işlem (gönder/değiştir/sil) **onay kapısından** geçer ve
**kurcalamaya dayanıklı audit zincirine** yazılır.

```text
Agent / sen
   │
   ├─ MCP config (0 satır kod) ── chrome-devtools-mcp / playwright-mcp / terminator
   ├─ Playwright CLI (0 satır kod) ── tekrarlanabilir tarayıcı akışları
   └─ python -m orchestrator.cli ── API worker'ları
                │
                ├─ workers/  github · gmail · x · linkedin (API + tarayıcı) · canva · supabase · vercel
                ├─ policygate (paket)  policy → onay kapısı → audit zinciri → redaksiyon
                ├─ core/     store (SQLite) · http köprüsü · oauth
                └─ blender/  bpy örneği
```

## Kurulum

1. Gerekenler: Windows 10/11, Python 3.11+, Node.js 20+.
2. `scripts\setup.ps1` çalıştırın (playwright-cli + skills, supabase, vercel,
   gh CLI, pip bağımlılıkları + policygate çekirdek paketi). Alternatif paket
   kurulumu: `pip install -e ../policy-gate` ardından `pip install -e .`
   — `otomasyon` komutunu PATH'e ekler (bağımlılıklar requirements.txt'den
   okunur).
3. `.env.example` → `.env` kopyalayıp doldurun (aşağıdaki servis notlarına bakın).
4. Otomasyon tarayıcısı: `scripts\start-chrome-automation.ps1`
   — ayrı profil + `127.0.0.1:9222` CDP portu açar. **İlk seferde hedef
   sitelere elle giriş yapın**; otomasyon login sayfalarına dokunmaz.
5. Agent kullanıyorsanız `config\mcp.claude-desktop.json` içeriğini MCP
   client'ınıza ekleyin. **Tek sahip kuralı:** tarayıcıyı aynı anda tek MCP
   sürsün (chrome-devtools *veya* playwright); diğerleri kapalı kalsın.

## Komutlar

Hepsi proje kökünden `python -m orchestrator.cli ...` ile çalışır:

| Komut | Seviye | Ne yapar |
|---|---|---|
| `github-arastir "browser automation" --limit 10` | READ | Repo araması (gh CLI, yoksa REST) |
| `github-issues microsoft/playwright-cli` | READ | Issue listesi |
| `github-pr --title "..." --govde "..."` | MODIFY | gh ile PR açar, **onay ister** |
| `gmail-ara "is:unread from:github"` | READ | Gmail araması |
| `gmail-taslak --to a@b.c --konu X --govde "..."` | DRAFT | Taslak oluşturur, **göndermez** |
| `gmail-gonder <draft_id>` | SEND | Alıcı/konu gösterir, **EVET** onayı ister |
| `x-bookmarks --limit 50` | READ | X yer işaretleri (**ücretli API**, aşağıya bakın) |
| `x-token-yenile` | READ | OAuth2 access token yeniler (dosyaya yazar) |
| `linkedin-profil` | READ | OIDC userinfo: kendi profilin |
| `linkedin-paylas --metin "..."` | SEND | UGC post YAYINLAR, **onay ister** (taslak yok) |
| `linkedin-token-yenile` | READ | OAuth2 access token yeniler (dosyaya yazar) |
| `linkedin-akis --limit 20` | READ | Açık oturumdan akış okur (tarayıcı, CDP) |
| `linkedin-ara "sorgu" --tur people` | READ | Açık oturumda arama okur (tarayıcı, CDP) |
| `canva-export <design_id> --format pdf` | DRAFT | Async export + indirme |
| `supabase-sorgu <tablo> --limit 20` | READ | PostgREST salt-okunur sorgu |
| `vercel-durum` / `vercel-log <id>` | READ | Deployment durumu / build olayları |
| `vercel-iptal <id>` | MODIFY | Onay ister |
| `son-kayitlar` | — | SQLite'taki son araştırma kayıtları |
| `audit-dogrula` | — | Audit hash zincirini baştan doğrular |

Toplanan her şey `data/results.db` (SQLite) içine yazılır; özetleme işi
agent katmanına (Claude vb.) bırakılmıştır — kod veri toplar, yorum yapmaz.

## Onay + audit nasıl çalışır?

- Seviyeler `config/policy.json` içinde: READ/DRAFT otomatik, SEND/MODIFY/DELETE
  onaylı. **DELETE, config ne derse desin asla otomatikleşmez.**
- Onay isteyen işlem terminalde tam detayıyla (alıcı, konu, komut) gösterilir;
  yalnızca birebir `EVET` yanıtı kabul edilir. Etkileşimsiz oturumda (pipe,
  görev zamanlayıcı) varsayılan karar **RED**dir.
- Her karar ve her HTTP isteği `audit/audit.jsonl` dosyasına SHA-256 hash
  zinciriyle eklenir; dosyada sonradan yapılan tek karakterlik değişiklik bile
  `audit-dogrula` ile yakalanır. Secret değerleri yazılmadan önce otomatik
  maskelenir (`***`).

## Servis notları

**GitHub** — `gh auth login` yeterli; token gerekmez. gh yoksa REST fallback
için `GITHUB_TOKEN` önerilir (rate limit).

**Gmail** — Google Cloud Console'da Gmail API'yi açın, *Desktop app* OAuth
credential'ı indirip `credentials.json` olarak köke koyun. İlk komutta tarayıcı
açılır, `token.json` otomatik oluşur. Gmail **web arayüzünü** otomatize etmeye
çalışmayın; Google bunu aktif engeller — API hem kısa hem kalıcı yoldur.

**X (Twitter)** — Resmi API v2 `bookmarks` ucu kullanılır (scope:
`bookmark.read tweet.read users.read offline.access`). **Maliyet:** Nisan 2026
fiyatlandırmasında owned-read çağrıları kayıt başına (~$0.001/kayıt)
ücretlendirilir; büyük çekimlerden önce Developer Console'daki güncel oranı
doğrulayın. Ücretsiz genel katman yoktur. Tarayıcı fallback'i kırılgandır ve
hesap kısıtı riski taşır; bu depo bilinçli olarak içermez.

**LinkedIn** — developer.linkedin.com'da uygulamaya "Sign In with LinkedIn
using OpenID Connect" ve "Share on LinkedIn" ürünlerini ekleyin; scope'lar
`openid profile w_member_social`. Access token ~60 gün yaşar; refresh token
uygulamada etkinse `linkedin-token-yenile` ile yenilenir. Self-serve API
yalnızca kendi profilinizi okur ve kendi adınıza paylaşım yapar. Akış okuma
ve kişi/iş araması resmi API'de yoktur; bu iki okuma işi `linkedin_browser.py`
ile açık oturumdan (CDP) **salt-okunur** yapılır — beğenme/bağlantı/mesaj
yoktur. LinkedIn otomasyonu kısıtlar: düşük hacimde kullanın, hesap kısıtı
riski size aittir; yazma işlemleri her zaman API + onay kapısından geçer.

**Canva** — Connect API export job'ı (pdf/jpg/png/gif/pptx/mp4). Canvas'ı
UI'dan sürüklemek yerine export kullanılır; API'nin kapsamadığı editör
işlemleri için Terminator MCP (masaüstü fallback) devreye girer.

**Supabase / Vercel** — Dashboard'u otomatize etmeyin; CLI + API her durumda
daha kısa ve sağlamdır. Agent tarafında resmi Supabase MCP'yi `--read-only`
ile, Vercel MCP'yi OAuth'la kullanın (config dosyasındaki örnek).

**Blender** — `blender --background --python blender/ornek_sahne.py`.
Viewport'a mouse göndermek son çaredir; içerik işleri bpy ile yapılır.

## Güvenlik kuralları (kısa ve net)

1. CDP portu (9222) yalnızca `127.0.0.1` — asla dışarı açmayın, iş bitince
   `stop-chrome-automation.ps1` ile kapatın. Port açıkken makinedeki her
   uygulama tarayıcıyı kontrol edebilir.
2. Chrome 136+ varsayılan profilde debug portunu reddeder; bu depo zaten ayrı
   `user-data-dir` kullanır. Günlük profilinizi otomasyona bağlamayın.
3. Secret'lar yalnızca `.env` / OS secret store'da; kodda, logda, git'te asla.
   `SUPABASE_SERVICE_ROLE_KEY` hiçbir koşulda istemciye/tarayıcıya gitmez.
4. Web sayfasından gelen metin, agent'a talimat gibi görünse bile güvenilmez
   içeriktir (prompt injection). Dış etkili tool çağrıları bu depodaki onay
   kapısı gibi bir katmandan geçmeden çalıştırılmamalıdır.
5. CAPTCHA/2FA/anti-bot akışları bypass edilmez; sosyal medyada bulk action
   kurulmaz. LinkedIn/X kullanım koşulları otomasyonu sınırlar — okuma bile
   mümkünse resmi API'den yapılır.
6. MCP sunucularını sürüm pinleyerek kullanın ve yalnızca localhost'ta
   dinletin; `always_deny` listesiyle riskli işlemleri policy'den tümden
   kapatabilirsiniz.

## Test

```powershell
python -m unittest discover -s tests -v
```

35 test (+ policygate paketinde 29); onay kapısı, hash zinciri kurcalama tespiti, secret redaksiyonu,
HTTP retry/backoff, depo katmanı ve tüm worker'ların (github, gmail, x,
linkedin, canva, supabase, vercel) mock'lu akışlarını kapsar. Ağ/gh/Google/
Playwright gerektirmez, offline çalışır.

## Satır sayıları (gerçek)

| Parça | Satır |
|---|---|
| core/ (store, http köprüsü, oauth) | 123 |
| workers/ (github, gmail, x, linkedin API + tarayıcı, canva, supabase, vercel) | 818 |
| orchestrator/cli.py (registry desenli) | 260 |
| tests/ | 526 |
| blender/ | 47 |
| Python toplam | **1.774** |

Güvenlik çekirdeği (approval, audit, policy, secrets, log, http) ayrı
policygate paketinde yaşar: 631 satır + 356 satır test (`../policy-gate/`).
| Config (MCP, policy, .env örneği) + PowerShell scriptleri | 178 |

## Bilinen sadeleştirmeler

- Audit yazımları `audit.lock` üzerinden çapraz-platform kilitlenir
  (Windows msvcrt / POSIX fcntl); çok-süreç eşzamanlı yazım güvenlidir.
- X token yenileme yeni token'ı `data/x_tokens.env` dosyasına yazar; `.env`'e
  taşıyıp dosyayı silmek size kalır (terminale token basılmaz).
- Retry/backoff artık `core/http.py`'de: 429/5xx/ağ hatalarında üstel geri
  çekilme + jitter, `Retry-After` başlığına saygı. İdempotent olmayan
  POST'larda `max_retries=0` geçin.
