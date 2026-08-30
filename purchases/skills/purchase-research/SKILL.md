---
name: purchase-research
description: Deep-research a potential purchase in the Colombian market and deliver a report with an executive verdict plus a shareable HTML comparison. Use this skill when the user says "investiga qué <producto> comprar", "ayúdame a decidir entre", "búscame opciones de", "compárame <productos>", "qué <producto> me recomiendas", or any variant of wanting to research a purchase before deciding.
---

# Purchase research

Full research of a potential purchase: multi-angle search, real price/availability verification, weighted value matrix, and archivable deliverables.

## Bootstrap
Resolve the config (city, currency, language, `html_branding`) per the agent's CLAUDE.md: `local/config.json` if present; otherwise Claude memory; if nothing, offer `purchases-setup`. Options without real shipping to the user's city (or justifiable pickup in a nearby city) **don't count** — discard them early.

## Standard process

### 1. Brief
Capture: what the user wants, budget (if any), use cases, constraints, and who it's for (criteria change — see `references/`).

### 2. Multi-angle search
Workflow of ~5 agents with distinct angles: marketplace, official brand stores, big retail, specialists, community/reviews, and (if applicable) the specific use case. Each agent returns structured options: name, key specs, price in local currency, store, URL, shipping availability. (Proven pattern: ~50 options in ~23 min.)

### 3. Browser verification (mandatory for finalists)
Never trust search results — they are usually stale. Verify in the browser: real price, stock, shipping to the user's city. Mark each finalist as verified with an explicit date in the report and HTML (Colombian 25-40% discounts expire fast).

### 4. Value matrix
Comparison table with use-case-relevant specs, price, and a weighted score per the brief. Include an efficiency view (score ÷ price, "points per million") — it tends to reveal that mid-range options win on value. **After-sales service weighs explicitly (~15%)** when the user lives outside the big cities.

### 5. Deliverables
- `report.md` (in the configured language): **executive verdict first** (what to buy, where, price, why — argued by cost-benefit, never by lowest price alone), then findings, matrix, and warnings.
- `<comparison>-con-claude.html`: usable and responsive — comparison tables desktop-only (≥900px); on mobile, cards carrying the full row's information; filters in both modes and a sort selector on mobile. Named in the report's language, self-descriptive, ending in `-con-claude`. Branding per config (if the house artifact skill is available, use it).
- Save everything under `local/research/YYYY-MM-<topic>/` (with `data/` for raw outputs).

## Search & verification conventions (learned from real cases)

- **The same product varies wildly in price across channels.** Always compare: official brand store vs big retail (Éxito, Alkosto, Falabella, Ktronix) vs Mercado Libre vs specialists. Real case: the same phone was $424,000 COP cheaper at retail than at the brand's own store. Big retail also solves shipping/warranty/pickup.
- **Local retail coverage**: verify which chains have a physical store in the user's city — it varies in mid-size cities, and in-person warranty may (or may not) justify a moderate premium (~$150,000 COP).
- **Mercado Libre blocks automated verification** (anti-bot wall). Its prices arrive via indexed snippets: treat them as approximate, open the listing manually before deciding, and prefer MercadoLíder sellers with invoicing.
- **Search agents get key specs wrong.** Real case: they reported a processor/IP rating/speakers that didn't match the variant actually sold in Colombia. During finalist verification, confirm processor, RAM of the exact variant, and decisive details on the store's spec sheet + one recent review — the verdict can flip.
- **After-sales red flag**: the brand's official local domain dead or hijacked (real case: a scooter brand's Colombian domain redirected to a betting site). No living distributor → no spare parts — check each brand's local domain before recommending it.
- **Real battery life/performance ≈ 50-60% of the brochure** for battery products (official figures come from bench tests); under demanding conditions discount more. See `references/mixed-terrain-criteria.md`.
- **Regulation**: when applicable (mobility, drones, etc.), note the Colombian legal limits (e.g. >25 km/h exceeds micromobility rules on public roads — VELMPU law).

## Per-profile criteria (references/)

- Purchase for an **older adult** (tech): read `references/older-adult-criteria.md` before building the matrix.
- Product for **mixed terrain / outdoors**: read `references/mixed-terrain-criteria.md`.

These files grow: when a research run produces reusable criteria for a new profile, add them as a new reference.

## Error handling
- **Config not found**: offer `purchases-setup`.
- **No local offer for the product**: say it clearly and evaluate importing only if the user asks (taxes + warranty).
- **Inconsistent prices across sources**: the browser-verified, date-stamped one wins.
