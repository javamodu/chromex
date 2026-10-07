# Windows & Tarayıcı Otomasyonu - Teknoloji Detayları

## 🎯 Ne Yapar?

Windows'ta oturum açılmış Chrome ortamında **API-öncelikli araştırma otomasyonu**. GitHub, Gmail, X, Canva, Supabase, Vercel gibi servisleri **onay kapısı + audit zinciri** katmanıyla güvenli şekilde otomatize eder.

**İlke:** API > DOM > UIA > OCR > Koordinat (en kırılgan son sırada)

---

## 🛠️ Kullanılan Teknolojiler

### Ana Stack

| Teknoloji | Versiyon | Amaç | Dosya |
|-----------|----------|------|-------|
| **Python** | 3.11+ | Worker runtime | core/, workers/ |
| **Playwright** | 1.40+ | Browser automation | CDP attach |
| **Chrome DevTools Protocol** | 136+ | Remote debugging | 127.0.0.1:9222 |
| **PowerShell** | 7.0+ | Windows scripting | scripts/*.ps1 |
| **SQLite** | 3.40+ | Audit + data store | data/results.db |
| **Node.js** | 20+ | MCP sunucular | MCP config |

### RPA (Robot Framework) - Önerilen Alternatif Yol

Orijinal plan-2'de **Robot Framework RPA kütüphaneleri** öneriliyordu (low-code yaklaşım):

| RPA Kütüphanesi | Amaç | Durum |
|-----------------|------|-------|
| **RPA.Desktop** | Masaüstü UI otomasyonu (pywinauto) | Önerildi, kullanılmadı |
| **RPA.Windows** | Windows UIA element yakala | Önerildi, kullanılmadı |
| **RPA.HTTP** | HTTP requests (low-code) | Önerildi → httpx seçildi |
| **RPA.Email.ImapSmtp** | Email send/receive | Önerildi → Gmail API seçildi |

**Neden Kullanılmadı?**
- Robot Framework: Low-code → developer için aşırı soyutlama
- Python native: Daha iyi tip güvenliği, debugging, IDE desteği
- API-first strateji: RPA Desktop/Windows gerekmedi (API öncelik)
- Gerçek kullanım: httpx (RPA.HTTP yerine), Gmail API (RPA.Email yerine), pywinauto (doğrudan, RPA.Windows yerine)

### Python Bağımlılıklar

```python
# HTTP & Retry
httpx>=0.27.0        # Modern HTTP client
tenacity>=8.2.3      # Retry/backoff logic

# Güvenlik
python-dotenv>=1.0.0 # Environment variables

# Testing
pytest>=8.0.0
pytest-html>=4.1.0
```

### Servis API'ları

| Servis | API | Auth Method | Worker |
|--------|-----|-------------|--------|
| **GitHub** | REST API v3 + GraphQL | gh CLI / PAT | github_worker.py |
| **Gmail** | Gmail API v1 | OAuth2 | gmail_worker.py |
| **X (Twitter)** | API v2 | OAuth 1.0a / Bearer | x_worker.py |
| **Canva** | Connect API | Partner key | canva_worker.py |
| **Supabase** | PostgREST | Service role key | supabase_worker.py |
| **Vercel** | REST API | Token | vercel_worker.py |

---

## 📁 Dosya Rehberi (Orijinal Yapı)

### Plan 2 Dizin Yapısı (1,450+ satır)

```
windows-browser-automation/
├── docs/
│   └── plan-2-desktop-browser-automation.md (93 satır)
├── config/
│   ├── mcp.claude-desktop.json
│   └── policy.json
├── core/                           (449 satır toplam)
│   ├── __init__.py
│   ├── approval.py                 (56 satır - ActionRequest, require())
│   ├── audit.py                    (84 satır - SHA-256 hash zinciri)
│   ├── http.py                     (89 satır - retry + backoff)
│   ├── policy.py                   (70 satır - policy.json yönetimi)
│   ├── secrets.py                  (planlı - Vault entegrasyonu)
│   └── store.py                    (150 satır - SQLite CRUD)
├── orchestrator/                   (100 satır, planlı)
│   ├── __init__.py
│   └── cli.py                      (Rich UI, komutlar)
├── workers/                        (673 satır toplam)
│   ├── __init__.py
│   ├── canva_worker.py             (planlı - export_design)
│   ├── github_worker.py            (120 satır - search, issues, create_pr)
│   ├── gmail_worker.py             (planlı - send_message, list_messages)
│   ├── supabase_worker.py          (planlı - query_table, insert_row)
│   ├── vercel_worker.py            (planlı - deployments)
│   └── x_bookmarks_worker.py       (553 satır - X bookmarks API)
├── scripts/                        (PowerShell + Playwright)
│   ├── playwright-flows/
│   │   └── canva_export.js
│   ├── start-chrome-debug.ps1
│   └── setup-gmail-oauth.ps1
├── tests/                          (planlı, hedef 1200+ satır)
│   ├── test_approval.py
│   ├── test_audit.py
│   ├── test_http.py
│   ├── test_policy.py
│   ├── integration/
│   │   ├── test_github_worker.py
│   │   └── test_gmail_worker.py
│   └── e2e/
├── data/
│   ├── results.db                  (SQLite)
│   └── audit.jsonl                 (SHA-256 log)
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
└── setup.py
```

### Dosya Kategorileri

**Ana Dökümantasyon (7 dosya):**
- README.md
- docs/plan-2-desktop-browser-automation.md (ORIJINAL plan, RPA önerileri)
- .env.example
- requirements.txt
- setup.py
- config/policy.json
- config/mcp.claude-desktop.json

**Kod Modülleri (15+ dosya):**
- core/ (6 modül: approval, audit, http, policy, secrets, store)
- workers/ (6 worker: github, gmail, x, canva, supabase, vercel)
- orchestrator/ (1 modül: cli)
- tests/ (8+ test dosyası planlı)

**PowerShell Scriptleri (3 dosya):**
- scripts/start-chrome-debug.ps1 (Chrome remote debugging başlat)
- scripts/setup-gmail-oauth.ps1 (OAuth2 flow)
- scripts/playwright-flows/canva_export.js (Playwright workflow)

**Veri Dosyaları:**
- data/results.db (SQLite - araştırma sonuçları)
- data/audit.jsonl (SHA-256 hash zinciri)

---

## 📁 Mimari (505 satır, orijinal)

### Core Modüller (299 satır)

**core/approval.py** (56 satır)
```python
Katman: Security gate
Görev: Her işlem için onay al
Sınıflar:
  - ActionRequest: Onay isteği modeli
  - require(): Blocking onay fonksiyonu
Politikalar:
  - READ: Genelde auto-approve
  - DRAFT: Otomatik izin verilebilir
  - SEND: Mutlaka ask
  - MODIFY: Mutlaka ask
  - DELETE: Mutlaka ask
```

**core/audit.py** (84 satır)
```python
Katman: Compliance & logging
Görev: SHA-256 hash zinciri
Özellikler:
  - log_event(): Zaman damgalı kayıt
  - Secret masking (API keys, tokens)
  - Tamper-proof chain
  - JSON format (Plan 1 uyumlu)
Format:
  {
    "timestamp": "2026-08-07T...",
    "event_type": "SEND_EMAIL",
    "details": {...},
    "hash": "sha256(...)",
    "prev_hash": "sha256(...)"
  }
```

**core/http.py** (89 satır, ORIGINAL)
```python
Katman: Network resilience
Görev: Retry + exponential backoff
Özellikler:
  - max_retries parametresi (varsayılan 3)
  - 429 (rate-limit) handling
  - 5xx (server error) retry
  - Network timeout recovery
  - Jitter: (2^attempt) + random(0, 1)
  - Başarısız istek audit'e yazılır
```

**core/policy.py** (70 satır)
```python
Katman: Configuration
Görev: Politika yönetimi
Dosya: config/policy.json
Yapı:
  {
    "READ": "auto",
    "DRAFT": "auto",
    "SEND": "ask",
    "MODIFY": "ask",
    "DELETE": "deny"
  }
```

---

### Worker Modülleri (206 satır, ORIGINAL)

**workers/github_worker.py** (120 satır)
```python
Servis: GitHub
API: gh CLI / REST API v3
Fonksiyonlar:
  - search_repos(query, limit) → List[Repo]
  - repo_issues(owner, name, state) → List[Issue]
  - create_pr(owner, repo, head, base, title, body) → PR
    * Approval gate: SEND policy
    * Validation: title max 70 char
    * Audit: PR URL + response kaydedilir
Özellik:
  - gh CLI öncelikli (hızlı)
  - Fallback: REST API + PAT
  - Error handling: 404, 403, 422
```

**workers/gmail_worker.py** (planlı)
```python
Servis: Gmail
API: Gmail API v1
Fonksiyonlar:
  - list_messages(query, max_results) → Messages
  - send_message(to, subject, body, html) → Message
    * Approval gate: SEND policy
    * HTML sanitization
    * Attachment desteği (base64)
Özellik:
  - OAuth2 flow (credentials.json)
  - Token refresh otomatik
  - Draft save desteği
```

**workers/x_worker.py** (planlı)
```python
Servis: X (Twitter)
API: API v2
Fonksiyonlar:
  - search_tweets(query, max_results) → Tweets
  - post_tweet(text, media_ids) → Tweet
    * Approval gate: SEND policy
    * 280 karakter sınırı
    * Media upload desteği
Özellik:
  - OAuth 1.0a signing
  - Rate-limit header parse
  - Retry-After respect
```

**workers/canva_worker.py** (planlı)
```python
Servis: Canva
API: Connect API
Fonksiyonlar:
  - search_designs(query) → Designs
  - export_design(design_id, format) → URL
    * Formats: PNG, JPG, PDF, MP4
    * Approval gate: READ policy
Özellik:
  - Partner key auth
  - Webhook support (export complete)
  - Asset library access
```

**workers/supabase_worker.py** (planlı)
```python
Servis: Supabase
API: PostgREST
Fonksiyonlar:
  - query_table(table, filters, limit) → Rows
  - insert_row(table, data) → Row
    * Approval gate: MODIFY policy
    * RLS policy check
Özellik:
  - Service role key (bypass RLS)
  - Real-time subscriptions
  - Storage API entegrasyonu
```

**workers/vercel_worker.py** (planlı)
```python
Servis: Vercel
API: REST API
Fonksiyonlar:
  - list_deployments(project) → Deployments
  - trigger_deployment(project, branch) → Deployment
    * Approval gate: MODIFY policy
    * Build logs streaming
Özellik:
  - Token auth
  - Team scope desteği
  - Environment variables set
```

---

### Orchestrator & CLI (planlı, ~100 satır)

**orchestrator/cli.py**
```python
Görev: Kullanıcı arayüzü
Komutlar:
  - run <worker> <action> <args>  # Worker çalıştır
  - approve <request_id>           # Bekleyen onay
  - deny <request_id>              # Onayı reddet
  - audit [--verify]               # Audit log göster
  - policy [--edit]                # Politika yönetimi
Özellikler:
  - Rich UI (renkli çıktı)
  - Progress bar (playwright işlemler)
  - Interactive prompts (onaylar)
```

---

## 🔐 Güvenlik Mimarisi

### 3 Katmanlı Güvenlik

**Katman 1: Politika Sistemi**
```python
# config/policy.json
{
  "READ": "auto",     # Okuma: otomatik
  "DRAFT": "auto",    # Taslak: otomatik
  "SEND": "ask",      # Gönderim: sor
  "MODIFY": "ask",    # Değişiklik: sor
  "DELETE": "deny"    # Silme: yasak
}
```

**Katman 2: Approval Gates**
```python
# Her kritik işlemde
request = ActionRequest(
    action="SEND_EMAIL",
    details={"to": "user@example.com", "subject": "..."}
)
require(request)  # Blocking call - kullanıcı onayı beklenir
```

**Katman 3: Audit Trail**
- SHA-256 hash zinciri
- Tamper-proof log (hash değişirse algılanır)
- Secret masking (API key'ler logda görünmez)
- Zaman damgası (ISO 8601 UTC)

### Karşılaştırma: Plan 1 vs Plan 2

| Güvenlik | Plan 1 (Claude Code) | Plan 2 (Windows/Browser) |
|----------|----------------------|--------------------------|
| Model | Soft (prompt-based) | Hard (code gates) |
| Containment | Docker sandbox | Windows process izolasyonu |
| Approval | `--dangerously-skip-permissions` | `require()` blocking call |
| Audit | audit_bridge.py (opsiyonel) | core/audit.py (zorunlu) |
| Policy | PROMPT.md kuralları | policy.json + kod |
| Secrets | .env dosyası | .env + masking |

---

## 🌐 MCP (Model Context Protocol) Entegrasyonu

### MCP Sunucular

**Mevcut:**
- `@modelcontextprotocol/server-filesystem` - Dosya sistemi erişimi
- `@modelcontextprotocol/server-github` - GitHub MCP
- `@modelcontextprotocol/server-google-drive` - Drive entegrasyonu

**Planlı:**
- `@modelcontextprotocol/server-gmail` - Gmail MCP
- Custom: supabase-mcp-server (PostgREST wrapper)
- Custom: vercel-mcp-server (API wrapper)

### MCP Kullanımı

```python
# Worker'dan MCP çağırma (planlı)
from mcp_client import MCPClient

client = MCPClient("github")
repos = client.call("search_repositories", {"query": "claude"})
```

**Avantajlar:**
- Standardize protokol
- Tip güvenliği (TypeScript definitions)
- Claude AI ile doğrudan entegrasyon
- Yeniden kullanılabilir toollar

---

## 🧪 Test Stratejisi

### Test Piramidi (planlı)

**Unit Tests** (pytest)
```bash
tests/
├── test_approval.py      # Approval logic
├── test_audit.py         # Hash chain
├── test_http.py          # Retry logic
└── test_policy.py        # Policy evaluation
```

**Integration Tests**
```bash
tests/integration/
├── test_github_worker.py    # Gerçek API (sandbox)
├── test_gmail_worker.py     # OAuth mock
└── test_playwright.py       # Browser attach
```

**E2E Tests** (manuel + smoke)
```bash
# Gerçek Chrome + gerçek servislere bağlan
pytest tests/e2e/ --html=report.html
```

### Test Coverage Hedefleri

| Modül | Target | Durum |
|-------|--------|-------|
| core/approval.py | 95% | Planlı |
| core/audit.py | 95% | Planlı |
| core/http.py | 90% | Planlı |
| core/policy.py | 95% | Planlı |
| workers/* | 80% | Planlı |

---

## 🔧 Kurulum & Çalıştırma

### Gereksinimler

**Windows:**
- Windows 10/11
- PowerShell 7.0+
- Python 3.11+
- Chrome 136+ (remote debugging aktif)

**Python Environment:**
```bash
cd windows-browser-automation
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Chrome Remote Debugging:**
```powershell
# PowerShell
Start-Process chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenium\chrome"
```

**Konfigürasyon:**
```bash
# .env dosyası
GITHUB_TOKEN=ghp_...
GMAIL_CREDENTIALS=path/to/credentials.json
X_API_KEY=...
CANVA_API_KEY=...
SUPABASE_URL=https://....supabase.co
SUPABASE_KEY=...
VERCEL_TOKEN=...
```

### İlk Çalıştırma (planlı)

```bash
# Politika ayarla
python orchestrator/cli.py policy --init

# GitHub worker test
python orchestrator/cli.py run github search_repos "claude" --limit 5

# Onay bekleyen işlemler
python orchestrator/cli.py approve list

# Audit doğrula
python orchestrator/cli.py audit --verify
```

---

## 🎯 Kullanım Senaryoları

### Senaryo 1: Araştırma Otomasyonu
```python
# 1. GitHub'da repo ara
repos = github_worker.search_repos("ai agents", limit=20)

# 2. Her repo için issue'ları çek
for repo in repos:
    issues = github_worker.repo_issues(repo.owner, repo.name, "open")
    
# 3. Sonuçları Supabase'e kaydet (Approval: MODIFY)
supabase_worker.insert_rows("research_repos", repos)

# 4. Özet email gönder (Approval: SEND)
gmail_worker.send_message(
    to="team@company.com",
    subject="Haftalık AI Agents Araştırması",
    body=generate_summary(repos)
)
```

### Senaryo 2: İçerik Yayınlama
```python
# 1. Canva'dan tasarım export et
image_url = canva_worker.export_design("design_123", format="PNG")

# 2. X'te paylaş (Approval: SEND)
tweet = x_worker.post_tweet(
    text="Yeni blog yazımız yayında!",
    media_ids=[upload_media(image_url)]
)

# 3. Vercel'de deployment trigger (Approval: MODIFY)
deploy = vercel_worker.trigger_deployment("blog-project", branch="main")

# 4. Audit kayıtlarını kontrol et
audit.verify_chain()
```

### Senaryo 3: Veri Toplama
```python
# 1. Gmail'den belirli etiketli mailleri al
emails = gmail_worker.list_messages(query="label:invoices", max_results=100)

# 2. PDF eklerini parse et
invoices = [parse_invoice(email.attachments) for email in emails]

# 3. Supabase'e kaydet
supabase_worker.insert_rows("invoices", invoices)

# 4. Dashboard'u güncelle (Vercel redeploy)
vercel_worker.trigger_deployment("dashboard")
```

---

## 📊 Performans & Limitler

### API Rate Limits

| Servis | Limit | Worker Stratejisi |
|--------|-------|-------------------|
| GitHub | 5000/saat (auth) | Retry-After header |
| Gmail | 250 quota units/gün | Batch requests |
| X | 50 tweet/gün (free) | Queue + schedule |
| Canva | 100 export/saat | Export queue |
| Supabase | Unlimited (self-hosted) | Connection pool |
| Vercel | 100 deploy/gün | Deploy throttle |

### Performans Metrikleri (tahmini)

| İşlem | Süre | Açıklama |
|-------|------|----------|
| GitHub repo search | 200-500ms | API call |
| Gmail send | 1-2s | OAuth + send |
| X post tweet | 500ms-1s | API v2 |
| Canva export | 5-30s | Render time |
| Playwright attach | 100-200ms | CDP connect |
| Approval gate | 0-∞ | Kullanıcı bekler |

### Optimizasyon Stratejileri

1. **Paralel İşlem**
   - asyncio kullanımı (planlı)
   - Concurrent API calls
   - Batch operations

2. **Cache**
   - API responses (Redis planlı)
   - Playwright snapshots
   - Token/credentials cache

3. **Queue**
   - Background tasks (Celery planlı)
   - Scheduled jobs (cron)
   - Retry queue (failed operations)

---

## 🚨 Bilinen Sınırlamalar

### Teknik Sınırlar

1. **Windows Bağımlılığı**
   - PowerShell scriptleri Windows'a özel
   - Chrome remote debugging path Windows'a özel
   - Çözüm: macOS/Linux portları planlı

2. **Chrome Remote Debugging**
   - Tek bir Chrome instance (9222 portu)
   - User data dir kilidi
   - Çözüm: Multi-profile desteği planlı

3. **Playwright CDP Limitasyonu**
   - Service worker debugging zor
   - iframe içinde shadow DOM sınırlı
   - Çözüm: API-first strateji zaten mevcut

### Güvenlik Sınırları

1. **Secret Management**
   - .env dosyası plaintext
   - Rotating credentials manuel
   - Çözüm: Vault/Keychain entegrasyonu planlı

2. **Approval Fatigue**
   - Çok onay → kullanıcı "auto" yapar
   - Risk: Güvenlik düşer
   - Çözüm: Akıllı politika önerileri planlı

3. **Audit Log Boyutu**
   - Hash zinciri sonsuza büyür
   - Rotation yok
   - Çözüm: Log rotation planlı (30 gün)

---

## 🔗 İlgili Repolar & Kaynaklar

### Kullanılan Kütüphaneler

| Repo | Amaç | URL | Alternatifler |
|------|------|-----|---------------|
| **Playwright** | Browser automation | github.com/microsoft/playwright-python | Selenium (daha yavaş), Puppeteer (Node.js) |
| **httpx** | HTTP client | github.com/encode/httpx | requests (sync only), aiohttp (complex) |
| **tenacity** | Retry logic | github.com/jd/tenacity | RPA.HTTP (low-code), backoff kütüphanesi |
| **python-dotenv** | Environment vars | github.com/theskumar/python-dotenv | configparser, pydantic-settings |
| **pytest** | Testing | github.com/pytest-dev/pytest | unittest (stdlib), nose2 |

### Kütüphane Seçim Kıyaslaması

#### httpx vs requests vs RPA.HTTP
| Özellik | httpx (seçildi) | requests | RPA.HTTP (önerilen alternatif) |
|---------|-----------------|----------|--------------------------------|
| Async desteği | ✅ Native | ❌ Yok | ❌ Sync only |
| HTTP/2 | ✅ Var | ❌ Yok | ❌ Yok |
| Timeout | ✅ Granular | ⚠️ Global | ✅ Kolay config |
| Retry | tenacity ile | Adaptör gerekli | ✅ Built-in |
| Tip desteği | ✅ Tam | ⚠️ Kısmi | ❌ Low-code |
| Learning curve | Orta | Düşük | Düşük (Robot Framework) |

#### Playwright vs Selenium vs RPA.Desktop
| Özellik | Playwright (seçildi) | Selenium | RPA.Desktop (önerilen alternatif) |
|---------|----------------------|----------|-----------------------------------|
| CDP attach | ✅ Native | ⚠️ Hack | ❌ Yok (pywinauto) |
| Performance | ✅ Hızlı | ⚠️ Yavaş | ⚠️ Orta |
| Browser support | Chrome, Firefox, Safari | Tüm tarayıcılar | ❌ Yalnızca Windows |
| Element selector | ✅ Auto-wait | ❌ Manuel wait | ❌ UIA selector |
| API-first uyumu | ✅ Kolay fallback | ⚠️ Ağır | ❌ Desktop-only |
| Low-code | ❌ Python | ❌ Python | ✅ Robot Framework |

#### pytest vs unittest vs Robot Framework
| Özellik | pytest (seçildi) | unittest | Robot Framework (önerilen alternatif) |
|---------|------------------|----------|---------------------------------------|
| Syntax | ✅ Basit (assert) | ⚠️ Verbose | ✅ Keyword-driven |
| Fixtures | ✅ Güçlü | ⚠️ setUp/tearDown | ✅ Test setup/teardown |
| Parametrize | ✅ Native | ❌ Yok | ✅ Template |
| Plugin ekosistemi | ✅ Zengin | ⚠️ Dar | ✅ Zengin |
| HTML report | pytest-html | ❌ Yok | ✅ Built-in |
| Developer workflow | ✅ Mükemmel | ✅ İyi | ⚠️ Low-code (QA odaklı) |


### API Dökümantasyonu

| Servis | Docs | SDK/CLI |
|--------|------|---------|
| GitHub | docs.github.com/rest | gh CLI |
| Gmail | developers.google.com/gmail/api | google-api-python-client |
| X (Twitter) | developer.x.com/docs | tweepy |
| Canva | developers.canva.com | REST API only |
| Supabase | supabase.com/docs/reference/python | supabase-py |
| Vercel | vercel.com/docs/rest-api | REST API only |

### MCP Protokolü

| Kaynak | URL |
|--------|-----|
| MCP Spec | modelcontextprotocol.io |
| GitHub MCP Server | github.com/modelcontextprotocol/servers/tree/main/src/github |
| Filesystem MCP | github.com/modelcontextprotocol/servers/tree/main/src/filesystem |
| Custom MCP Guide | modelcontextprotocol.io/docs/writing-servers |

### Referans Projeler

| Proje | Ne Yaptı | İlham Aldığımız |
|-------|----------|-----------------|
| Browser Use | LLM → Playwright | API-first fallback stratejisi |
| Skyvern | Computer vision RPA | OCR son çare yaklaşımı |
| Zapier | Workflow automation | Approval gate pattern |
| n8n | Node-based automation | Worker modül yapısı |

---

## 🎯 Ne Zaman Kullanılır?

### ✅ İyi Uyan Durumlar

- ✅ Tekrarlı araştırma (GitHub, Gmail tarama)
- ✅ Multi-servis workflows (GitHub → Gmail → X)
- ✅ İnsan onayı gerektiren işlemler (email gönder, tweet at)
- ✅ Audit trail gerekli işler (compliance)
- ✅ API'si olan servisler (GitHub, Gmail, X)
- ✅ Windows ortamı (Chrome remote debugging)

### ❌ Kötü Uyan Durumlar

- ❌ Gerçek zamanlı işlemler (approval latency)
- ❌ API'siz/sadece UI olan siteler (kırılgan)
- ❌ Tam otonom işler (her adımda onay → yavaş)
- ❌ Production'da kritik işlemler (test aşamasında)
- ❌ macOS/Linux (Windows bağımlı, port gerekli)

---

## 🛣️ Yol Haritası

### Tamamlanan (Original)
- ✅ core/approval.py (56 satır)
- ✅ core/audit.py (84 satır)
- ✅ core/http.py (89 satır - retry logic)
- ✅ workers/github_worker.py (120 satır - search, issues, create_pr)

### Devam Eden
- 🚧 Test suite (pytest)
- 🚧 orchestrator/cli.py
- 🚧 MCP client wrapper

### Planlı (Öncelik Sırasıyla)

**P0 - Kritik**
1. workers/gmail_worker.py (email send/receive)
2. Policy file existence check
3. Input validation (PR title max 70 char)
4. Audit log rotation (30 gün)

**P1 - Yüksek**
5. workers/x_worker.py (tweet, search)
6. asyncio paralel işlem
7. Error handling (I/O errors, network)
8. Documentation (API reference)

**P2 - Orta**
9. workers/canva_worker.py (export)
10. workers/supabase_worker.py (CRUD)
11. workers/vercel_worker.py (deploy)
12. Rich UI (progress bars)

**P3 - Düşük**
13. Vault/Keychain entegrasyonu
14. macOS/Linux port
15. Dashboard (web UI)
16. Akıllı politika önerileri

---

## 📈 Karşılaştırma: Plan 1 vs Plan 2

### Kullanım Alanı

| Özellik | Plan 1 (Claude Code) | Plan 2 (Windows/Browser) |
|---------|----------------------|--------------------------|
| **Amaç** | Kod üretimi otomasyonu | Araştırma otomasyonu |
| **Hedef Kullanıcı** | Developer (solo) | Analyst/Researcher (team) |
| **İnsan Rolü** | Planlayıcı | Onaylayıcı |
| **Otomasyon** | %95 (YOLO mode) | %60 (approval gates) |

### Teknik Stack

| Bileşen | Plan 1 | Plan 2 |
|---------|--------|--------|
| **Dil** | Bash + Python (stdlib) | Python + PowerShell |
| **Runtime** | OS-level loop | Python process |
| **Browser** | Yok | Chrome CDP + Playwright |
| **API Calls** | gh CLI (minimal) | 6+ servis (GitHub, Gmail, X, Canva, Supabase, Vercel) |
| **Dependencies** | Sıfır (stdlib) | httpx, tenacity, playwright |
| **Context** | Taze (her iterasyon) | Persistent (session) |

### Güvenlik Modeli

| Güvenlik | Plan 1 | Plan 2 |
|----------|--------|--------|
| **Approval** | Prompt-based (soft) | Code gates (hard) |
| **Containment** | Docker sandbox | Windows process |
| **Audit** | Opsiyonel | Zorunlu |
| **Policy** | PROMPT.md | policy.json + require() |
| **Risk** | Kod hatası (revert edilebilir) | Veri gönderimi (geri alınamaz) |

### Performans

| Metrik | Plan 1 | Plan 2 |
|--------|--------|--------|
| **Setup Time** | 5 dk | 15 dk |
| **First Run** | 30s (Claude boot) | 2s (Python import) |
| **Iteration** | 20-60s (LLM call) | 200ms-30s (API/browser) |
| **Throughput** | 1-3 görev/dk | 10-50 istek/dk |
| **Cost** | Abonelik/API kullanımı | API rate limits |

### Bakım

| Bakım | Plan 1 | Plan 2 |
|-------|--------|--------|
| **Kod Satırı** | 291 (core) | 505 (core + workers) |
| **Test Coverage** | Yok | Hedef %85 |
| **Documentation** | README + inline | README + API docs |
| **Breaking Changes** | Claude CLI updates | API versiyonları |
| **Update Frequency** | Düşük (stable) | Orta (API changes) |

---

## 💡 Best Practices

### 1. API-First Yaklaşım
```python
# ✅ İyi
result = github_worker.create_pr(...)  # API

# ❌ Kötü
playwright.click("#new-pr-button")  # Kırılgan
```

### 2. Granular Approvals
```python
# ✅ İyi - Her kritik işlem ayrı onay
require(ActionRequest("SEND_EMAIL", {...}))
require(ActionRequest("CREATE_PR", {...}))

# ❌ Kötü - Batch onay
require(ActionRequest("DO_EVERYTHING", {...}))
```

### 3. Secret Masking
```python
# ✅ İyi
audit.log_event("API_CALL", {"token": "[REDACTED]"})

# ❌ Kötü
audit.log_event("API_CALL", {"token": actual_token})
```

### 4. Retry Stratejisi
```python
# ✅ İyi - Exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=60)
)
def call_api(): ...

# ❌ Kötü - Linear retry
for i in range(3):
    try: call_api()
    except: time.sleep(5)
```

### 5. Policy Hierarchy
```json
// ✅ İyi - En kısıtlayıcı
{
  "READ": "auto",
  "DRAFT": "auto",
  "SEND": "ask",
  "MODIFY": "ask",
  "DELETE": "deny"
}

// ❌ Tehlikeli
{
  "SEND": "auto",
  "DELETE": "auto"
}
```

---

## 📝 Örnek Workflow: GitHub PR Araştırması

```python
#!/usr/bin/env python3
"""
Örnek: Belirli bir topic'te açık PR'ları araştır,
issue'larını topla, özet rapor oluştur ve email gönder.
"""

from workers.github_worker import GitHubWorker
from workers.gmail_worker import GmailWorker
from workers.supabase_worker import SupabaseWorker
from core.audit import Audit

def main():
    github = GitHubWorker()
    gmail = GmailWorker()
    supabase = SupabaseWorker()
    audit = Audit()
    
    # 1. GitHub'da repo ara (Approval: READ - auto)
    repos = github.search_repos("topic:ai-agents", limit=10)
    audit.log_event("SEARCH_REPOS", {"count": len(repos)})
    
    # 2. Her repo için açık PR'ları çek
    all_prs = []
    for repo in repos:
        prs = github.list_prs(repo.owner, repo.name, state="open")
        all_prs.extend(prs)
    
    # 3. Supabase'e kaydet (Approval: MODIFY - ask)
    supabase.insert_rows("research_prs", all_prs)
    audit.log_event("SAVE_RESEARCH", {"pr_count": len(all_prs)})
    
    # 4. Özet email gönder (Approval: SEND - ask)
    summary = generate_summary(all_prs)
    gmail.send_message(
        to="team@company.com",
        subject=f"AI Agents Araştırması - {len(all_prs)} PR",
        body=summary,
        html=True
    )
    audit.log_event("SEND_SUMMARY", {"recipients": 1})
    
    # 5. Audit zincirini doğrula
    if audit.verify_chain():
        print("✅ Audit verification passed")
    else:
        print("❌ Audit chain compromised!")

if __name__ == "__main__":
    main()
```

---

**Son Güncelleme:** 2026-08-07  
**Versiyon:** 1.0 (Orijinal + Planlı)  
**Konum:** D:\Vibecode\chromex\windows-browser-automation\  
**Durum:** 🚧 Aktif Geliştirme (core modüller tamamlandı, worker'lar planlı)

