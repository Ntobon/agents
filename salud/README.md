# Salud

Informes de salud personalizados e imprimibles (PDF, en español) por miembro de la familia, a partir de exámenes de laboratorio. Adapta las recomendaciones a la edad del paciente (pediátrico → adulto mayor, con des-intensificación de tamizajes basada en evidencia) y al contexto del sistema de salud colombiano (EPS).

## Instalación

Este agente es liviano (sin backend). Se instala como parte del marketplace `Ntobon/agents`:
- **claude.ai** (web + celular): Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → Add.
- **Claude Code**: `claude plugin marketplace add Ntobon/agents` + `claude plugin install salud@ntobon-agents`.

## Uso

1. Crea un Proyecto de Claude por familiar (p. ej. "Salud Papá") y sube ahí sus exámenes (PDF).
2. Di: **"hazme el informe de salud"** — el skill detecta solo la identidad, la edad y los informes previos desde el proyecto.
3. Recibes un PDF listo para leer, imprimir o llevar al médico. Cuando lleguen exámenes nuevos, pide "el informe actualizado": compara contra el anterior y lidera con lo que cambió.

Los datos de cada persona viven en su Proyecto (o en `local/personas/` si se usa en Claude Code) — nunca en este repo.

## Qué NO hace

No diagnostica, no reemplaza la consulta médica, no dosifica medicamentos, no extrapola más allá de los documentos.
