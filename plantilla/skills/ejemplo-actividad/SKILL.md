---
name: <actividad>
description: <Qué hace + disparadores literales que diría el usuario, entre comillas. Incluir variantes coloquiales — la descripción es lo único que decide si el skill se activa.>
---

# <Actividad>

<Qué hace este skill, en una frase.>

## Connection & session bootstrap
1. **Working inside the agent repo** (a `local/config.json` exists in the working directory) → read it. If the repo is present but the file is missing, offer to run the **<agente>-setup** skill.
2. **Anywhere else** (claude.ai, mobile app, or Claude Code with the plugin installed in another folder) → check Claude memory for the config. If missing, ask the user once and save it to memory.

<Si hay backend: llamada única de contexto por conversación; cachear; si devuelve reglas personales del usuario, seguirlas toda la sesión.>

## Flujos
### Flujo 1 — <caso típico>
<Entrada del usuario → pasos → salida. Mostrar el formato de respuesta esperado.>

## Reglas
- <Nunca adivinar X; ante ambigüedad preguntar mostrando opciones.>
- <Confirmar antes de operaciones masivas.>

## Error handling
- **Config not found**: ofrecer <agente>-setup.
- <Errores propios del dominio.>
