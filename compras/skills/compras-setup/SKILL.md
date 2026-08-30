---
name: compras-setup
description: Configurar una instancia nueva del agente de compras (ciudad, moneda, idioma, branding del HTML y carpeta de investigaciones). Use cuando el usuario diga "quiero instalarlo", "configura el agente de compras", "setup de compras", o cuando investigar-compra no encuentre la configuración.
---

# Compras Setup

Onboarding liviano — este agente no tiene backend. **El usuario no ejecuta comandos**: Claude pregunta y escribe todo.

**Idempotente**: si la config ya existe y está completa, mostrarla y salir.

## Pasos

1. Preguntar (una sola tanda, en lenguaje simple):
   - ¿En qué ciudad estás? (las opciones deben tener envío real ahí)
   - ¿Moneda de los precios? (default: COP)
   - ¿Idioma de los reportes? (default: español)
   - ¿Quieres una marca/branding en los HTML que se comparten? (default: "Investigación hecha con Claude")
2. Escribir la config:
   - **Con carpeta de trabajo** (Claude Code): `local/config.json` con `{ "ciudad", "moneda", "idioma", "html_branding" }` y crear `local/investigaciones/`. Explicar que `local/` es privada y no se versiona.
   - **Sin carpeta** (claude.ai/celular): guardar los mismos datos en la memoria de Claude.
3. Verificar leyendo la config recién escrita y estrenar: "Prueba con: *investiga qué [producto que le interese] comprar*".

## Error handling
- Ciudad ambigua (hay varias con el mismo nombre) → confirmar país/departamento.
- El usuario no quiere responder algo → usar el default y decirlo.
