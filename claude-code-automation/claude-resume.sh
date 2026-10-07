#!/usr/bin/env bash
# claude-resume.sh — en yalın dayanıklılık sarmalayıcısı.
# claude başarısız çıkarsa (limit, 529, ağ) POLL saniye bekleyip AYNI komutu
# tekrar dener. "Planı bir bir bitir" beyni burada DEĞİL, ralph.sh + PROMPT.md'de.
#
# Kullanım:
#   bash claude-resume.sh -p "görev..." --dangerously-skip-permissions
#   POLL=600 bash claude-resume.sh ...   # bekleme süresini değiştir
#
# Daha akıllısı (reset saatini parse eden): npm i -g claude-auto-retry
POLL=${POLL:-300}

while true; do
  claude "$@" && break
  echo "Limit/hata — ${POLL}s sonra tekrar deniyorum... (çıkış: Ctrl+C)"
  sleep "$POLL" || break
done
