# Chromex - Final Otomasyon Sistemi

İki çalışır otomasyon çözümü: Claude Code otomasyonu ve Windows/Browser otomasyonu.

## 🧭 SSOT

1. `ANAYASA.md` — değişmez kurallar ve LOC tavanı
2. `AGENTS.md` — ajan çalışma kuralları
3. `DESIGN_MANIFESTO.md` — tasarım felsefesi
4. `GLOSSARY.md` — ortak sözlük
5. `plans/FAZ2-SPRINTLER.md` — canlı testli Faz 2 planı
6. `README.md` — kullanıcı yüzeyi
7. `STATE_BOARD.md` — durum takibi

Çelişkide üst sıra kazanır. Toplam LOC tavanı **9.000**; aşım durumunda yeni iş açılmaz.

## 📁 Dizin Yapısı

```
chromex/
├── README.md                        → Bu dosya
├── REHBER.md                        → Araç seçim karar matrisi
├── claude-code-automation/          → Claude Code loop sistemi
│   ├── README.md
│   ├── ralph.sh                     → Ana döngü (taze context ile)
│   ├── audit_bridge.py              → SHA-256 audit köprüsü
│   ├── model_manager.py             → Paseo CLI model yönetimi ve `sor` komutu (varsayılan: glm-5.3)
│   ├── models.json                  → Sağlayıcı/model kayıt defteri
│   ├── run-sandbox.sh               → Docker izolasyonu
│   ├── PLAN.md / PROMPT.md / DECISIONS.md → Şablonlar
│   └── docs/                        → Orkestrasyon planı
├── docs/                            → Tasarım taslakları + arşiv (eski TECH envanterleri)
├── policy-gate/                     → policygate paketi (v1.1.0, güncel): onay kapısı + audit zinciri
└── windows-browser-automation/      → Windows/Browser otomasyonu
    ├── README.md
    ├── core/                        → store (SQLite), http köprüsü, oauth (güvenlik çekirdeği policygate'te)
    ├── workers/                     → github, gmail, x, linkedin (API + CDP okuyucu), canva, supabase, vercel
    ├── orchestrator/cli.py          → Tek giriş noktası
    ├── mcp_server/                  → 20 CLI komutunu MCP tool'ına çevirir
    │   ├── tests/                       → 75 birim test (core + worker + MCP + parite, offline)
    ├── config/                      → policy.json, MCP config (.env.example paket kökünde)
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
- ✅ Paseo model yönetimi ve güvenli `sor` komutu (varsayılan `glm-5.3`)
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
- ✅ MCP sunucusu (`chromex-mcp`, 21 tool)

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
| Windows Otomasyonu | ✅ ÇALIŞIR | core + 9 worker + CLI + MCP sunucusu + 75 test |
| policygate | ✅ v1.1.0 (güncel) | 6 modül + 41 test (docs/policy-gate-taslak.md) |

Faz 2 sprintleri: `plans/FAZ2-SPRINTLER.md`

---

## 📚 Dökümanlar

Her sistem kendi dizininde detaylı README içerir:
- Kurulum adımları
- Kullanım örnekleri
- Yapılandırma
- Sorun giderme

---

**Toplam test:** 126 (policygate 41 + wba 75 + model yönetimi 10)

**Geçiş kapısı senaryosu:**
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\gecis_kapisi.ps1
```

Canlı model testi için `-Canli`, Chrome CDP aç/kapa testi için `-Chrome` ekleyin.
**Sürüm:** 1.1.0  
**Oluşturulma:** 2026-08-06  
**Güncelleme:** 2026-10-30
**Durum:** Çekirdek çalışır; Faz 2 Sprint 4 model çağrısı canlı doğrulandı
