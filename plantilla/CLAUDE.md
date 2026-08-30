# <Nombre del agente> — <qué es>

<Descripción corta del agente y su dominio.>

**Arquitectura de tres capas**: el motor (este repo, 100% agnóstico) / la instancia (`local/`, gitignored) / los datos (backend del usuario). Regla de oro: **nada personal fuera de `local/` y del backend** — las reglas personales del usuario viven en su configuración, nunca hardcodeadas en un skill.

## Bootstrap de sesión (obligatorio antes de operar)

1. Si existe `local/config.json` en el directorio de trabajo → leerlo.
2. En cualquier otro lado (claude.ai, celular, Claude Code vía plugin en otra carpeta) → buscar la config en la memoria de Claude; si falta, preguntar una vez y guardarla.
3. Si no hay config en ningún lado → ofrecer el skill `<agente>-setup`.

<Si hay backend: llamada única de contexto por conversación, cachear, y tratar las reglas personales del usuario como instrucciones de la sesión.>

## Skills

| Skill | Cuándo |
|---|---|
| `<agente>-setup` | Instalar/provisionar una instancia nueva |
| `<actividad>` | <disparadores> |

## Convenciones

- <Formatos, confirmaciones, idioma.>
- Los archivos generados para el usuario van en `local/exports/`.
