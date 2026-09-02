# Contexto para Claude — carpeta "Papá" (Jorge Restrepo Vélez)

> **PACIENTE FICTICIO** de la familia de ejemplo. Nada de lo que hay aquí corresponde a una persona real.

Documentación médica de **Jorge Restrepo Vélez**, padre de Camila (la dueña de la carpeta). Sigue el patrón documental de la familia — estructura, políticas y convenciones están en [../CLAUDE.md](../CLAUDE.md) y **no se repiten aquí**: este archivo es solo lo específico de esta persona.

**Punto de entrada clínico:** `00 Índice general.md` (índice, línea de tiempo, pendientes — fuente de verdad). **Memoria:** `MEMORY.md`. **Tareas de archivo/administrativas:** `TAREAS.md`.

## Datos

- Jorge Restrepo Vélez, CC 00.000.001 (ficticia), nacido 12-mar-1955 (71 años).
- Vive en Medellín, barrio Laureles (dirección ficticia). Teléfono: <pendiente>.
- EPS Ejemplo, plan básico. Atención en IPS Demo Salud (medicina interna). Historia clínica HC-26-4410.
- Talla 1,72 m. Peso: no se lleva serie aún.

## Cuadro clínico en una frase

Diabetes tipo 2 e hipertensión en mejoría con el tratamiento actual (HbA1c 7,4 % en nov-2025 → 6,9 % en may-2026), con LDL todavía por encima de la meta (104 mg/dL) y un ascenso leve de creatinina (1,1 → 1,2 mg/dL) por el que su médica ordenó una ecografía renal el 28-may-2026.

## Diagnósticos activos

| Diagnóstico | CIE-10 | Estado |
| --- | --- | --- |
| Diabetes mellitus tipo 2 sin complicaciones | E11.9 | En control, HbA1c 6,9 % (20-may-2026) |
| Hipertensión esencial | I10 | Controlada, 134/82 en consulta (28-may-2026) |
| Hiperlipidemia | E78.5 | LDL 104 mg/dL, meta < 100; dosis de estatina aumentada el 28-may-2026 |

## Medicación actual

| Medicamento | Dosis | Frecuencia |
| --- | --- | --- |
| Metformina | 850 mg | Cada 12 h |
| Losartán | 50 mg | 1 al día |
| Atorvastatina | 40 mg | 1 en la noche (subió de 20 mg el 28-may-2026) |

## Médicos tratantes

- **Dra. Ejemplo Pérez** — medicina interna, IPS Demo Salud (registro ficticio 00000). Lleva el control de la diabetes y la hipertensión; ordenó la ecografía renal.

## Reglas específicas de este paciente

(Las políticas generales están en `..\CLAUDE.md` — aquí solo lo propio.)

1. **Cómo se le escribe:** tiene 71 años; tratamiento de usted, frases cortas, sin siglas sin explicar, letra grande en lo impreso.
2. **Línea de comunicación:** él conoce sus diagnósticos y sus resultados; no hay nada que la familia le oculte.
3. **Frente clínico abierto:** ecografía renal ordenada el 28-may-2026 por el ascenso de creatinina — pendiente de realizar y archivar.
4. **Prioridad permanente:** control trimestral de HbA1c, creatinina y perfil lipídico mientras dure el ajuste de tratamiento.

## Particularidades de archivo

- Los cuatro documentos que existen llegaron como PDF y están transcritos. Falta el informe de salud en lenguaje llano (carpeta 01) — es uno de los casos de uso de la demo.
- La orden médica del 28-may-2026 es un documento firmado: si hay que circularla, va como escaneo, nunca como transcripción (política 12).
