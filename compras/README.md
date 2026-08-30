# Compras

Purchase research agent for the Colombian market: deep-researches a potential purchase (multi-angle search with ~5 agents, real in-browser verification of price/stock/shipping, weighted value matrix) and delivers a report with an **executive verdict** plus a **shareable HTML comparison**. Every research run is archived for future reference.

## Installation

Lightweight agent (no backend). Installs from the `Ntobon/agents` marketplace:
- **claude.ai** (web + mobile): Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → Add.
- **Claude Code**: `claude plugin marketplace add Ntobon/agents` + `claude plugin install compras@ntobon-agents`.

Then say **"configura el agente de compras"** (30 seconds: city, currency, branding) and try it with *"investiga qué [producto] comprar"*.

## The three layers

| Layer | Where it lives | Shared? |
|---|---|---|
| The engine (process, conventions, per-profile criteria) | This plugin | ✅ |
| Your instance (`local/config.json` + `local/investigaciones/`) | Your folder / your Claude memory | ❌ |

## What it can do

| You say | Result |
|---|---|
| "investiga qué patineta eléctrica comprar" | Full report + HTML comparison, with date-stamped verified prices |
| "ayúdame a decidir entre X y Y" | Value matrix weighted to the use case |
| "es para mi papá de 80 años" | Applies specialized per-profile criteria (references/) |
