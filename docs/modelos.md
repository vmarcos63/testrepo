# Modelos por nivel

La fuente de verdad ejecutable es `docs/modelos.env` (la lee `scripts/run-clite.sh`). Este archivo explica el porqué.

## Catálogo ClinePass (doc oficial, oct-2026)
Vigentes: GLM-5.3, GLM-5.3 Flash, Kimi K3, DeepSeek V4 Pro, DeepSeek V4.1 Flash, MiMo-V2.5, MiMo-V2.5-Pro, MiniMax M3, Muse Spark 1.3 Contributor, Qwen3.8 Max, Qwen3.7 Max, Qwen3.7 Plus.
Retirados: GLM-5.2, Kimi K2.6, Kimi K2.7 Code, DeepSeek V4 Flash (y DeepSeek V3.2 ya no figura).
MiMo V2.6 Flash/Pro: estado discrepante entre fuentes; no usar.
Formato de ID: `cline-pass/<modelo>`. IDs confirmados en fuentes: `kimi-k3`, `deepseek-v4-pro`, `deepseek-v4.1-flash`, `mimo-v2.5`, `mimo-v2.5-pro`, `minimax-m3`, `glm-5.3`. El resto: confirmar en tu selector.

## Asignación inicial (HIPÓTESIS, no benchmark)
| Nivel | Modelo | Razonamiento | Alternativa |
| :-- | :-- | :-- | :-- |
| N1 | `deepseek-v4.1-flash` | low | `mimo-v2.5` |
| N2 | `minimax-m3` | medium | `mimo-v2.5-pro`, `glm-5.3` |
| N3 | `deepseek-v4-pro` | high | `kimi-k3` |

El nivel de razonamiento (`--thinking`) es una segunda palanca de ahorro: razonar menos en tareas simples.
Se ajusta con `docs/ledger.csv` tras ~20 tareas.

## Flags de clite usados (de `clite --help`)
`-m` modelo · `--thinking` · `-t` timeout (s) · `--retries` · `-c` cwd · `-p/--plan` solo planificar · `--json` salida parseable.
`--auto-approve` es **true por defecto**: clite ejecuta comandos y edita sin preguntar. Correr siempre en un branch/worktree por tarea.
