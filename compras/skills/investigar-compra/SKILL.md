---
name: investigar-compra
description: Investigar a fondo una compra potencial en el mercado colombiano y entregar reporte con veredicto ejecutivo más comparativa HTML compartible. Use este skill cuando el usuario diga "investiga qué <producto> comprar", "ayúdame a decidir entre", "búscame opciones de", "compárame <productos>", "qué <producto> me recomiendas", o cualquier variante de querer investigar una compra antes de decidir.
---

# Investigar compra

Investigación completa de una compra potencial: búsqueda multi-enfoque, verificación real de precios y disponibilidad, matriz de valor ponderada y entregables archivables.

## Bootstrap
Resolver la config (ciudad, moneda, idioma, `html_branding`) según el CLAUDE.md del agente: `local/config.json` si existe; si no, memoria de Claude; si falta todo, ofrecer `compras-setup`. Las opciones que no tengan envío real a la ciudad del usuario (o retiro viable en una ciudad cercana justificable) **no sirven** — descartarlas temprano.

## Proceso estándar

### 1. Brief
Capturar: qué quiere el usuario, presupuesto (si lo hay), casos de uso, restricciones, y para quién es (los criterios cambian — ver `references/`).

### 2. Búsqueda multi-enfoque
Workflow de ~5 agentes con ángulos distintos: marketplace, tiendas oficiales de marca, retail grande, especialistas, comunidad/reviews, y (si aplica) el caso de uso específico. Cada agente devuelve opciones estructuradas: nombre, specs clave, precio en la moneda local, tienda, URL, disponibilidad de envío. (Patrón probado: ~50 opciones en ~23 min.)

### 3. Verificación con browser (obligatoria para finalistas)
No confiar en resultados de búsqueda — suelen estar desactualizados. Verificar en el navegador: precio real, stock, envío a la ciudad del usuario. Marcar cada finalista como "verificado DD-MM-AAAA" en reporte y HTML (los descuentos colombianos del 25-40% vencen rápido).

### 4. Matriz de valor
Tabla comparativa con specs relevantes al caso de uso, precio y puntaje ponderado según el brief. Incluir una vista de eficiencia (puntaje ÷ precio, "puntos por millón") — suele revelar que las gamas medias ganan en valor. La **posventa pondera explícito (~15%)** cuando el usuario vive fuera de las ciudades grandes.

### 5. Entregables
- `reporte.md`: **veredicto ejecutivo primero** (qué comprar, dónde, precio, por qué — argumentado por costo-beneficio, nunca solo por precio), luego hallazgos, matriz y advertencias.
- `comparativa-<tema>-...-con-claude.html`: usable y responsive — tablas comparativas solo en desktop (≥900px); en móvil, cartas con toda la información de la fila; filtros en ambos modos y selector de orden en móvil. Branding según config (si el skill de artefactos de la casa está disponible, usarlo).
- Guardar todo en `local/investigaciones/YYYY-MM-<tema>/` (con `datos/` para salidas crudas).

## Convenciones de búsqueda y verificación (aprendidas en casos reales)

- **El mismo producto varía fuerte de precio por canal.** Comparar siempre: tienda oficial de marca vs retail grande (Éxito, Alkosto, Falabella, Ktronix) vs Mercado Libre vs especialistas. Caso real: un mismo celular $424.000 más barato en retail que en la tienda de la marca. El retail grande además resuelve envío/garantía/retiro.
- **Cobertura local del retail**: verificar qué cadenas tienen tienda física en la ciudad del usuario — varía en ciudades intermedias, y la garantía presencial puede justificar un sobreprecio moderado (~$150.000) o no.
- **Mercado Libre bloquea la verificación automatizada** (muro anti-bot). Sus precios llegan de snippets indexados: tratarlos como aproximados, abrir la publicación manualmente antes de decidir, y preferir vendedores MercadoLíder con facturación.
- **Los agentes de búsqueda se equivocan en specs clave.** Caso real: reportaban un procesador/IP rating/parlantes que no correspondían a la variante vendida en Colombia. En la verificación de finalistas confirmar procesador, RAM de la variante exacta y detalles decisivos en la ficha de la tienda + una review reciente — el veredicto puede cambiar.
- **Señal de alerta posventa**: dominio oficial de la marca muerto o secuestrado en Colombia (caso real: el dominio local de una marca de patinetas redirigía a un sitio de apuestas). Sin distribuidor vivo no hay repuestos — revisar el dominio local de cada marca antes de recomendarla.
- **Autonomía/rendimiento real ≈ 50-60% del catálogo** en productos con batería (las cifras oficiales son de banco de pruebas); en condiciones exigentes, descontar más. Ver `references/criterios-terreno-mixto.md`.
- **Normativa**: cuando aplique (movilidad, drones, etc.), anotar los límites legales colombianos (ej. >25 km/h excede la micromovilidad en vía pública — Ley VELMPU).

## Criterios por perfil (references/)

- Compra para **adulto mayor** (tecnología): leer `references/criterios-adulto-mayor.md` antes de armar la matriz.
- Producto para **terreno mixto / exteriores**: leer `references/criterios-terreno-mixto.md`.

Estos archivos crecen: cuando una investigación produzca criterios reutilizables para un perfil nuevo, agregarlos como referencia nueva.

## Error handling
- **Config not found**: ofrecer `compras-setup`.
- **Producto sin oferta local**: decirlo claro y evaluar importación solo si el usuario lo pide (impuestos + garantía).
- **Precios inconsistentes entre fuentes**: gana el verificado en browser con fecha.
