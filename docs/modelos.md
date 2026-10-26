# Tabla de modelos por nivel (única fuente de verdad)

El resto de la documentación habla de **niveles**; solo este archivo conoce IDs de modelo.
Verificar los IDs vigentes contra el catálogo real antes de usarlos (`clite --help` / listado de modelos de tu cuenta ClinePass).

| Nivel | Modelo (ID en clite) | Estado | Notas |
| :-- | :-- | :-- | :-- |
| N1 | `cline-pass/mimo-v2.6-flash` | por validar | Solo tareas acotadas y verificables |
| N2 | `deepseek-ai/DeepSeek-V3.2` | por validar | Alternativa: `minimax-m2.7` |
| N3 | `deepseek-ai/DeepSeek-V4-Pro` | por validar | Alternativa: `kimi-k2.6` |

Estado: `por validar` → `validado` solo con evidencia en `docs/ledger.csv` (ver estrategia §7).

## Invocación de clite

Los flags exactos dependen de la versión instalada. **Confirmar con `clite --help`** y completar:

```
# Plantilla (ajustar flags reales):
clite <flag-modo-autonomo> <flag-modelo> "<modelo>" <flag-cwd> . "$(cat docs/templates/brief.md renderizado)"
```

Checklist de verificación única (hacerlo una vez):
- [ ] Flag para modo no interactivo / auto-aprobación
- [ ] Flag para elegir modelo por invocación
- [ ] Flag para directorio de trabajo
- [ ] Flag de salida JSON o texto parseable (si existe)
- [ ] Flag de límite de turnos/tiempo (si no existe, envolver con `timeout 20m clite ...`)
