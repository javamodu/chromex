# Plan 2 — Masaüstü ve Tarayıcı Otomasyonu Çözümü

Kaynak repo: `otomasyon-stack/otomasyon-stack/`
Destekleyici belgeler: `desktop-browser-automation.md`, `rf-disi-cozumler.md`, `otomasyon-rehberi-v3.md`

## Amaç
Windows’ta oturum açılmış Chrome ortamında GitHub, X yer işaretleri, Gmail,
Canva ve Supabase/Vercel araştırmasını **en az kodla** yürütmek.
Tarayıcı otomasyonu yalnızca API’nin yetmediği yerde devreye girer;
dış etki yaratan her işlem **onay kapısından** geçer ve
**kurcalamaya dayanıklı audit zincirine** yazılır.

## Katman Modeli
1. API
2. DOM
3. Windows UIA
4. Screen/OCR
5. Blind koordinat

## Önerilen Ana Yol
- Agent yüzeyi: Chrome DevTools MCP / Playwright MCP / Playwright CLI + skills
- Motor: Playwright CDP attach
- Masaüstü: `RPA.Desktop` + `RPA.Windows`
- HTTP: `RPA.HTTP`
- E-posta: `RPA.Email.ImapSmtp`
- İçerik: `bpy`
- Depolama/kanıt: SQLite/JSON audit + onay policy

## RF Dışı Alternatif Yığınları
- Yığın 1 (minimal, ~60 satır): `helium + pywinauto + requests + pywin32`
- Yığın 2 (üretim, ~150 satır, önerilen): `playwright-python + pywinauto + httpx/tenacity + pytest-html`
- Yığın 3 (sıfır kod): `chrome-devtools-mcp + Windows-MCP`

## Hazır Repo Yapısı
- `core/` → secrets, audit, policy, approval, store, HTTP
- `workers/` → github, gmail, x, canva, supabase, vercel
- `orchestrator/cli.py` → komut satırı arayüzü
- `scripts/` → setup, Chrome otomasyon başlat/durdur, Playwright akışları
- `config/mcp.claude-desktop.json` → Claude Desktop MCP yapılandırması

## Kritik Uyarılar
- WinAppDriver bakımsız, kullanma
- Power Automate Desktop “ücretsiz” katmanı premium bağlayıcılar için $15/kişi/ay gerektirir
- Chrome 136+ varsayılan profil debug portunu reddeder; ayrı `user-data-dir` kullan
- CDP portu 9222 yalnızca `127.0.0.1`; iş bitince kapat
- X API owned-reads pay-per-use; büyük çekimlerden önce fiyatı doğrula

## Önerilen Başlangıç Adımları
1. `scripts\setup.ps1` ile ortamı hazırla
2. `scripts\start-chrome-automation.ps1` ile otomasyon profilini başlat, hedef sitelere elle giriş yap
3. `config\mcp.claude-desktop.json` içeriğini istemciye ekle; tek sahip kuralını uygula
4. İlk görev olarak GitHub araması (`github-arastir`) ile stack’i doğrula
5. Gerekirse `workers/` ve `core/` üzerine kendi servis/domain adapter’ını ekle
