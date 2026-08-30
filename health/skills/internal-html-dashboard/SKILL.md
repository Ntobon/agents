---
name: internal-html-dashboard
description: Creates or updates the owner's private HTML reports (living tracking dashboards, full-information briefings for relatives, situation reports) for any patient in the family health folder. Use when the user asks for "el HTML para mí", "actualiza mi tablero", "el centro de seguimiento", "un reporte para entender dónde vamos", "agrégale una sección al reporte", or when a relevant clinical update warrants refreshing an existing dashboard. These documents are PRIVATE to the owner (real clinical language, without the softening used in patient-facing folder 01) and are read mostly ON THE PHONE.
---

# Internal HTML dashboard (the owner's private boards)

## What it is and for whom

The reader is **the owner on their phone**, managing the case in real time: between appointments, in the waiting room, answering WhatsApp. The document must answer in seconds "where are we, what's next, what does it mean" — with **complete, accurate, non-condescending information**. Real clinical terms are used here; softened language is only for patient-facing documents (folder 01 and each patient's communication rule).

## Non-negotiable rules

1. **Archive first, publish second (root policy 11).** The `.html` file lives in the patient's folder: **living** dashboards under a canonical name (e.g. `00 Centro de seguimiento (solo el dueño).html`); **one-off** reports dated (`AAAA-MM-DD Informe … .html`). Edit the file, then republish the artifact **to its same URL** (recorded in the patient's `MEMORY.md`). Never mint a new URL for an existing dashboard; on a publish conflict, read the published version, integrate, and publish again.
2. **Responsive, mobile first (design rule, 2026-08-18).** Always, as the FIRST lines of the file: `<meta charset="utf-8">` and `<meta name="viewport" content="width=device-width, initial-scale=1">`. The artifact wrapper adds them at publish time, but these files are also opened straight from Drive or forwarded by WhatsApp — **without the charset declared, iOS/Safari decodes as Latin-1 and accents come out broken ("CastaÃ±o")**, which is exactly what happened to a family member in a real case. Also: grids with `auto-fit/minmax`, never fixed widths; every table inside an `overflow-x: auto` container; a media query collapsing two-column grids to one on narrow screens (≤560 px); touch targets ≥15 px; body ≥14 px. Mentally test every section at 375 px wide.
3. **Light/dark theme.** Full palette as tokens on `:root` (light), redefined under `@media (prefers-color-scheme: dark)` guarded as `:root:not([data-theme="light"])`, and again under `:root[data-theme="dark"]`. Body background always explicit with a token.
4. **Critical thinking with sources (root policy 8).** Every new clinical answer or recommendation is researched before being written (guidelines, web search) and the section containing it closes with a sources line. Nothing is invented: every clinical fact comes from a dated document in folders 02-06, or a cited source.
5. **Privacy.** Fixed top banner stating it is the owner's private document and recalling the current communication line with the patients. The artifact is published private; it is not shared unless the owner asks.
6. **No-slop writing (design rule, 2026-08-19).** Before delivering, run every block through this filter:
   - **One block, one job.** Each section, card, or paragraph does ONE job (give a number, a script, a decision). If it needs sub-parts or does two jobs, it's two blocks — or one is redundant.
   - **The cut test.** Sentence by sentence: "if I delete it, what does the reader lose?" If nothing, delete it. Applies especially to motivational closers, repeated justifications, and transition phrases.
   - **Grounding: each concept explained ONCE.** A term (portability, lymphadenectomy, remission) is grounded the first time it appears and not re-explained in every section that uses it.
   - **Each datum lives in ONE place.** Phones, dates, and prices appear once where they're used; the "Datos rápidos" table is the only allowed repetition (it's the reference).
   - **Bold only for the actionable**: numbers, dates, names, decisions. Not for rhetorical emphasis.
   - **No management ornaments**: no "the gem", "the master move", "pure gold", "it's important to highlight". The naked fact convinces on its own.
   - **Deliberate format**: a list only for truly parallel items; a table only when the same shape repeats 3+ times; everything else, short prose.
   - **Mobile measure**: each action block (one call, one task) must fit on a phone screen.
7. **The visual craft is defined by the house artifact-design skill — ALWAYS load it together with this one (design rule, 2026-08-27).** This skill says WHAT goes on the board; the design skill says HOW it looks and navigates: tool-not-document (top level in tabs, not one long scroll), banned anti-patterns, outline pills with semantic color, comparison grids that collapse to cards on mobile, contrast and typography discipline. If an existing dashboard is still a linear scroll, the next big edit migrates it to tabs preserving ids and URL.

## Structure of a living dashboard (the proven pattern)

In order — sections exist if there's content; never pad:

1. **Private banner** (warning + agreed communication line).
2. **Header**: eyebrow, title, line "Actualizado: <date and rough time> (<what changed>)" — updated on EVERY edit.
3. **Stat cards** (auto-fit grid): the 3-5 numbers/states that define the situation today.
4. **"Lo nuevo hoy"**: what happened and what it means, in `concept` blocks (bold fact + plain explanation).
5. **"Tus preguntas — respuestas francas"**: a living section. Every question the owner asks in chat gets answered here (numbered, dated), researched, with sources at the section's foot. Old answers stay while valid; they're retired when the case makes them obsolete.
6. **Immediate agenda**: per-day blocks with persistent checkboxes (`localStorage`). **Checkbox `id`s are stable and never reused** (t1, t2, … t99) — recycling an id inherits another task's saved state in the owner's browser. Done tasks get ✅ in the text and stay a while as record before being retired.
7. **Critical path / lanes** (private · insurer · legal, or whichever apply).
8. **Scenarios**, each with "your move".
9. **Concepts to keep straight** (`concept` blocks).
10. **Emergencies** (critical box): signs that mean going to the ER without waiting.
11. **Coordinated communication** (table): what is said to whom.
12. **Datos rápidos** (table): phones, case numbers, doctors, medication, latest measurements.
13. **Footer**: disclaimer (informational, doesn't replace the treating team) + source of truth (the patient's folder in Drive).

## Update flow

1. Read the patient's `CLAUDE.md`, `MEMORY.md`, and `00 Índice general.md` (the clinical source of truth is the index, not the dashboard).
2. Edit the canonical file in Drive (don't regenerate from scratch: it preserves checkbox ids and the URL).
3. Update the header's "Actualizado:" line and whichever stat cards changed.
4. Republish to the artifact's same URL (recorded in the patient's `MEMORY.md`), with a short version `label`.
5. If the change reflects new clinical facts, verify the patient's index/management registry already has them — the dashboard is never the only place a fact lives.

## Verification before delivering

- [ ] The Drive file was updated BEFORE publishing (policy 11).
- [ ] Meta viewport present; tables with overflow; grids collapse well when narrow.
- [ ] "Actualizado:" reflects this edit.
- [ ] No checkbox changed `id`; new ones use never-used ids.
- [ ] New clinical answers have sources; case data has file and date.
- [ ] Republished to the SAME URL; the link is handed to the owner in chat.
