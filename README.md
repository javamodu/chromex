# Chromex - Final Otomasyon Sistemi

İki çalışır otomasyon çözümü: Claude Code otomasyonu ve Windows/Browser otomasyonu.

## 📁 Dizin Yapısı

```
chromex/
├── README.md                        → Bu dosya
├── REHBER.md                        → Araç seçim karar matrisi
├── claude-code-automation/          → Claude Code loop sistemi
│   ├── README.md
│   ├── ralph.sh                     → Ana döngü (taze context ile)
│   ├── audit_bridge.py              → SHA-256 audit köprüsü
│   ├── run-sandbox.sh               → Docker izolasyonu
│   ├── PLAN.md / PROMPT.md / DECISIONS.md → Şablonlar
│   └── docs/                        → Orkestrasyon planı
├── docs/                            → Tasarım taslakları + arşiv (eski TECH envanterleri)
├── policy-gate/                     → (TASLAK) onay+audit pip paketi — bkz. docs/policy-gate-taslak.md
└── windows-browser-automation/      → Windows/Browser otomasyonu
    ├── README.md
    ├── core/                        → approval, audit, policy, http, secrets, store, log
    ├── workers/                     → github, gmail, x, linkedin (API + CDP okuyucu), canva, supabase, vercel
    ├── orchestrator/cli.py          → Tek giriş noktası
    ├── tests/                       → 46 birim test (core + worker + parite, offline)
    ├── config/                      → policy.json, .env.example, MCP config
    └── scripts/                     → setup.ps1, Chrome başlat/durdur
```

## 🎯 Hangi Birini Kullanmalıyım?

| İhtiyaç | Çözüm |
|---------|-------|
| Kodlama görevlerini durmadan tamamlat | → `claude-code-automation/` |
| GitHub/Gmail/X/Supabase/Vercel araştırması | → `windows-browser-automation/` |
| Browser/web scraping | → `windows-browser-automation/` |
| Windows uygulaması kontrolü | → `windows-browser-automation/` |
| Gece boyu kod yazdırma | → `claude-code-automation/` |

## 1️⃣ Claude Code Otomasyonu

**Amaç:** Claude Code'u planları durdurmadan tamamlatmak

### Özellikler
- ✅ Loop sistemi (ralph.sh)
- ✅ Otomatik alt görev tanımlama
- ✅ Rate-limit toleransı
- ✅ PLAN.md → sıralı uygulama
- ✅ Kararları DECISIONS.md'ye loglar
- ✅ Docker sandbox desteği

### Hızlı Başlangıç
```bash
cd YOUR_PROJECT
git checkout -b otonom-test
# PLAN.md, PROMPT.md, DECISIONS.md şablonlarını köke kopyala, PLAN.md'yi doldur
MAX=50 bash /path/to/claude-code-automation/ralph.sh
```

**Detaylar:** [claude-code-automation/README.md](claude-code-automation/README.md)

---

## 2️⃣ Windows & Browser Otomasyonu

**Amaç:** Web servisleri + Windows UI + Güvenlik

### Özellikler
- ✅ API-first (GitHub, Gmail, X, Canva, Supabase, Vercel)
- ✅ Onay kapısı (READ/DRAFT/SEND/MODIFY/DELETE)
- ✅ Audit zinciri (SHA-256)
- ✅ Policy yönetimi
- ✅ MCP entegrasyonu

### Hızlı Başlangıç
```powershell
cd windows-browser-automation
scripts\setup.ps1
copy .env.example .env
python -m orchestrator.cli github-arastir "browser automation"
```

**Detaylar:** [windows-browser-automation/README.md](windows-browser-automation/README.md)

---

## 🔗 İkisini Birlikte Kullanma

**Örnek:** Windows otomasyonu veri toplar → Claude Code kodu yazar

```bash
# Terminal 1: Veri toplama
cd windows-browser-automation
python -m orchestrator.cli github-arastir "browser automation" > data.json

# Terminal 2: Kod geliştirme
cd YOUR_PROJECT
# PLAN.md'ye "data.json'u analiz et" maddesini ekle
MAX=50 bash /path/to/claude-code-automation/ralph.sh
```

---

## 📊 Durum

| Sistem | Durum | Dosyalar |
|--------|-------|----------|
| Claude Code Otomasyonu | ✅ HAZIR | ralph.sh + audit köprüsü + sandbox + şablonlar |
| Windows Otomasyonu | ✅ ÇALIŞIR | core + 8 worker + CLI + 56 test |
| policygate | 🧪 TASLAK | 5 modül + 13 test (docs/policy-gate-taslak.md) |

---

## 📚 Dökümanlar

Her sistem kendi dizininde detaylı README içerir:
- Kurulum adımları
- Kullanım örnekleri
- Yapılandırma
- Sorun giderme

---

**Sürüm:** 1.1.0  
**Oluşturulma:** 2026-08-06  
**Güncelleme:** 2026-10-08  
**Durum:** İki sistem de çalışır durumda
