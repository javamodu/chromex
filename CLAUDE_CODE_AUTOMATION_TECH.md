# Claude Code Otomasyonu - Teknoloji Detayları

## 🎯 Ne Yapar?

Claude Code/Codex'i **otonom, sıralı, durmadan** çalıştırarak planları tamamlar. OS-level orkestrasyon ile kod ajanını döngüde çalıştırır.

---

## 📁 Dosya Rehberi (Orijinal Yapı)

### Plan 1 Dizin Yapısı (837 satır)

```
claude-code-automation/
├── docs/
│   ├── otonom-ajan-orkestrasyon-plani.md (400+ satır)
│   └── plan-1-claude-code-os-level.md    (150+ satır)
├── audit_bridge.py                        (108 satır)
├── claude-resume.sh                       (17 satır)
├── ralph.sh                               (89 satır)
├── recete-b-taskmaster.sh                 (41 satır)
├── run-sandbox.sh                         (36 satır)
├── DECISIONS.md                           (şablon)
├── PLAN.md                                (19 satır şablon)
├── PROMPT.md                              (şablon)
├── README.md
└── .gitignore
```

### Dosya Kategorileri

**Ana Dökümantasyon (6 dosya):**
- README.md (genel bakış, 3 reçete, setup)
- docs/otonom-ajan-orkestrasyon-plani.md (detaylı mimari, repo kıyaslamaları)
- docs/plan-1-claude-code-os-level.md (orijinal plan, CVE-2025-54795 analizi)
- PLAN.md (checkbox şablonu)
- PROMPT.md (Claude'a talimatlar)
- DECISIONS.md (karar logu)

**Core Scriptler (5 dosya, 291 satır):**
- ralph.sh (89 satır - ana loop)
- audit_bridge.py (108 satır - SHA-256 audit)
- claude-resume.sh (17 satır - retry wrapper)
- run-sandbox.sh (36 satır - Docker izolasyon)
- recete-b-taskmaster.sh (41 satır - Task Master entegrasyon)

**Config:**
- .gitignore

### Satır Dağılımı

| Kategori | Satır | Dosya Sayısı |
|----------|-------|--------------|
| Dökümantasyon | 546 | 6 |
| Kod (Bash + Python) | 291 | 5 |
| **TOPLAM** | **837** | **11** |

---

## 🛠️ Kullanılan Teknolojiler

### Ana Araçlar

| Teknoloji | Versiyon | Amaç | Repo |
|-----------|----------|------|------|
| **Claude Code CLI** | v2.1.139+ | Kod ajanı | `@anthropic-ai/claude-code` |
| **Bash** | 5.0+ | Loop orchestration | Native |
| **Python** | 3.11+ | Audit bridge | Stdlib only |
| **Docker** | 20.10+ | Sandbox izolasyonu | docker.com |
| **Git** | 2.40+ | Version control | git-scm.com |

### Destek Araçları

| Araç | Amaç | Repo | Kıyaslama |
|------|------|------|-----------|
| **claude-auto-retry** | Rate-limit toleransı | cheapestinference/claude-auto-retry | tmux-based, sıfır bağımlılık, "5 saat doldu" parse eder |
| **Task Master** | Görev ağacı yönetimi | eyaltoledano/claude-task-master | PRD→görev ağacı, MCP entegrasyon, bağımlılık sistemi |
| **Vibe Kanban** | Görsel görev takibi | BloopAI/vibe-kanban | Çok-ajan kanban, To Do→In Progress→Done otomasyonu |
| **ralph** (referans) | OS-level loop örnekleri | dial481/ralph | CVE-2025-54795 sonrası dış loop referansı |
| **ralph-loop-skills** | Skills implementasyonu | tradesdontlie/ralph-loop-skills | Skill pattern örnekleri |

### Repo Kıyaslamaları

#### claude-auto-retry vs Manuel Bekleme
| Özellik | claude-auto-retry | Manuel sleep |
|---------|-------------------|--------------|
| Reset saati parse | ✅ Otomatik | ❌ Manuel hesap |
| 529/overload | ✅ Yakalar | ❌ Görmez |
| tmux entegrasyon | ✅ Built-in | ❌ Yok |
| Bağımlılık | Sıfır | Sıfır |
| False-positive | ✅ Akıllı retry | ❌ Körü körüne |

#### Task Master vs Vibe Kanban
| Özellik | Task Master | Vibe Kanban |
|---------|-------------|-------------|
| Görsel UI | ❌ CLI | ✅ Kanban board |
| Bağımlılık ağacı | ✅ DAG | ❌ Manuel sıra |
| PRD→görev dönüşümü | ✅ Otomatik | ❌ Manuel |
| Çok-ajan | ❌ Tek | ✅ 10+ ajan |
| MCP desteği | ✅ Var | ❌ Yok |
| Şirket durumu | ✅ Aktif | ⚠️ Community (bloop kapandı) |

#### Ralph Referans Implementasyonları
| Repo | Satır | Özellik | Kullanım |
|------|-------|---------|----------|
| dial481/ralph | ~200 | Temel loop | Referans |
| tradesdontlie/ralph-loop-skills | ~400 | Skills pattern | İlham |
| Bu proje (ralph.sh) | 89 | Minimalist, audit | Üretim |

---

## 📁 Dosya Yapısı ve Roller

### Core Scripts (291 satır)

**ralph.sh** (89 satır)
```bash
Katman: OS-level orchestration
Görev: PLAN.md'deki görevleri sırayla işler
Özellikler:
  - Rate-limit algılama (log parsing)
  - Otomatik bekleme (WAIT_ON_LIMIT=900s)
  - Her iterasyon commit
  - MAX_ITERATIONS limiti
  - Audit bridge entegrasyonu
```

**audit_bridge.py** (108 satır)
```python
Katman: Audit & logging
Görev: SHA-256 hash zincirli audit kaydı
Özellikler:
  - Stdlib-only (sıfır dependency)
  - Plan 2 uyumlu format
  - Komutlar: log, verify
  - Tamper detection
```

**claude-resume.sh** (17 satır)
```bash
Katman: Resilience
Görev: Basit retry wrapper
Özellikler:
  - Çökme durumunda yeniden başlat
  - Tek komut için wrapper
```

**run-sandbox.sh** (36 satır)
```bash
Katman: Security
Görev: Docker izolasyonu
Özellikler:
  - node:22-bookworm container
  - Volume mount
  - API key injection
  - Abonelik girişi desteği
```

**recete-b-taskmaster.sh** (41 satır)
```bash
Katman: Task orchestration
Görev: Task Master entegrasyonu
Özellikler:
  - PRD → görev ağacı
  - Bağımlılık yönetimi
  - Sıralı yürütme
```

---

## 🔧 3 Reçete (Kullanım Şekilleri)

### Reçete A - Minimal (Native /goal)
```bash
npm i -g claude-auto-retry
claude-auto-retry install
git checkout -b otonom-run
claude --dangerously-skip-permissions

# İçeride:
/goal PLAN.md'deki tüm maddeler tamam, testler geçiyor
```

**Kullanılan:**
- Native `/goal` komutu
- `--dangerously-skip-permissions` (YOLO mode)
- claude-auto-retry

**Avantaj:** Sıfır kod
**Dezavantaj:** Taze context yok

### Reçete B - Yapılandırılmış (Task Master)
```bash
bash recete-b-taskmaster.sh

# PRD'yi .taskmaster/docs/prd.txt'e koy
task-master next  # Sıradaki görevi al
```

**Kullanılan:**
- Task Master MCP
- Görev ağacı yönetimi
- Bağımlılık sistemi

**Avantaj:** Disiplinli görev takibi
**Dezavantaj:** Setup overhead

### Reçete C - Ralph Loop (Önerilen)
```bash
# Docker sandbox
bash run-sandbox.sh /path/to/project

# Ralph'ı başlat
MAX=50 bash ralph.sh
```

**Kullanılan:**
- ralph.sh (OS-level loop)
- audit_bridge.py
- Docker izolasyonu
- claude-auto-retry (opsiyonel)

**Avantaj:** Taze context, tam kontrol, audit trail
**Dezavantaj:** 290 satır kod gerekir

---

## 🔑 Yetenekler

### 1. Otonom Çalışma
- `--dangerously-skip-permissions` ile onay beklemez
- PROMPT.md kurallarıyla "sorma, varsay" modu
- DECISIONS.md'ye otomatik karar kaydı

### 2. Sıralı Görev Yürütme
- PLAN.md → checkbox sistemi (`- [ ]` / `- [x]`)
- Her turda bir görev
- Alt görev desteği (indent ile)
- Otomatik commit

### 3. Rate-Limit Toleransı
**claude-auto-retry:**
- "5 saatlik limit doldu, 15:00'te sıfırlanır" parse eder
- Otomatik bekler ve devam eder
- 529/overload yakalar

**ralph.sh algılama:**
- Log'da limit ifadesi arar
- `WAIT_ON_LIMIT` saniye bekler
- Kaldığı yerden devam eder

### 4. Güvenlik (Sandbox)
- Docker container izolasyonu
- Tek kullanımlık branch
- Her iterasyon commit (geri alınabilir)
- `MAX_ITERATIONS` sınırı
- Yıkıcı işlem yasağı (PROMPT.md'de)

### 5. Audit & Compliance
- SHA-256 hash zinciri
- Tamper-proof log
- `verify` komutu ile doğrulama
- Plan 2 ile uyumlu format
- Her koşu audit/audit.jsonl'e yazılır

### 6. Context Management
- Her iterasyon **taze context**
- PLAN.md → hafıza
- DECISIONS.md → karar geçmişi
- Log → ilerleme kaydı

---

## 📊 Teknik Karşılaştırma

| Özellik | Reçete A (Native) | Reçete B (Task Master) | Reçete C (Ralph) |
|---------|-------------------|------------------------|------------------|
| Kod satırı | 0 | ~50 (MCP setup) | ~290 |
| Taze context | ❌ | ❌ | ✅ |
| Audit trail | ❌ | Kısmi | ✅ Tam |
| Rate-limit toleransı | Auto-retry ile | Auto-retry ile | Algılama + auto-retry |
| Setup | Kolay | Orta | Orta |
| Kontrol | Claude'un elinde | Task Master'da | Senin elinde |
| Bağımlılık yönetimi | ❌ | ✅ | Manuel (PLAN.md'de) |
| Paralel işlem | `/batch` ile | ❌ | ❌ |

---

## 🎯 Ne Zaman Hangisi?

### Reçete A (Native) - Kullan eğer:
- ✅ Tek iş, hızlı bitir
- ✅ Context window yeterli
- ✅ Sıfır kod istiyorsun
- ❌ Çok uzun plan (context dolar)

### Reçete B (Task Master) - Kullan eğer:
- ✅ Karmaşık bağımlılık ağacı
- ✅ PRD → görev dönüşümü
- ✅ Disiplinli takip
- ❌ Simple task (overkill)

### Reçete C (Ralph) - Kullan eğer:
- ✅ Uzun plan (>50 görev)
- ✅ Taze context şart
- ✅ Tam denetim istiyorsun
- ✅ Audit trail gerekli
- ❌ Hızlı prototype (overhead var)

---

## 🚨 Bilinen Sınırlamalar

1. **Context Window**
   - Native `/goal` context doldurabilir
   - Ralph her turda taze başlar ama büyük proje dosyalarını her turda okur
   - Çözüm: Görevleri küçük tut

2. **Rate Limits**
   - Abonelik limitleri (5 saat/gün)
   - claude-auto-retry bekler ama süre kaybı var
   - Çözüm: Off-peak saatlerde çalıştır

3. **Karmaşık Kararlar**
   - Mimari kararlar hala insan onayı gerektirir
   - DECISIONS.md'ye yazsa da insan review şart
   - Çözüm: Kritik kararları önceden belirle

4. **Maliyet**
   - Abonelik: headless koşular krediden düşer
   - API: Süre sınırı yok ama fatura riski
   - Çözüm: MAX_ITERATIONS ile sınırla

---

## 📦 Bağımlılıklar

### Zorunlu
- Bash 5.0+
- Python 3.11+ (audit_bridge için)
- Git 2.40+
- Claude Code CLI v2.1.139+

### Opsiyonel
- Docker 20.10+ (sandbox için)
- Node.js 20+ (claude-auto-retry için)
- Task Master (Reçete B için)
- Vibe Kanban (görsel takip için)

---

## 🔗 Önemli Linkler

| Kaynak | URL |
|--------|-----|
| Claude Code CLI | npmjs.com/package/@anthropic-ai/claude-code |
| claude-auto-retry | github.com/cheapestinference/claude-auto-retry |
| Task Master | github.com/eyaltoledano/claude-task-master |
| Vibe Kanban | github.com/BloopAI/vibe-kanban |
| Ralph referansları | github.com/dial481/ralph |
|  | github.com/tradesdontlie/ralph-loop-skills |

---

## ✅ İyi Uyan Senaryolar

- ✅ Test yeşilletme
- ✅ Framework migrasyonu
- ✅ Lint/build temizliği
- ✅ Mekanik refactoring
- ✅ "Bitti"yi komutun söyleyebildiği işler

## ❌ Kötü Uyan Senaryolar

- ❌ Açık uçlu/öznel işler
- ❌ Mimari kararlar
- ❌ Production'a dokunan işlemler
- ❌ İnsan yargısı gerektiren işler

---

**Son Güncelleme:** 2026-08-07  
**Versiyon:** 1.0 (Orijinal)  
**Konum:** D:\Vibecode\chromex\claude-code-automation\
