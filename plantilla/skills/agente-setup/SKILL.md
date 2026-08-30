---
name: <agente>-setup
description: Guided zero-command onboarding for <agente> — walks a non-technical person through accounts, plugin install tied to the repository, backend provisioning, and local config. Use when the user says "quiero instalarlo", "instalar", "setup inicial", or when another skill of this agent can't find its configuration.
---

# <Agente> Setup — onboarding guiado (cero comandos para el usuario)

## Principio rector
**El usuario NO ejecuta comandos ni edita archivos.** Todo lo ejecutable lo ejecuta Claude. Al usuario solo se le piden los clics que requieren su identidad (crear cuentas, iniciar sesión, autorizar), guiado paso a paso, esperando confirmación en cada uno. Claude **nunca** pide ni escribe contraseñas. Si hay navegador disponible, Claude puede hacer los clics él mismo y entregarle el control al usuario en los pasos de login/autorización; si el usuario se pierde, pedirle una captura y guiarlo sobre lo que ve.

**Idempotente**: en la Fase 0 detectar qué ya está hecho y saltarlo.

## Fase 0 — Diagnóstico (silencioso)
- ¿Existe `local/config.json` y el backend responde? → ya instalado; mostrar config y salir.
- ¿Plugin instalado? ¿Conectores necesarios conectados? ¿Cuentas creadas?
- Presentar el mapa: "Vamos a hacer N cosas: … Te guío en cada una."

## Fase 1 — Cuentas y acceso al repo
1. ¿Tiene cuenta de GitHub? Si no → guiar a crearla (github.com/signup).
2. Pedir su username → el dueño lo invita al repo → aceptar la invitación.

## Fase 2 — Instalar el plugin atado al repo
- **Claude Code** (Claude ejecuta): `claude plugin marketplace add <owner>/<repo>` + `claude plugin install <plugin>@<marketplace>`.
- **claude.ai** (cubre web y celular): Customize → Plugins → Add → Add marketplace → *Add from a repository* → elegir el repo → activar **Sync automatically** → Sync → Browse → **Add**. Si sale "Repository not accessible" → "Install the Claude GitHub App" (clic del usuario).

## Fase 3 — Backend y conectores
<Guiar la creación de la cuenta del backend y la conexión del conector en Claude. Claude verifica con una llamada de listado.>

## Fase 4 — Provisionar (Claude hace todo)
<Crear el proyecto/recurso, aplicar `setup/schema.sql` como migración, sembrar defaults, crear el usuario. Preguntar solo lo humano.> Al final, escribir `local/config.json` (explicar que `local/` es privada y nunca se comparte).

## Fase 5 — Verificar y estrenar
<Llamada de verificación + primer uso de ejemplo.>

## Error handling
- Conector no conectado → volver a la fase correspondiente; no continuar sin él.
- Instalación del plugin falla por permisos → revisar la invitación al repo / el GitHub App.
- Provisioning falla a medias → inspeccionar qué quedó creado y continuar por partes.
- El usuario se pierde en un paso web → pedir captura y guiar sobre lo que ve.
