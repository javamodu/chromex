#!/usr/bin/env bash
# ralph.sh — Ralph Wiggum döngüsü: kodlama ajanını her turda TAZE context ile
# çağırıp PLAN.md'deki maddeleri bir bir bitirtir.
#
# Her iterasyonda:
#   1) $AGENT_CMD "$(cat PROMPT.md)"   (headless; prompt sona eklenir)
#   2) Ajan PLAN.md'deki İLK işaretsiz "- [ ]" maddeyi yapar, testleri koşar,
#      geçerse kutuyu [x] yapıp commit atar ve çıkar.
#   3) Döngü: limit yendiyse bekler; işaretsiz madde kalmadıysa biter.
#
# Kullanım (SADECE izole ortamda — Docker veya tek kullanımlık branch):
#   MAX=50 bash ralph.sh
#
# Ayarlar (env):
#   MAX    : en fazla iterasyon            (varsayılan 50)
#   WAIT   : limit/hata bekleme süresi sn  (varsayılan 900 = 15 dk)
#   PLAN   : plan dosyası                  (varsayılan PLAN.md)
#   PROMPT : ajan talimat dosyası          (varsayılan PROMPT.md)
#   LOG    : log dosyası                   (varsayılan ralph.log)
#   AGENT_CMD : ajan komut şablonu; prompt sona eklenir
#               (varsayılan: claude -p --dangerously-skip-permissions)
#               ör. Codex: AGENT_CMD="codex exec --dangerously-bypass-approvals-and-sandbox"
#               ör. Gemini: AGENT_CMD="gemini --yolo"
set -euo pipefail

MAX=${MAX:-50}
WAIT=${WAIT:-900}
PLAN=${PLAN:-PLAN.md}
PROMPT=${PROMPT:-PROMPT.md}
LOG=${LOG:-ralph.log}
AGENT_CMD=${AGENT_CMD:-"claude -p --dangerously-skip-permissions"}

# Audit köprüsü: iterasyonlar Plan 2 uyumlu hash zincirine yazılır
# (python3 yoksa sessizce atlanır; doğrulama: python3 audit_bridge.py verify)
KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRIDGE="$KIT_DIR/audit_bridge.py"
audit_log() {
  command -v python3 >/dev/null 2>&1 && [ -f "$BRIDGE" ] \
    && python3 "$BRIDGE" log "$@" >/dev/null 2>&1 || true
}

# --- Ön kontroller ---------------------------------------------------------
command -v "${AGENT_CMD%% *}" >/dev/null 2>&1 || {
  echo "HATA: '${AGENT_CMD%% *}' bulunamadı — AGENT_CMD değişkenini kontrol et."
  exit 1; }
[ -f "$PLAN" ]   || { echo "HATA: $PLAN yok. Önce planını yaz."; exit 1; }
[ -f "$PROMPT" ] || { echo "HATA: $PROMPT yok. Ajan kurallarını yaz."; exit 1; }

if [ ! -d .git ]; then
  echo "UYARI: Burası bir git deposu değil — geri dönüş noktan olmayacak."
  echo "       Devam etmek için 5 sn... (iptal: Ctrl+C)"
  sleep 5
fi

# --- Ana döngü --------------------------------------------------------------
audit_log run_start "max=$MAX" "plan=$PLAN"
for i in $(seq 1 "$MAX"); do
  # Önce bitiş kontrolü: işaretsiz madde kalmadıysa çık.
  if ! grep -Eq '^[[:space:]]*- \[ \]' "$PLAN"; then
    echo "TAMAM: $PLAN içindeki tüm maddeler işaretli." | tee -a "$LOG"
    audit_log run_complete "iterasyon=$i"
    exit 0
  fi

  echo "=== İterasyon $i / $MAX — $(date '+%Y-%m-%d %H:%M:%S') ===" | tee -a "$LOG"
  audit_log iteration_start "i=$i" "max=$MAX"

  iter_log="$(mktemp)"
  set +e
  # Kelime bölme bilinçli: AGENT_CMD birden çok token içerir (ör. "codex exec ...")
  $AGENT_CMD "$(cat "$PROMPT")" 2>&1 | tee "$iter_log"
  status=${PIPESTATUS[0]}
  set -e
  cat "$iter_log" >> "$LOG"

  # Rate-limit / overload algılama: YALNIZCA bu iterasyonun çıktısına bakılır
  # (birikmiş log'a bakmak bir önceki turun mesajıyla yanlış alarm verir).
  if grep -qiE 'limit reached|usage limit|rate.?limit|overloaded|529' "$iter_log"; then
    rm -f "$iter_log"
    echo "Limit algılandı — ${WAIT}s bekleniyor..." | tee -a "$LOG"
    audit_log limit_wait "i=$i" "bekleme_sn=$WAIT"
    sleep "$WAIT"
    continue
  fi
  rm -f "$iter_log"

  if [ "$status" -ne 0 ]; then
    echo "ajan çıkış kodu: $status — ${WAIT}s sonra tekrar." | tee -a "$LOG"
    audit_log iteration_error "i=$i" "exit=$status"
    sleep "$WAIT"
  fi
done

echo "DUR: MAX=$MAX iterasyona ulaşıldı; $PLAN ve $LOG dosyalarını incele." | tee -a "$LOG"
audit_log run_max_reached "max=$MAX"
exit 1
