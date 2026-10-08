# Otonom Ajan Kit — Claude Code / Codex'i durmadan, sırayla çalıştırma

Bir planı ve alt görevlerini kodlama ajanına **OS seviyesinde, bir bir,
onay için durmadan** tamamlatmak; rate-limit'e takılınca **bekleyip kaldığı
yerden sürdürmek** için minimal kit. Kendi kodun ~330 satır (shell + audit
köprüsü); gerisi hazır araçlar.

```text
Katman 0  Sandbox        → run-sandbox.sh (Docker) / tek kullanımlık branch
Katman 1  Otonomi        → --dangerously-skip-permissions + PROMPT.md kuralları
Katman 2  Sıralı yürütme → PLAN.md kutuları  |  native /goal  |  Task Master
Katman 3  Dayanıklılık   → claude-auto-retry | claude-resume.sh | ralph.sh algılama
Katman 4  Görsel (ops.)  → npx vibe-kanban
```

## Dosyalar

| Dosya | Rol |
|---|---|
| `ralph.sh` | Ana döngü: taze context ile ajanı tekrar tekrar çağırır (Reçete C). Not: 2026 itibarıyla native `/goal` (Reçete A) önceliklidir; ralph.sh eski sürümler ve Codex gibi başka ajanlar için yedek yoldur |
| `audit_bridge.py` | Koşu olaylarını Plan 2 uyumlu SHA-256 hash zincirine yazar (stdlib-only) |
| `PLAN.md` | İşaretlenebilir alt görev listesi — döngünün hafızası |
| `PROMPT.md` | Ajanın her turdaki kuralları: tek madde, sorma-varsay, yıkıcı işlem yok |
| `DECISIONS.md` | Ajanın varsayım/karar günlüğü |
| `claude-resume.sh` | En basit "çökerse bekle-tekrar dene" sarmalayıcı |
| `run-sandbox.sh` | Docker izolasyonu (node:22-bookworm) |
| `recete-b-taskmaster.sh` | PRD → görev ağacı → sıralı yürütme (Task Master) |
| `docs/` | Planın tam metni ve katman anlatımı |

## Hızlı başlangıç (Reçete C — bu kitin ana yolu)

```bash
# 1) İzolasyon — Docker (önerilen):
bash run-sandbox.sh /host/proje/yolu            # API key ile
bash run-sandbox.sh /host/proje/yolu --claude-config   # abonelik girişiyle
#    ...veya en azından:  git checkout -b otonom-run

# 2) Bu kitteki PLAN.md + PROMPT.md + DECISIONS.md'yi proje köküne kopyala,
#    PLAN.md'yi kendi görevlerinle doldur (küçük, doğrulanabilir maddeler).

# 3) Çalıştır:
MAX=50 bash ralph.sh
# Ayarlar: MAX (tur), WAIT (limit beklemesi sn), PLAN, PROMPT, LOG,
# AGENT_CMD (ajan komutu; varsayılan claude — örn. "codex exec
# --dangerously-bypass-approvals-and-sandbox" veya "gemini --yolo")
```

İzleme: `tail -f ralph.log`. Sağlıklı koşuda her turda bir madde `[x]` olur
ve bir commit düşer; olmuyorsa madde büyük/belirsizdir — böl.

## Reçete A — En az parça (native `/goal`)

```bash
npm i -g claude-auto-retry && claude-auto-retry install   # limitte bekle-devam
git checkout -b otonom-run
claude --dangerously-skip-permissions
# içeride:
#   /goal PLAN.md'deki tüm maddeler işaretli, testler geçiyor, lint temiz.
#   Kurallar: sorma; belirsizlikte makul varsayım yap ve DECISIONS.md'ye yaz.
```

Claude Code v2.1.139+ native araçları: `/goal` (bitiş koşuluna kadar çalış),
kalıcı task yönetimi (`Ctrl+T` panel), `/batch` (paralel worktree).

## Reçete B — Yapılandırılmış (Task Master)

```bash
bash recete-b-taskmaster.sh
```

PRD'yi `.taskmaster/docs/prd.txt`e koyar, görev/alt görev ağacına böler,
`task-master next` ile bağımlılık sırasında yürütürsün. MCP olarak Claude
Code'a bağlayıp ajanın kendi kendine sürmesini sağlayabilirsin (script sonu).

## Rate-limit stratejisi

1. **claude-auto-retry** (önerilen): "5 saatlik limit doldu, 15:00'te
   sıfırlanır" mesajındaki saati parse eder, o saate kadar bekler, otomatik
   devam eder; 529/overload'ı da yakalar. `npm i -g claude-auto-retry`.
2. **ralph.sh içi algılama**: log'da limit ifadesi görürse `WAIT` sn bekler.
3. **claude-resume.sh**: tek komutluk işler için kaba bekle-tekrar dene.

## Codex uyarlaması

- Otonomi: `codex --full-auto`
- Reçete B ve Vibe Kanban Codex'i executor olarak destekler.
- `claude-auto-retry` Claude'a özel; Codex'te ralph.sh'nin limit algılaması
  (grep desenini Codex'in mesajına göre güncelle) veya kendi retry ayarları.

## Güvenlik kontrol listesi (okumadan çalıştırma)

- [ ] YOLO + döngü SADECE Docker/tek kullanımlık branch'te; asla home/prod.
- [ ] `PROMPT.md`'de yıkıcı işlem yasağı duruyor (silme, force push, prod).
- [ ] Her iterasyon commit atıyor (geri alınabilirlik).
- [ ] `MAX` sınırı makul (sonsuz döngü + maliyet koruması).
- [ ] Maliyeti izliyorsun: abonelikte headless koşular kredinden düşer;
      API anahtarında süre sınırı yok ama fatura ana risktir.
- [ ] Merge'den önce diff'i İNSAN olarak okuyorsun; `ATLANDI` notlarını elle
      kapatıyorsun.
- [ ] CVE-2025-54795 sonrası döngüyü `claude` içinden değil, KENDİ
      shell'inden çalıştırıyorsun (bu kit zaten öyle).

## Ne zaman hangisi?

- Tek işi AFK bitir → **Reçete A**
- PRD'yi disiplinli görev ağacıyla ilerlet → **Reçete B**
- Maksimum "zorla bitir", taze context, tam kontrol → **Reçete C**
- Çok işi görsel takip → üstüne `npx vibe-kanban`

Ralph iyi uyar: test yeşilletme, framework migrasyonu, lint/build temizliği,
mekanik refactor — "bitti"yi bir komutun söyleyebildiği işler. Kötü uyar:
açık uçlu/öznel işler, mimari kararlar, prod'a dokunan her şey.

## Audit zinciri

ralph.sh her koşuda çalıştığın dizinde `audit/audit.jsonl` oluşturur
(python3 varsa; yoksa sessizce atlanır). run_start, iteration_start,
limit_wait, iteration_error, run_complete/run_max_reached olayları SHA-256
hash zinciriyle eklenir; sonradan yapılan her değişiklik tespit edilir:

```bash
python3 audit_bridge.py verify
```

Format Plan 2'nin `core/audit.py`'siyle birebir aynıdır — iki planın
zincirleri aynı araçla doğrulanabilir. `audit/` dizinini commit etme
(.gitignore'da).

## Repolar

| Araç | Repo |
|---|---|
| claude-auto-retry | github.com/cheapestinference/claude-auto-retry |
| Task Master | github.com/eyaltoledano/claude-task-master |
| Vibe Kanban | github.com/BloopAI/vibe-kanban (community-maintained) |
| Ralph referansları | github.com/dial481/ralph · github.com/tradesdontlie/ralph-loop-skills |
