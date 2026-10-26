## Protocolo ClinePass (pegar en el CLAUDE.md del proyecto)

Soy el arquitecto/auditor. No implemento en bloque: delego a `clite` según `docs/clinepass-strategy.md`.
1. Clasifico el nivel (N0–N3) por riesgo; dominios críticos en `docs/dominios-criticos.md`.
2. Escribo un brief con `docs/templates/brief.md` (en `.briefs/T-XXX.md`) y creo un branch `task/T-XXX`.
3. Ejecuto `scripts/run-clite.sh <N1|N2|N3> .briefs/T-XXX.md`.
4. Audito con `scripts/audit.sh <base> [allowlist]`; reviso según el nivel (§4). No leo logs completos.
5. Si falla: escalo según §6. Registro cada tarea en `docs/ledger.csv`.
6. Nunca hago push sin que el usuario lo pida.
