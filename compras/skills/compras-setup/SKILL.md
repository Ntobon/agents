---
name: compras-setup
description: Configure a new instance of the purchase-research agent (city, currency, language, HTML branding, and the research archive folder). Use when the user says "quiero instalarlo", "install this", "configura el agente de compras", "setup de compras", or when investigar-compra can't find its configuration.
---

# Compras Setup

Lightweight onboarding — this agent has no backend. **The user runs no commands**: Claude asks and writes everything.

**Idempotent**: if the config already exists and is complete, show it and exit.

## Steps

1. Ask (one round, plain language):
   - What city are you in? (options must actually ship there)
   - Price currency? (default: COP)
   - Report language? (default: Spanish)
   - Do you want a brand line on the shareable HTMLs? (default: "Investigación hecha con Claude")
2. Write the config:
   - **With a working folder** (Claude Code): `local/config.json` with `{ "city", "currency", "language", "html_branding" }` and create `local/investigaciones/`. Explain that `local/` is private and never versioned.
   - **No folder** (claude.ai/mobile): save the same values to Claude memory.
3. Verify by reading back the config just written, then first use: "Try: *investiga qué [product they care about] comprar*".

## Error handling
- Ambiguous city (several share the name) → confirm country/region.
- The user skips a question → use the default and say so.
