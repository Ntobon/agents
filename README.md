# Agents — índice y fábrica de agentes

Catálogo de mis agentes de Claude, la [metodología](METODOLOGIA.md) para construirlos y compartirlos, y la [plantilla](plantilla/) para arrancar uno nuevo. Este repo es además un **marketplace de plugins**: los agentes livianos viven aquí como subcarpetas; los que tienen setup profundo viven en su propio repo y este índice los referencia.

## Catálogo

| Agente | Qué hace | Dónde vive | Estado |
|---|---|---|---|
| **finance-tracker** | Finanzas personales sobre Supabase: gastos en lenguaje natural, pagos recurrentes, extractos, reportes | [Ntobon/agentic-finance-tracker](https://github.com/Ntobon/agentic-finance-tracker) (repo propio — backend y provisioning profundo) | ✅ Empaquetado y en producción |
| **compras** | Investigaciones de compra: búsqueda multi-enfoque, verificación real, matriz de valor, comparativa HTML | [`compras/`](compras/) en este repo | ✅ Empaquetado |
| **salud** | Informes de salud personalizados (PDF) por miembro de la familia, adaptados por edad y contexto EPS | [`salud/`](salud/) en este repo | ✅ Empaquetado |

## Instalar un agente

Cada agente se instala como **plugin sincronizado con su repositorio** — se actualiza solo con cada push. Para personas no técnicas: abrir la carpeta del agente en Claude y decir **"quiero instalarlo"**; el skill de setup guía todo sin comandos. El detalle por superficie (claude.ai / Claude Code) está en [METODOLOGIA.md §4](METODOLOGIA.md).

Para instalar los agentes de ESTE repo:
- claude.ai: Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → Add.
- Claude Code: `claude plugin marketplace add Ntobon/agents` y luego `claude plugin install <agente>@ntobon-agents`.

## Compartir un agente

Invitar a la persona al repo correspondiente (o hacerlo público). Los repos no contienen nada personal — arquitectura de tres capas: motor compartible / instancia local gitignored / datos en el backend de cada quien. Ver [METODOLOGIA.md §2 y §5](METODOLOGIA.md).

## Crear un agente nuevo

1. Copiar `plantilla/` (como subcarpeta aquí si es liviano, o como repo propio si tendrá backend — criterios en [METODOLOGIA.md §9](METODOLOGIA.md)).
2. Seguir el checklist de [METODOLOGIA.md §10](METODOLOGIA.md).
3. Registrarlo en el catálogo de este README y, si vive aquí, en `.claude-plugin/marketplace.json`.
