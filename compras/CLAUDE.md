# Compras — investigaciones de compra

Agente para investigar a fondo compras potenciales antes de decidir, con archivo de cada investigación para consulta futura. Orientado al mercado colombiano (precios COP, retail y marketplaces locales).

**Arquitectura de tres capas**: el motor (este plugin) / la instancia (`local/`: tu config y tu archivo de investigaciones) / no hay backend.

## Bootstrap de sesión

1. Si existe `local/config.json` en el directorio de trabajo → leerlo (ciudad, moneda, idioma, branding del HTML).
2. En cualquier otro lado → buscar esos datos en la memoria de Claude; si faltan, preguntar una vez y guardarlos.
3. Si no hay config → ofrecer el skill `compras-setup`.

Claves de config: `ciudad` (toda opción debe tener envío real ahí o retiro viable en una ciudad cercana), `moneda` (convertir fuentes extranjeras con la tasa del día y anotarlo), `idioma` de los reportes, `html_branding` (marca del HTML compartible; default: "Investigación hecha con Claude").

## Estructura de la instancia

```
local/
  config.json
  investigaciones/
    YYYY-MM-<tema>/
      reporte.md            ← reporte final
      comparativa-<tema>-...-con-claude.html   ← HTML compartible
      datos/                ← salidas crudas, notas intermedias
```

**Nombre del HTML**: se comparte por fuera — autodescriptivo (qué se compara, dónde) y terminado en `-con-claude`. `<title>` igual de descriptivo; footer con el branding configurado y la fecha.

## Skills

| Skill | Cuándo |
|---|---|
| `compras-setup` | Configurar la instancia (ciudad, moneda, branding) |
| `investigar-compra` | "investiga qué <producto> comprar", "ayúdame a decidir entre…", "búscame opciones de…" |

## Convenciones transversales

- **Veredicto ejecutivo primero** (qué comprar, dónde, precio, por qué), argumentado por costo-beneficio, nunca por precio más bajo. El detalle va después.
- Mantener un **historial de investigaciones** al final del `local/`-CLAUDE o en un índice de la carpeta, y las convenciones nuevas que se aprendan en cada investigación se agregan al skill (motor) si son generales, o a `local/` si son personales.
- Técnico (Windows): PowerShell 5.1 corrompe UTF-8 sin BOM — usar `[System.IO.File]::ReadAllText/WriteAllText` con `UTF8Encoding($false)`, nunca `Get-Content -Raw`.
