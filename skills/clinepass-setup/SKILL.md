---
name: clinepass-setup
description: Configura el proyecto actual para trabajar con Claude Code como arquitecto/auditor y Cline CLI (clite, ClinePass) como ejecutor, optimizando tokens sin perder calidad. Usar cuando el usuario pida "setup clinepass", "configurar cline + claude code", "delegar a clite" o "eficientizar tokens con ClinePass". También para refrescar IDs de modelo en un proyecto ya configurado.
---

# clinepass-setup

Instala en el proyecto actual el protocolo de orquestación (niveles N0–N3, briefs, auditoría mecánica, escalación, ledger). Hacelo vos, sin pedirle al usuario que copie archivos. Los archivos fuente están en `assets/` junto a este SKILL.md.

## Pasos

1. **Preflight** (en el directorio del proyecto):
   - `git rev-parse --is-inside-work-tree`; si no es repo, avisar y ofrecer `git init`.
   - `clite --version` y `clite config`. Si `clite` no existe o no hay provider/auth, detenerte e indicar `clite auth` (no inventar credenciales).
   - Detectar stack: `package.json` (scripts typecheck/lint/test), `pyproject.toml`/`pytest`, `go.mod`, `Cargo.toml`, etc.
2. **Copiar assets sin pisar nada**: `assets/docs/` → `docs/`, `assets/scripts/` → `scripts/`. Si un destino ya existe y difiere, mostrar diff y preguntar. `chmod +x scripts/*.sh`. Crear `.briefs/` y agregarlo a `.gitignore`.
3. **Validar modelos**: comparar los IDs de `docs/modelos.env` con los disponibles según `clite config`. Si alguno no existe, buscar el reemplazo vigente (doc oficial: https://docs.cline.bot/getting-started/clinepass) y proponer el cambio al usuario. Los IDs solo viven en `docs/modelos.env`.
4. **Checks del stack**: si no es Node con scripts `typecheck/lint/test`, copiar `docs/audit.conf.example` a `docs/audit.conf` y ajustarlo (ruff/mypy/pytest, go vet/test, cargo clippy/test, etc.). Ejecutar cada check una vez para confirmar que funciona.
5. **Dominios críticos**: escanear el repo (pagos, auth/permisos, migraciones/esquema DB, concurrencia, contratos públicos) y proponer un borrador de `docs/dominios-criticos.md` con rutas concretas. Pedir confirmación al usuario antes de dejarlo final.
6. **CLAUDE.md del proyecto**: agregar el contenido de `assets/docs/CLAUDE.snippet.md` entre marcadores `<!-- clinepass:start -->` y `<!-- clinepass:end -->`; si ya están, reemplazar el bloque (idempotente). Crear `docs/decisiones.md` si no existe.
7. **Smoke test**: crear un brief trivial de N1 en `.briefs/T-000.md` (p. ej. "agregar un comentario de una línea en un archivo de docs") y correr `scripts/run-clite.sh N1 .briefs/T-000.md --plan`. Luego `scripts/audit.sh`. Reportar si funciona; no dejar cambios de la prueba.
8. **Resumen final** (breve): qué se instaló, modelos por nivel, qué quedó pendiente de confirmar (dominios críticos, IDs dudosos).

## Reglas de operación posteriores (ya quedan en el CLAUDE.md del proyecto)

Seguir `docs/clinepass-strategy.md`: clasificar por riesgo, brief con `docs/templates/brief.md`, un branch por tarea, `scripts/run-clite.sh`, `scripts/audit.sh`, revisión proporcional al nivel, escalar N1→N2→N3→Claude→usuario, registrar en `docs/ledger.csv`. Nunca push sin pedido del usuario. clite corre con auto-aprobación: siempre en branch/worktree aislado.
