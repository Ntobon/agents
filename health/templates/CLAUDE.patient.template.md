# Contexto para Claude — carpeta "<Nombre>" (<nombre completo>)

Documentación médica de **<nombre completo>**, <relación con el dueño de la carpeta>. Sigue el patrón documental de la familia — estructura, políticas y convenciones están en [../CLAUDE.md](../CLAUDE.md) y **no se repiten aquí**: este archivo es solo lo específico de esta persona.

**Punto de entrada clínico:** `00 Índice general.md` (índice, línea de tiempo, pendientes — fuente de verdad). **Memoria:** `MEMORY.md`. **Tareas de archivo/administrativas:** `TAREAS.md`.

## Datos

- <Nombre completo, documento de identidad, fecha de nacimiento (edad)>.
- <Dirección, teléfono, correo>.
- <EPS/aseguradora, plan, número de contrato, historia clínica, ciudad de atención>.
- <Talla; dónde vive la serie de peso si se lleva>.

## Cuadro clínico en una frase

<Una frase honesta y completa del estado actual, con los hallazgos mayores fechados. Se actualiza con cada hecho clínico relevante.>

## Diagnósticos activos

| Diagnóstico | CIE-10 | Estado |
| --- | --- | --- |
| <…> | <…> | <…> |

## Medicación actual

| Medicamento | Dosis | Frecuencia |
| --- | --- | --- |
| <…> | <…> | <…> |

## Médicos tratantes

- **<Dr./Dra. nombre>** — <especialidad, institución, registro>. <Qué papel juega en el caso.>

## Reglas específicas de este paciente

(Las políticas generales están en `..\CLAUDE.md` — aquí solo lo propio.)

1. **Cómo se le escribe:** <edad, tono, tratamiento (usted/tú), nivel de detalle>.
2. **Línea de comunicación:** <qué sabe el paciente, qué tono acordó la familia con el tratante, desde cuándo>.
3. <Frente clínico abierto más urgente y su estado.>
4. <Prioridades permanentes (p. ej. prevención de caídas).>

## Monitoreo de canales

(Opcional — solo si se quiere que la skill `channel-monitoring` haga rondas por los canales de este paciente. Sin esta sección, la skill no corre.)

- **Navegador:** <cuál usar y cómo reconocerlo>
- **Buzón:** <cuenta> · remitentes pertinentes: <lista> · palabras clave: <lista>
- **Portal de la aseguradora:** <URL base y secciones> · ingreso: lo hace <quién> (nunca el agente)
- **Otros portales:** <URL> · qué se consulta
- **Autorizaciones permanentes del titular:** <descargar adjuntos de los remitentes listados: sí/no> · <enviar el formulario de consulta de tal portal con el documento del paciente: sí/no>
- **Dominios a los que se puede seguir un enlace:** <lista>
- **Carpeta legal:** <ruta, si existe>
- **A quién se avisa:** <canal de notificación>

## Particularidades de archivo

- <Lo que un futuro lector debe saber del estado del archivo de esta carpeta: qué falta, qué formatos, decisiones de organización.>
