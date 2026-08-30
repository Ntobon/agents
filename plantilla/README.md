# <Nombre del agente>

<Una frase: qué hace este agente y para quién.>

## Instalación (sin comandos)

1. Recibes acceso a este agente (carpeta o repo) y lo abres en Claude.
2. Dices: **"quiero instalarlo"** → el skill `<agente>-setup` te guía por todo. Tú solo creas cuentas y autorizas con clics; los comandos los ejecuta Claude.
3. Pruebas con: <ejemplo de primer uso>.

## Las tres capas

| Capa | Dónde vive | ¿Se comparte? |
|---|---|---|
| El motor (skills, CLAUDE.md, setup) | Este repo | ✅ |
| Tu instancia (config) | `local/` (gitignored) | ❌ |
| Tus datos | <tu backend> | ❌ |

## Cómo se actualiza

Plugin atado al repositorio con Sync automatically: cada push actualiza los skills en todas las instalaciones. Ver la metodología en el repo índice `Ntobon/agents`.

## Qué sabe hacer

| Pides | Skill |
|---|---|
| <frase típica> | <skill> |
