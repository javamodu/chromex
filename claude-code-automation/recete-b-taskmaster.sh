#!/usr/bin/env bash
# recete-b-taskmaster.sh — PRD → görev/alt görev ağacı → sıralı yürütme.
# Adım adım ilerler; model seçimi gibi etkileşimli adımlarda seni bekler.
set -euo pipefail

echo "== 1) Task Master kurulumu =="
npm install -g task-master-ai

echo "== 2) Proje başlatma =="
task-master init

echo "== 3) Model ayarı — listeden 'Claude Code' seçin (ayrı API key GEREKMEZ) =="
task-master models --setup

echo
echo "== 4) PRD =="
echo "Planınızı şu dosyaya koyun:  .taskmaster/docs/prd.txt"
read -r -p "Hazır olunca Enter'a basın... " _

task-master parse-prd .taskmaster/docs/prd.txt

echo "== 5) Karmaşıklık analizi + alt görevlere genişletme =="
task-master analyze-complexity || true   # --research için Perplexity key opsiyonel
task-master expand --all

cat <<'EOT'

== 6) Sıralı yürütme döngüsü ==
  task-master next                      # bağımlılıklara göre SIRADAKİ görev
  task-master show <id>                 # görev/alt görev detayı (ör. 1.2)
  ... görevi Claude Code ile uygula ...
  task-master set-status --id=<id> --status=done
  (tüm görevler bitene kadar tekrarla)

== MCP ile Claude Code'un İÇİNDEN sürmek (önerilen) ==
  claude mcp add task-master-ai --scope user -- npx -y task-master-ai@latest
Sonra Claude Code'a tek cümle:
  "Task Master'daki görevleri next ile sırayla al, her birini uygula,
   tamamlayınca set_task_status ile done işaretle, bitene kadar durma.
   Belirsizlikte sorma; varsay ve update_subtask ile logla."
EOT
