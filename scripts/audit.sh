#!/usr/bin/env bash
# Auditoría mecánica de lo entregado por clite. Uso:
#   scripts/audit.sh [BASE_REF] [ALLOWLIST_FILE]
# BASE_REF: commit/rama contra la que comparar (default HEAD~1)
# ALLOWLIST_FILE: un path/glob por línea con los archivos permitidos (opcional)
# Sale con código != 0 si encuentra violaciones. Imprime solo lo relevante.
set -uo pipefail
BASE="${1:-HEAD~1}"
ALLOW="${2:-}"
fail=0
say() { printf '%s\n' "$*"; }

say "== Resumen =="
git diff --stat "$BASE"...HEAD 2>/dev/null || git diff --stat "$BASE"

ADDED=$(git diff -U0 "$BASE" | grep -E '^\+' | grep -vE '^\+\+\+' || true)

say; say "== Patrones prohibidos en líneas agregadas =="
if echo "$ADDED" | grep -nE '(:\s*any\b|\bas any\b|as unknown as|@ts-ignore|@ts-nocheck|eslint-disable)'; then
  say "FAIL: patrón prohibido"; fail=1
else say "OK"; fi

say; say "== Assertions (no deben disminuir) =="
rem=$(git diff -U0 "$BASE" -- '*test*' '*spec*' | grep -E '^-' | grep -cE '\b(expect|assert)\b' || true)
add=$(git diff -U0 "$BASE" -- '*test*' '*spec*' | grep -E '^\+' | grep -cE '\b(expect|assert)\b' || true)
say "removidas=$rem agregadas=$add"
if [ "$rem" -gt "$add" ]; then say "FAIL: disminuyeron assertions, revisar a mano"; fail=1; else say "OK"; fi

if [ -n "$ALLOW" ] && [ -f "$ALLOW" ]; then
  say; say "== Alcance =="
  while read -r f; do
    ok=0
    while read -r pat; do
      [ -z "$pat" ] && continue
      # shellcheck disable=SC2254
      case "$f" in $pat) ok=1;; esac
    done < "$ALLOW"
    [ $ok -eq 0 ] && { say "FUERA DE ALCANCE: $f"; fail=1; }
  done < <(git diff --name-only "$BASE")
  [ $fail -eq 0 ] && say "OK"
fi

run() { # run <nombre> <cmd...>: muestra solo cola si falla
  local n="$1"; shift
  say; say "== $n =="
  if out=$("$@" 2>&1); then say "OK"; else say "FAIL"; echo "$out" | tail -n 40; fail=1; fi
}
if [ -f package.json ]; then
  for s in typecheck lint test; do
    grep -q "\"$s\"" package.json && run "npm run $s" npm run -s "$s"
  done
fi

say; [ $fail -eq 0 ] && say "AUDITORÍA MECÁNICA: PASA" || say "AUDITORÍA MECÁNICA: FALLA"
exit $fail
