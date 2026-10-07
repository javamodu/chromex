# Plan 1 — Masaüstünde OS-Level Zorlama ile Claude Code

Kaynak repo: `otonom-ajan-kit/otonom-ajan-kit/`

## Amaç
Bir planı ve alt görevlerini, ajanı durdurmadan ve rate-limit’te bekleyip devam ederek
**OS seviyesinde** tamamlatmak. Kendi yazdığın kod ~20 satır; gerisi hazır araçlar.

## Kullanılan Araçlar
- Claude Code (`claude -p`)
- Task Master
- Vibe Kanban
- `claude-auto-retry`
- Docker
- git

## Ana Döngü
Dosya: `ralph.sh`

- Headless modda `claude -p` çağırır
- `PROMPT.md` kurallarını uygulatır
- `PLAN.md` içindeki ilk işaretsiz `- [ ]` maddesini tamamlatır
- Bitince çıkar; dış döngü onu tekrar çağırır
- Kullanım: `MAX=50 bash ralph.sh`
- Ayarlanabilir: `MAX` (iterasyon), `WAIT` (limit beklemesi sn), `PLAN`, `PROMPT`, `LOG`

## Rate-Limit Stratejisi
Dosya: `claude-resume.sh`

- Hata/limit mesajı geldiğinde `POLL` süresiyle bekleyip tekrar dener
- Daha akıllı alternatif: `claude-auto-retry` kurulumu

## İzolasyon
Dosya: `run-sandbox.sh`

- `node:22-bookworm` containerında projeyi bağlar
- `ANTHROPIC_API_KEY` aktarır
- Gerekirse `~/.claude` bind eder
- Kullanım: `bash run-sandbox.sh /host/proje/yolu`

## Görev Yönetimi
- Reçete A: `PLAN.md` + `PROMPT.md` ile en az kod
- Reçete B: `recete-b-taskmaster.sh` ile PRD → görevler → sıralı yürütme
- Reçete C: `ralph.sh` ile saf zorlama

## Maliyet Kontrolü
- Abonelikte headless otomasyon kredisinden düşer
- API anahtarlarında pratikte süre sınırı yok; ana maliyet budur

## Kritik Kural
Home/prod dizininde asla çalıştırma; tek kullanımlık branch ya da Docker kullan.

## Önerilen Başlangıç Adımları
1. `run-sandbox.sh /host/proje/yolu` ile izole ortam oluştur
2. `PLAN.md` ve `PROMPT.md`yi görevinize göre düzenleyin
3. Reçete A için `claude --dangerously-skip-permissions`
4. Reçete B için Task Master komutlarını sırayla çalıştırın
5. Reçete C için `MAX=50 bash ralph.sh`
