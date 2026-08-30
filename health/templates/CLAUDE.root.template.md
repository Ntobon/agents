# Contexto para Claude — carpeta "<Nombre de la carpeta de salud>"

Carpeta raíz de toda la documentación de salud de la familia de **<dueño de la carpeta>** (<correo>): documentos médicos propios y de los familiares que se listan abajo. Todo vive en Google Drive (`<ruta>`).

## Jerarquía de contexto

**Este archivo es la única fuente de las políticas generales y las convenciones documentales.** Los `CLAUDE.md` de las subcarpetas NO las repiten: contienen solo lo específico de esa persona y remiten aquí. Al trabajar en cualquier subcarpeta se leen ambos. Si una regla nueva aplica a todos, se agrega aquí — nunca se copia en varios archivos.

**Memoria:** antes de trabajar, leer `MEMORY.md` (hechos duraderos). Cada subcarpeta tiene el suyo. Hechos nuevos se registran con fecha en el que corresponda.
**Tareas:** pendientes en `TAREAS.md` (transversales) y en el de cada subcarpeta; al cerrar, mover a "Hechas". Los pendientes clínicos de cada paciente viven en su `00 Índice general.md`.

## Quién es quién

| Carpeta | Persona | Documentación |
| --- | --- | --- |
| `<Carpeta1>\` | <Nombre, documento de identidad, fecha de nacimiento, relación> | <estado del archivo> |
| … | … | … |

<Datos comunes: dónde viven los pacientes, EPS/aseguradora y plan de cada uno.>

## Políticas generales (aplican en TODA la carpeta)

1. **No inventar datos clínicos.** Todo valor, fecha o dosis sale de un documento real; si no está, se dice.
2. **Citar la fuente** (archivo y fecha) de cada dato clínico usado.
3. **Lenguaje llano** en los documentos dirigidos a la familia, calibrado a la edad de cada lector.
4. **Privacidad.** Nada se publica ni se comparte sin que el dueño lo pida explícitamente.
5. **Los originales no se tocan.** `06 - Originales\` conserva los crudos tal como llegaron.
6. **Descargo permanente:** todo documento generado es informativo; no reemplaza al médico tratante.
7. **Criterio de etapa de vida:** equilibrar prevención con evitar estudios innecesarios según la edad; los informes incluyen "lo que probablemente NO necesita".
8. **Pensamiento crítico, no notaría:** toda decisión clínica nueva se investiga (guías, evidencia) y se contrasta antes de asentarla; si el análisis contradice lo pedido, se dice con argumentos; segunda opinión cuando el caso lo amerite; toda decisión se registra con su análisis y sus criterios de revisión.
9. **Informes de salud** con la skill `personal-health-report` (o equivalente); el entregable es el PDF; la fuente se conserva para regenerar.
10. **Sincronización local ↔ nube:** la nube es la fuente de verdad ante la duda; duplicados `(1)` son choques de nombres — conservar el más nuevo con nombre canónico; todo documento que llegue por chat/correo se archiva según el patrón, nunca queda suelto; al cerrar una sesión con cambios relevantes, dejar el delta escrito.
11. **Reportes y tableros HTML se archivan** en la carpeta del paciente, además de publicarse: vivos con nombre canónico (actualizar archivo → republicar a la misma URL); puntuales con fecha `AAAA-MM-DD`.
12. **Documentos firmados NUNCA circulan como transcripción:** valen por papel y firma; se procesan con la herramienta de escaneo de la skill `medical-record-package` y circula el escaneo. La transcripción `.md` es solo índice interno.
13. **Los planes de la familia no contaminan la historia clínica:** los documentos clínicos (carpetas 02-05, paquetes) llevan solo hechos; estrategias y logística viven en CLAUDE/MEMORY/TAREAS/índices/registros de gestión.
14. **Separación agente / contexto:** skills, plantillas y rutinas son agnósticas y replicables; todo dato personal vive en los archivos de contexto. La skill `archive-audit` lo vigila.

## Convenciones del patrón documental

Cada carpeta de paciente:

```
<Carpeta del paciente>\
├── CLAUDE.md · MEMORY.md · TAREAS.md    Contexto, memoria y tareas del paciente
├── 00 Índice general.md                 Índice + línea de tiempo + pendientes clínicos
├── 01 - Informe de salud\               Informes en lenguaje llano + paquetes médicos
├── 02 - Historia clínica\               Valoraciones, notas de consulta, epicrisis
├── 03 - Laboratorios\                   Resultados + 00 Tendencia de laboratorios.md
├── 04 - Imágenes diagnósticas\          Informes + subcarpetas de imágenes
├── 05 - Órdenes y remisiones\           Órdenes con su estado + registro de gestiones
└── 06 - Originales\<año>\               Crudos tal como llegaron. No tocar.
```

- Las carpetas 01-06 existen siempre; las vacías llevan `00 Sin documentos aún.md`.
- Nombres: `AAAA-MM-DD Descripción.ext` con la fecha de toma/atención. Prefijo `00` para archivos meta.
- PDF + transcripción `.md` al lado; documentos compuestos en subcarpeta `- cortes`/`- imágenes`.
- Transcripciones: encabezado (paciente, sede, fechas, origen) → tablas con referencia y estado → "Lectura rápida" en lenguaje llano.
- Marcas: ✅ normal/cumplido · ⚠️ fuera de rango/pendiente · ▼▲ dirección del cambio.

### Al agregar un documento nuevo

1. Crudo a `06 - Originales\<año>\`.
2. Copia renombrada a la carpeta 01-05 correspondiente; transcripción si es examen.
3. Actualizar la tendencia de laboratorios si trae valores.
4. Actualizar línea de tiempo y pendientes del índice.
5. Si cierra un pendiente, retirarlo.
