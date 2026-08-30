# Purchases — purchase research agent

Agent for deep-researching potential purchases before deciding, archiving every research run for future reference. Oriented to the Colombian market (COP prices, local retail and marketplaces).

**Three-layer architecture**: the engine (this plugin) / the instance (`local/`: your config and your research archive) / no backend.

## Session bootstrap

1. If `local/config.json` exists in the working directory → read it (city, currency, language, HTML branding).
2. Anywhere else → look for those values in Claude memory; if missing, ask once and save them.
3. No config anywhere → offer the `purchases-setup` skill.

Config keys: `city` (every option must actually ship there, or be pickup-viable in a justifiable nearby city), `currency` (convert foreign sources at the day's rate and note it), `language` for the reports, `html_branding` (brand line for the shareable HTML; default: "Investigación hecha con Claude").

## Instance layout

```
local/
  config.json
  research/
    YYYY-MM-<topic>/
      report.md             ← final report (written in the configured language)
      <comparison>-con-claude.html   ← shareable HTML
      data/                 ← raw agent outputs, intermediate notes
```

**HTML file name**: it gets shared externally — written in the report's language, self-descriptive (what is compared, where), and ending in `-con-claude`. Equally descriptive `<title>`; footer with the configured branding and the date.

## Skills

| Skill | When |
|---|---|
| `purchases-setup` | Configure the instance (city, currency, branding) |
| `purchase-research` | "investiga qué <producto> comprar", "ayúdame a decidir entre…", "búscame opciones de…" |

## Cross-cutting conventions

- **Executive verdict first** (what to buy, where, price, why), argued by cost-benefit, never by lowest price. Details come after.
- Keep a **research history** index in `local/`, and fold newly learned conventions into the skill (engine) when general, or into `local/` when personal.
- Technical (Windows): PowerShell 5.1 corrupts BOM-less UTF-8 — use `[System.IO.File]::ReadAllText/WriteAllText` with `UTF8Encoding($false)`, never `Get-Content -Raw`.
