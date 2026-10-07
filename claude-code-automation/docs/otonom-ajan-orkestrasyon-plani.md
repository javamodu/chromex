# Otonom Kodlama Ajanı Orkestrasyon Planı
### Claude Code / Codex'i planı ve alt görevleri sırayla, durmadan tamamlatmak için uçtan uca kurulum

---

## 0. Amaç

Bir plan (ve alt görevleri) verildiğinde, kodlama ajanının:

1. Görevleri **sırayla, bir bir** OS seviyesinde tamamlaması,
2. Onay/soru için durmayıp **kendi kendine karar verip devam etmesi**,
3. İnternet / rate-limit sınırına takılınca **bahane üretmeden bekleyip kaldığı yerden sürdürmesi**,
4. Bunların **mümkün olan en az kodla / hazır repolarla** kurulması.

Bu dört ihtiyaç birbirinden bağımsız katmanlar. Aşağıda önce her katmanın hangi araçla çözüldüğünü, sonra hepsini birleştiren üç hazır **reçete** veriyorum. Kendine uyanı seç.

---

## 1. Mimari — Katmanlı bakış

| Katman | İhtiyaç | Çözüm |
|--------|---------|-------|
| **0. Sandbox** | Güvenlik (zorunlu) | Docker container / tek kullanımlık repo + branch |
| **1. Otonomi** | Onay için durmama | `--dangerously-skip-permissions` (YOLO) + prompt ile "sorma, varsay" talimatı |
| **2. Sıralı yürütme** | Plan → alt görev bir bir | Native `/goal` + task yönetimi **veya** Task Master |
| **3. Dayanıklılık** | Rate-limit bahanesi yok | `claude-auto-retry` |
| **4. Görselleştirme** *(ops.)* | Çoklu ajan / takip | Vibe Kanban |

Önemli tespit: **Katman 1, 2 ve kısmen 3 artık Claude Code'un içinde** native olarak var. Dışarıdan gerçekten eklemen gereken tek kritik parça, senin en çok istediğin rate-limit toleransı (Katman 3). Dolayısıyla "en az kod" hedefin fazlasıyla ulaşılabilir.

---

## 2. Katman 0 — Güvenli sandbox (önce bunu oku)

`--dangerously-skip-permissions` + döngü kombinasyonu güçlü ama **gerçek bir foot-gun**. Ajan, döngüden çıkmak için "tamamlandı" sözünü tutmaya çalışırken yanlış yola saparsa ev dizinini silmeye, config dosyalarını bozmaya kadar gidebilir — bunlar topluluğun yaşadığı gerçek vakalar. Bu yüzden **her zaman izole bir ortamda** çalıştır.

**En basit izolasyon — tek kullanımlık branch (hızlı ama zayıf):**
```bash
cd projem
git checkout -b otonom-deneme
# iş biterse: beğenmezsen  git checkout main && git branch -D otonom-deneme
```

**Güçlü izolasyon — Docker (önerilen):**
```bash
# Node + git içeren bir container, projeni içine bağla
docker run -it --rm \
  -v "$PWD":/workspace -w /workspace \
  -e ANTHROPIC_API_KEY \
  node:22-bookworm bash

# Container içinde:
npm i -g @anthropic-ai/claude-code
```
Container içinde YOLO modu çalıştırırsan, en kötü senaryoda sadece container'ı silersin; host makinen etkilenmez.

> Kural: YOLO + döngü **asla** prod dizininde, asla host home'unda. Sadece sandbox.

---

## 3. Katman 1 — Otonomi (durmadan çalışma)

İki farklı "durma" var, ikisini ayrı çöz:

**a) İzin dialog'ları (dosya yaz, komut çalıştır → "onaylıyor musun?")**
Bunu `--dangerously-skip-permissions` (YOLO modu) kapatır:
```bash
claude --dangerously-skip-permissions
# veya headless:
claude -p "görev..." --dangerously-skip-permissions
```
`-p` (print/headless) modu: promptu al, işi yap, çık — döngüye sokmak için ideal.

**b) Belirsizlik soruları ("PostgreSQL mi MongoDB mi kullanayım?")**
Bunu bayrak çözmez; **prompt mühendisliğiyle** çözersin. Ajana açıkça "kullanıcıya sorma, makul varsayım yap ve varsayımını `DECISIONS.md`'ye yaz" dersin. Senin "soru sorarsa cevaplayacak" isteğinin gerçek karşılığı bu: soruları önceden cevaplamak yerine, **ajana kendi kararını verme yetkisi** verirsin. (Şablon Bölüm 8'de.)

---

## 4. Katman 2 — Planı ve alt görevleri sırayla yürütme

İki yol var. Basitten karmaşığa:

### Yol A — Claude Code'un native araçları (kod yok, sürüm-güncel)

Yeni sürümlerde (v2.1.139+) tam bu iş için komutlar geldi ve bunlar plugin değil, sürüm güncellemelerinde de yaşıyor:

- **`/goal <koşul>`** → bir bitiş koşulu verirsin, bir değerlendirici model her turda kontrol eder, koşul sağlanana kadar çalışır. "Zorla tamamlat"ın native hali.
  ```
  /goal PLAN.md'deki tüm maddeler tamam, tüm testler geçiyor ve lint temiz
  ```
- **Native task yönetimi** → görevleri bağımlılıklarıyla oluşturur, oturumlar arası kalıcıdır, biri bitince kilidi açılan sıradaki otomatik başlar:
  ```
  claude "kullanıcı auth özelliğini bağımlılıklı alt görevlere böl ve sırayla uygula"
  ```
  Terminalde `Ctrl+T` ile görev panelini aç/kapat.
- **`/batch`** → tek büyük değişikliği 5–30 paralel worktree ajanına dağıtır (sıralı değil, paralel; büyük mekanik refactor için).

### Yol B — Task Master (PRD → görev/alt görev → sıralı)

Senin tarif ettiğin "plan dökümanı → alt görevler → bir bir yürüt" akışına birebir oturan repo bu. Planlamayı (orchestrator) yürütmeden (executor) ayırır, ilerlemeyi izler, görev bitince bir sonrakini otomatik açar. (Kurulumu Reçete B'de detaylı.)

---

## 5. Katman 3 — Rate-limit toleransı (`claude-auto-retry`)

Senin en çok vurguladığın kısım için birebir yapılmış araç. Claude Code "5 saatlik limit doldu, 15:00'te sıfırlanır" dediğinde, mesajdaki reset saatini parse edip (timezone/DST farkında) o saate kadar bekler ve otomatik `continue` gönderir. 529/5xx overload ve safeguard false-positive'lerini de yakalar. tmux tabanlı ama tmux'ı senden gizler; sıfır bağımlılık, iş akışını değiştirmez.

```bash
npm i -g claude-auto-retry
claude-auto-retry install
# Bundan sonra 'claude'u normal kullan; limit gelince kendi bekleyip devam eder.
# 'claude -p "..." | jq' gibi pipe kullanımını da destekler (buffer + retry).
```

**Aynı işin 5 satırlık DIY hali** (hazır aracı istemezsen — exit code'a bakıp tekrar dener):
```bash
#!/usr/bin/env bash
# claude-resume.sh
POLL=${POLL:-300}
while true; do
  claude "$@" && break
  echo "Limit/hata — ${POLL}s sonra tekrar deniyorum... (Ctrl+C çıkış)"
  sleep "$POLL" || break
done
```

---

## 6. Katman 4 (opsiyonel) — Görsel orkestrasyon (Vibe Kanban)

Birden fazla işi tek yerden, görsel takip etmek ve PR'lara bağlamak istersen. Kartı To Do → In Progress → Done taşıyınca izole git worktree açıp bağlı ajanı çalıştırır; Claude Code, Codex, Gemini dahil 10+ ajan destekler.
```bash
npx vibe-kanban          # → http://localhost:3000
PORT=3001 npx vibe-kanban --port 3001   # port çakışırsa
```
> **Not:** Arkasındaki şirket (bloop) kapanıyor; proje open-source / community-maintained olarak devam edecek. Yeni bir bağımlılık seçerken bakım hızını göz önünde bulundur.

---

## 7. REÇETELER — Hepsini birleştir

### 🟢 Reçete A — En Az Kod / Hemen Kullan
> Tek sıralı görev akışını AFK bırakıp bitirmek için en yalın yol. Yeni repo yazımı = sıfır.

```bash
# 1) Rate-limit toleransını kur (bir kez)
npm i -g claude-auto-retry && claude-auto-retry install

# 2) Sandbox'a gir (Docker veya en azından yeni branch)
git checkout -b otonom-run

# 3) Planını ve otonomi kurallarını dosyaya koy
#    (PLAN.md + PROMPT-KURALLARI için Bölüm 8 şablonu)

# 4) YOLO + /goal ile başlat
claude --dangerously-skip-permissions
# Ajan açılınca:
#   /goal PLAN.md'deki tüm kutular işaretli, testler geçiyor, lint temiz.
#   Kurallar: kullanıcıya sorma; belirsizlikte makul varsayım yap ve DECISIONS.md'ye yaz.
```
Böylece: `/goal` → tamamlanana kadar çalışır; `--dangerously-skip-permissions` → onay için durmaz; `claude-auto-retry` → limit gelince bekleyip sürdürür.

---

### 🔵 Reçete B — Yapılandırılmış / Repo Tabanlı (Task Master)
> PRD → görev/alt görev ağacı → bağımlılık sırasına göre yürütme istiyorsan.

```bash
# 1) Kur ve projede başlat
npm install -g task-master-ai
cd projem
task-master init                 # klasör yapısını ve kuralları kurar

# 2) Modeli ayarla — Claude Code CLI ile API KEY GEREKMEZ
task-master models --setup       # listeden "Claude Code" seç

# 3) Planını PRD olarak yaz, sonra görevlere böl
#    Planını buraya koy:  .taskmaster/docs/prd.txt
task-master parse-prd .taskmaster/docs/prd.txt

# 4) Alt görevlere genişlet (karmaşık görevleri parçala)
task-master analyze-complexity   # (--research istersen Perplexity key gerekir; opsiyonel)
task-master expand --all

# 5) Sıralı yürütme döngüsü
task-master next                 # bağımlılıklara göre SIRADAKİ görevi verir
task-master show 1.2             # belirli görev/alt görev detayı
# ... Claude Code ile o görevi uygula ...
task-master set-status --id=1.2 --status=done
# tekrar: task-master next → bir sonraki otomatik gelir
```

**Task Master'ı Claude Code'un İÇİNE (MCP) bağlarsan**, ajan bu adımları kendi çağırır — sen sadece "sıradaki görevi al, uygula, done işaretle, devam et" dersin:
```bash
claude mcp add task-master-ai --scope user -- npx -y task-master-ai@latest
```
Sonra Claude Code içinde tek cümle:
> "Task Master'daki görevleri `next` ile sırayla al, her birini uygula, tamamlayınca `set_task_status` ile done işaretle, tüm görevler bitene kadar durma. Belirsizlikte bana sorma, varsay ve `update_subtask` ile logla."

Bunu `--dangerously-skip-permissions` + `claude-auto-retry` ile birleştirince Reçete A'nın disiplinli versiyonunu almış olursun.

---

### 🟣 Reçete C — Saf OS-Level Zorlama (Ralph Wiggum döngüsü)
> "Bash döngüsü ajanı kafasını kapıya vura vura bitirsin" yaklaşımı. Her iterasyonda **taze context** (context çürümesini engeller); durum dosya sistemi + git'te tutulur.

`ralph.sh` — çalıştığın (izole) dizinde `bash ralph.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
MAX=${MAX:-50}

for i in $(seq 1 "$MAX"); do
  echo "=== İterasyon $i / $MAX ==="

  # PROMPT.md ajana der ki: PLAN.md'deki SIRADAKİ işaretsiz maddeyi al,
  # SADECE onu yap, test et, geçerse kutuyu [x] yap + commit et, sonra çık.
  claude -p "$(cat PROMPT.md)" --dangerously-skip-permissions 2>&1 | tee -a ralph.log

  # Basit rate-limit koruması: logda limit görürsek bekle, aynı iterasyonu tekrarla
  if tail -n 20 ralph.log | grep -qiE "limit reached|usage limit|rate.?limit"; then
    echo "Limit algılandı, 15 dk bekliyorum..."; sleep 900; continue
  fi

  # Tüm kutular işaretliyse bitir
  if ! grep -q '^- \[ \]' PLAN.md; then
    echo "✅ Tüm görevler tamamlandı."; break
  fi
done
```
> Not: CVE-2025-54795 sonrası `claude` **komutunun içinde** çok satırlı bash / `$()` engelleniyor. Bu yüzden döngüyü **kendi shell'inden** çalıştırmak (yukarıdaki gibi) resmi `ralph-wiggum` plugin'inden daha sağlam. Hazır bir referans uygulama istersen: `dial481/ralph` ya da `tradesdontlie/ralph-loop-skills`.

---

## 8. Kritik parça — Plan ve prompt şablonu

"Sırayla bir bir" ve "sorma, kendin cevapla" davranışı büyük ölçüde **bu iki dosyada** yaşıyor.

**`PLAN.md`** (alt görevler = işaretlenebilir kutular, sıralı):
```markdown
# Uygulama Planı

## Faz 1 — Kurulum
- [ ] 1. Proje iskeletini oluştur (paket yöneticisi, dizin yapısı)
- [ ] 2. Lint + test altyapısını kur

## Faz 2 — Özellikler
- [ ] 3. Veri modelini tanımla
- [ ] 4. API uçlarını yaz + testleri
- [ ] 5. ...
```

**`PROMPT.md`** (ajanın her turda okuduğu talimat — otonomiyi burada tanımlarsın):
```markdown
Sen otonom bir kodlama ajanısın. Kurallar:

1. PLAN.md'yi oku. Sıradaki İLK işaretsiz `- [ ]` maddeyi seç.
2. SADECE o maddeyi uygula. Kapsamı genişletme, ilgisiz refactor yapma.
3. Değişiklikten sonra ilgili testleri/lint'i çalıştır.
4. Testler geçerse: PLAN.md'de o maddeyi `- [x]` yap ve anlamlı bir mesajla commit et.
5. Sonra çık (döngü seni yeniden çağıracak).

Belirsizlik / karar gerektiren durumlar:
- Kullanıcıya SORMA. Makul, yaygın bir varsayım yap.
- Yaptığın her varsayımı DECISIONS.md'ye tek satırla yaz (tarih + karar + gerekçe).
- Geri dönülemez/yıkıcı işlemlerden (dosya silme, force push, prod'a dokunma) kaçın.
```
Bu `PROMPT.md`, `--dangerously-skip-permissions`'ın kapatamadığı **belirsizlik sorularını** çözer: ajanı "sor" yerine "karar ver ve kaydet" moduna alır.

---

## 9. Codex uyarlaması

- Codex'in kendi otonom modu var: `codex --full-auto` (onay atlamalı yürütme).
- **Task Master ve Vibe Kanban Codex'i executor olarak destekliyor** — yani Reçete B ve görsel akış Codex'le de aynen çalışır.
- Tek fark: `claude-auto-retry` Claude-Code'a özel. Codex tarafında rate-limit toleransı için **Reçete C'deki bash döngüsü + limit-algılama** ya da Codex'in kendi retry ayarlarını kullan.

---

## 10. Güvenlik kontrol listesi

- [ ] YOLO + döngü **sadece** Docker container veya tek kullanımlık branch'te.
- [ ] `PROMPT.md`'de "yıkıcı işlem yapma / prod'a dokunma" kuralı var.
- [ ] Her iterasyon commit atıyor (geri alınabilirlik + ilerleme takibi).
- [ ] `MAX` iterasyon limiti koydun (sonsuz döngü + maliyet koruması).
- [ ] API/subscription maliyetini izliyorsun (uzun otonom koşular hızlı harcar).
- [ ] Çıktıyı merge etmeden önce diff'i insan olarak gözden geçiriyorsun.

---

## 11. Karar rehberi — hangisini seçeyim?

- **Tek işi AFK bitir, uğraşma** → **Reçete A** (native `/goal` + skip-perms + auto-retry).
- **Net bir PRD'yi görev ağacına bölüp disiplinli ilerlet** → **Reçete B** (Task Master).
- **Maksimum "zorla bitir", taze context, tam kontrol** → **Reçete C** (Ralph bash döngüsü).
- **Çok işi görsel takip + PR'lara bağla** → üstüne **Katman 4** (Vibe Kanban).

En pratik başlangıç: **Reçete A**'yı bir Docker sandbox'ında dene. İşe yararsa, plan disiplini için Task Master'ı (Reçete B) ekle.

---

### Repolar
| Araç | Repo | Rolü |
|------|------|------|
| claude-auto-retry | `github.com/cheapestinference/claude-auto-retry` | Rate-limit / 529 toleransı |
| Task Master | `github.com/eyaltoledano/claude-task-master` | PRD → görev/alt görev, sıralı yürütme |
| Vibe Kanban | `github.com/BloopAI/vibe-kanban` | Görsel çok-ajan orkestrasyon |
| Ralph (referans) | `github.com/dial481/ralph` · `github.com/tradesdontlie/ralph-loop-skills` | OS-level otonom döngü |
