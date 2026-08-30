# Agent Builder — fábrica e índice de agentes

Esta carpeta es el repo `Ntobon/agents`: el índice de mis agentes de Claude y el lugar donde se construyen y empaquetan los nuevos.

**Al trabajar aquí, la fuente de verdad del oficio es [METODOLOGIA.md](METODOLOGIA.md).** Toda creación, conversión o empaquetado de un agente sigue esa metodología: arquitectura de tres capas (motor compartible / instancia en `local/` / datos en el backend del usuario), plugin atado al repositorio con Sync automatically, onboarding sin comandos, y el checklist del §10.

Reglas de esta carpeta:
- Los agentes **livianos** (solo CLAUDE.md + skills) viven aquí como subcarpetas y se registran en `.claude-plugin/marketplace.json` (`source: "./<carpeta>"`). Los de **setup profundo** (backend propio) viven en su repo y solo se catalogan en el README.
- Nunca meter datos personales en el motor de un agente: van en `local/` (gitignored) o en el backend del usuario.
- Todo agente nuevo parte de `plantilla/`.
- Al terminar cualquier cambio: commit + push (identidad Ntobon / nicolastoboncastano@gmail.com — ya configurada local al repo), y actualizar el catálogo del README si cambió la lista de agentes.
- Referencia viva del patrón completo: el repo [Ntobon/agentic-finance-tracker](https://github.com/Ntobon/agentic-finance-tracker) (primer agente convertido; copia de trabajo en `E:\Claude\Finance`).
