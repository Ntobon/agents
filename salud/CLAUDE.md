# Salud — informes de salud por persona

Agente para generar informes de salud personalizados (PDF en español) para cada miembro de la familia, a partir de exámenes de laboratorio y contexto médico. El corazón es el skill `personal-health-report`.

**Arquitectura de tres capas**: el motor (este plugin, 100% agnóstico) / la instancia (los espacios por persona, ver abajo) / los datos (los exámenes e informes de cada persona — NUNCA en este repo).

## Cómo se organiza la instancia (los datos de cada quien)

Dos modos equivalentes — el skill detecta el contexto solo, sin interrogar al usuario:

1. **Proyectos de Claude por persona** (web/celular, recomendado): un Proyecto por familiar ("Salud Papá", "Mi salud"), con sus PDFs de laboratorio e informes previos como archivos del proyecto y su descripción en las instrucciones del proyecto.
2. **Carpeta local por persona** (Claude Code): `local/personas/<nombre>/` con los exámenes e informes previos. `local/` está gitignored — jamás se versiona ni se comparte.

## Reglas del agente

- El informe es para el **paciente**, no para quien lo pide: tono y tratamiento según edad (ver el skill).
- Nunca inventar valores; citar cifras y fechas de los documentos.
- Un solo disclaimer por informe; no diluir el contenido con advertencias repetidas.
- El entregable es el **PDF**; el .docx se conserva solo como fuente de regeneración.
- Preguntas rápidas sobre un examen → responder inline, sin generar informe.

## Skills

| Skill | Cuándo |
|---|---|
| `personal-health-report` | "informe de salud", "analiza estos exámenes para [persona]", "genera el informe actualizado" |
