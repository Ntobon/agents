# Metodología: agentes personales empaquetados como plugins

Destilado de la conversión del **finance-tracker** (agosto 2026) en un agente autocontenido, compartible y auto-actualizable. Esta es la forma canónica de construir, empaquetar y compartir mis agentes de Claude.

## 1. Qué es un agente aquí

Un agente = **una carpeta que es un repo git y un plugin de Claude a la vez**:

- Un `CLAUDE.md` que orquesta (contexto, reglas, catálogo de skills, bootstrap).
- Skills en `skills/` que encapsulan cada actividad.
- Manifiestos de plugin en `.claude-plugin/` para que se instale y actualice desde el repo.
- Un `setup/` con lo necesario para autoprovisionarse (esquemas, scripts).
- Una capa `local/` (gitignored) con lo personal de cada instalación.

## 2. Arquitectura de tres capas (la regla de oro)

| Capa | Qué es | Dónde vive | ¿Se comparte? |
|---|---|---|---|
| **El motor** | Skills, CLAUDE.md, esquema, docs | El repo (todo menos `local/`) | ✅ 100% agnóstico, sin datos personales |
| **La instancia** | Config de esa instalación (IDs de proyectos, emails, exports) | `local/` (gitignored) | ❌ Nunca |
| **Los datos** | Los datos del usuario y sus reglas personales | Su backend (p. ej. su proyecto Supabase, campo `system_prompt`) | ❌ Cada usuario provisiona el suyo |

**Nada personal fuera de `local/` y del backend.** Si un skill necesita un dato personal (mapeos, reglas, preferencias), ese dato vive en la configuración del usuario (DB o `local/`), jamás hardcodeado en el skill. Así el motor se comparte y actualiza sin arrastrar información de nadie.

## 3. Estructura estándar del repo de un agente

```
mi-agente/
├── CLAUDE.md                  → orquestador (ver §7)
├── README.md                  → qué es, instalación sin comandos, ciclo de actualización
├── config.example.json        → plantilla de la config local
├── .gitignore                 → local/ y dist/
├── .claude-plugin/
│   ├── plugin.json            → { name, description, version, author }
│   └── marketplace.json       → { name, owner, plugins: [{ name, source: "./" }] }
├── skills/
│   ├── <agente>-setup/        → onboarding guiado sin comandos (ver §6)
│   └── <actividad>/SKILL.md   → un skill por actividad
├── setup/
│   ├── schema.sql             → si hay DB: esquema completo para autoprovisionar
│   └── package-skills.ps1     → empaqueta zips (solo como alternativa congelada)
└── local/                     → capa personal, NUNCA en git
    └── config.json
```

## 4. Distribución: plugin atado al repositorio

Dos modos posibles; **el estándar es el segundo**:

1. **Zip (Upload plugin)**: se sube una vez, queda congelado, sin actualizaciones. Solo para casos puntuales.
2. **Atado al repositorio** ✅: el plugin se asocia al repo de GitHub con sincronización automática — cada push actualiza los skills en todas las instalaciones.

Instalación por superficie (flujo verificado en vivo):

| Superficie | Cómo | Actualización tras un push |
|---|---|---|
| **claude.ai** (cubre web **y celular**) | Customize → Plugins → Add → Add marketplace → *Add from a repository* → elegir repo → activar **Sync automatically** → Sync → pestaña Browse → **Add** | Automática |
| **Claude Code** | `claude plugin marketplace add <owner>/<repo>` + `claude plugin install <plugin>@<marketplace>` | `claude plugin update <plugin>` (o `git pull` si el marketplace es carpeta local) |

Gotchas conocidos:
- Repo privado en claude.ai → sale **"Repository not accessible"**: el usuario hace clic en **"Install the Claude GitHub App"** y le da acceso al repo (Only select repositories). Ese clic siempre es del usuario.
- Al instalar el plugin en claude.ai, los skills de cuenta homónimos quedan reemplazados; borrar manualmente los que sobren (Customize → Skills → ⋮ → Remove).
- El dueño mantiene con: editar → commit → push. Nada más.

## 5. Compartir

- **La unidad de compartición es el repo**: dar el agente a alguien = invitarlo como colaborador (repo privado) o hacer el repo público.
- El repo no contiene nada personal (capa 1), así que compartirlo no expone nada.
- Cada persona provisiona su propio backend con el skill de setup; los datos nunca se cruzan.

## 6. Onboarding sin comandos (patrón del skill `*-setup`)

La instalación está diseñada para personas **no técnicas**. Principio rector del skill de setup:

> El usuario NO ejecuta comandos ni edita archivos. Todo lo ejecutable lo ejecuta Claude. Al usuario solo se le piden los clics que requieren su identidad (crear cuentas, iniciar sesión, autorizar), guiado paso a paso y esperando confirmación en cada uno.

Estructura del skill de setup:
1. **Fase 0 — Diagnóstico silencioso**: detectar qué falta (config local, plugin, conectores, cuentas) y saltar lo ya cumplido. Idempotente.
2. **Cuentas** (GitHub, backend): guiar a crearlas con enlaces y pasos simples. **Claude nunca pide ni escribe contraseñas.**
3. **Acceso al repo**: el usuario pasa su username al dueño → invitación → aceptar.
4. **Plugin**: Claude ejecuta los comandos (Claude Code) o hace los clics (claude.ai) — ver §4.
5. **Backend**: Claude crea el proyecto, aplica `setup/schema.sql` como migración, siembra defaults, crea el usuario, escribe `local/config.json`. Solo pregunta lo humano (nombre, email, moneda…).
6. **Verificar y estrenar**: una llamada de verificación + un primer uso de ejemplo.

**Modalidad navegador asistido**: cuando hay navegador disponible, Claude abre las páginas y hace los clics él mismo, y **le entrega el control al usuario** exactamente en los pasos de login/autorización. Si el usuario se pierde, pedirle captura de pantalla y guiarlo sobre lo que ve.

## 7. El CLAUDE.md del agente

Debe declarar:
- Qué es el agente y qué NO es (legados eliminados, fuentes canónicas).
- La arquitectura de tres capas y la regla de "nada personal fuera de local/ y el backend".
- **Bootstrap de sesión multi-superficie** (crítico para que funcione igual en carpeta, plugin, web y celular):
  1. Si existe `local/config.json` en el directorio de trabajo → usarlo.
  2. En cualquier otro lado (claude.ai, celular, Claude Code vía plugin en otra carpeta) → memoria de Claude; si falta, preguntar una vez y guardar.
- Catálogo de skills (tabla actividad → skill).
- Convenciones (formatos, confirmaciones, dónde van los archivos generados).

## 8. Personalización sin tocar el motor

Las reglas personales del usuario viven en SU configuración (p. ej. campo `system_prompt` en su DB, cargado por todos los skills en el bootstrap). Ejemplos: mapeos de comercios, idioma, reglas de categorización. Un skill del agente (`*-settings`) las administra. El motor nunca cambia por preferencias de una persona.

## 9. ¿Repo propio o repo índice? (criterios de decisión)

Un marketplace puede contener **varios plugins** (subcarpetas, `source: "./<carpeta>"`), así que hay dos ubicaciones posibles para un agente:

**Repo propio** cuando cumple alguna:
- Setup profundo: backend propio, esquema, provisioning (ej: finance-tracker con Supabase).
- Audiencia/privacidad distinta: el acceso se otorga por repo — si comparto el repo comparto TODO lo que hay en él.
- Cadencia de cambios propia o riesgo alto (un push en un mono-repo actualiza todos los plugins de todos los instalados).

**Dentro del repo índice (`Ntobon/agents`)** cuando:
- Es liviano: solo CLAUDE.md + skills, sin backend propio.
- Comparte audiencia con los demás agentes del índice.
- Cambia poco o su blast radius es bajo.

El repo índice siempre cumple además el rol de **catálogo**: lista todos los agentes (vivan donde vivan) con su enlace e instalación.

## 10. Checklist: convertir un agente existente a este formato

- [ ] Auditar la carpeta actual: separar motor / instancia / datos.
- [ ] Sacar TODO lo personal de skills y CLAUDE.md → moverlo a `local/` o al backend (`system_prompt`).
- [ ] Si hay DB: extraer el esquema real (tablas, funciones, índices, constraints) a `setup/schema.sql` autocontenido.
- [ ] Reescribir el bootstrap de cada skill al patrón multi-superficie (§7).
- [ ] Eliminar dependencias muertas (sincronizadores viejos, servicios abandonados) del código Y de las cuentas.
- [ ] Crear `.claude-plugin/plugin.json` + `marketplace.json` (o registrar la subcarpeta en el marketplace del índice).
- [ ] Escribir el skill `*-setup` de onboarding sin comandos (§6).
- [ ] README con instalación, capas y ciclo de actualización.
- [ ] `.gitignore`: `local/`, `dist/`.
- [ ] git init/commit con identidad personal (`Ntobon` / gmail) → push.
- [ ] Instalar el plugin en claude.ai (Sync automatically) y en Claude Code; borrar skills de cuenta viejos que dupliquen.
- [ ] Registrar el agente en el catálogo del repo índice.
