#!/usr/bin/env bash
# run-sandbox.sh — YOLO modu (--dangerously-skip-permissions) SADECE burada!
# Projeyi node:22-bookworm containerına bağlar; en kötü senaryoda container
# silinir, host makinen etkilenmez.
#
# Kullanım:
#   bash run-sandbox.sh /host/proje/yolu                  # API key ile
#   bash run-sandbox.sh /host/proje/yolu --claude-config  # abonelik girişini taşı
#
# Kimlik:
#   - API anahtarı: önce host'ta  export ANTHROPIC_API_KEY=...
#   - Abonelik (Pro/Max): --claude-config ile ~/.claude içeriye bind edilir.
set -euo pipefail

PROJE=${1:?Kullanım: bash run-sandbox.sh /host/proje/yolu [--claude-config]}
IMAJ=${IMAJ:-node:22-bookworm}

[ -d "$PROJE" ] || { echo "HATA: dizin yok: $PROJE"; exit 1; }

ARGS=(-it --rm -v "$PROJE":/workspace -w /workspace)
[ -n "${ANTHROPIC_API_KEY:-}" ] && ARGS+=(-e ANTHROPIC_API_KEY)

if [ "${2:-}" = "--claude-config" ]; then
  [ -d "$HOME/.claude" ] || { echo "HATA: ~/.claude yok (önce host'ta giriş yap)"; exit 1; }
  ARGS+=(-v "$HOME/.claude":/root/.claude)
fi

exec docker run "${ARGS[@]}" "$IMAJ" bash -lc '
  echo "Claude Code kuruluyor..."
  npm i -g @anthropic-ai/claude-code >/dev/null
  echo
  echo "Sandbox hazır. Örnekler:"
  echo "  claude --dangerously-skip-permissions        # Reçete A (içeride /goal kullan)"
  echo "  MAX=50 bash ralph.sh                         # Reçete C"
  exec bash
'
