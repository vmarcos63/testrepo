#!/usr/bin/env bash
# Uso: scripts/run-clite.sh <N1|N2|N3> <archivo-brief.md> [--plan]
# Corre clite con el modelo/razonamiento del nivel, con tope de tiempo y reintentos.
set -euo pipefail
LEVEL="${1:?nivel N1|N2|N3}"; BRIEF="${2:?archivo brief}"; shift 2
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/docs/modelos.env"
M="${LEVEL}_MODEL"; T="${LEVEL}_THINKING"
MODEL="${!M:?nivel desconocido}"; THINK="${!T}"
EXTRA=(); [ "${1:-}" = "--plan" ] && EXTRA+=(--plan)
echo ">> clite nivel=$LEVEL modelo=$MODEL thinking=$THINK" >&2
exec clite "${EXTRA[@]}" -m "$MODEL" --thinking "$THINK" \
  -t "$TIMEOUT_SECONDS" --retries "$MAX_RETRIES" -c "$PWD" "$(cat "$BRIEF")"
