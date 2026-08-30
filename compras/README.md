# Compras

Agente de investigaciones de compra para el mercado colombiano: investiga a fondo una compra potencial (búsqueda multi-enfoque con ~5 agentes, verificación real de precios/stock/envío en el navegador, matriz de valor ponderada) y entrega un reporte con **veredicto ejecutivo** más una **comparativa HTML compartible**. Cada investigación queda archivada para consulta futura.

## Instalación

Agente liviano (sin backend). Se instala desde el marketplace `Ntobon/agents`:
- **claude.ai** (web + celular): Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → Add.
- **Claude Code**: `claude plugin marketplace add Ntobon/agents` + `claude plugin install compras@ntobon-agents`.

Luego di **"configura el agente de compras"** (30 segundos: ciudad, moneda, branding) y estrena con *"investiga qué [producto] comprar"*.

## Las tres capas

| Capa | Dónde vive | ¿Se comparte? |
|---|---|---|
| El motor (proceso, convenciones, criterios por perfil) | Este plugin | ✅ |
| Tu instancia (`local/config.json` + `local/investigaciones/`) | Tu carpeta / tu memoria de Claude | ❌ |

## Qué sabe hacer

| Pides | Resultado |
|---|---|
| "investiga qué patineta eléctrica comprar" | Reporte completo + comparativa HTML, con precios verificados con fecha |
| "ayúdame a decidir entre X y Y" | Matriz de valor ponderada al caso de uso |
| "es para mi papá de 80 años" | Aplica criterios especializados por perfil (references/) |
