#!/usr/bin/env bash
# Instala el skill clinepass-setup a nivel usuario (disponible en todos tus proyectos).
set -euo pipefail
DEST="${HOME}/.claude/skills/clinepass-setup"
mkdir -p "$(dirname "$DEST")"
rm -rf "$DEST"
cp -R "$(cd "$(dirname "$0")" && pwd)/skills/clinepass-setup" "$DEST"
echo "Instalado en $DEST. En cualquier proyecto, abrí Claude Code y escribí: /clinepass-setup"
