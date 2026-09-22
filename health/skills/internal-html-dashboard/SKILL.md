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

8. **Every technical term gets a tooltip, on every occurrence (family request, 2026-09-05; widened by the owner, 2026-09-22).** The dashboard uses real clinical vocabulary, but no reader should trip on a word. Single source: the glossary in the Glossary tab, as `<dl id="dicc">` with one row per term, `<div data-terms="alias|alias…"><dt>Term</dt><dd>Definition</dd></div>`. **Definitions are one or two short plain-language sentences** (a long definition does not fit in a tooltip). A script wraps **every occurrence** of every alias (not just the first) in `<span class="gl" tabindex="0">` with a dotted underline; tap or hover opens a single tooltip (`#tip`) with title and definition; Escape or tapping elsewhere closes it. Match with Unicode word boundaries (`\p{L}`) and aliases sorted longest first. Wrap inside task `<label>`s too (clicking the term calls `preventDefault` so the checkbox doesn't toggle); never inside `h1`, the tab bar, buttons, mono labels, the glossary itself, or SVG. Everything in `try/catch`: **without JS the dashboard stays intact** (terms as plain text, glossary visible). Every new term enters the glossary first; when writing, prefer the word that already has a row.

9. **Few words, big visuals (owner's rule, 2026-09-22: "it is very hard to read").** The dashboard is glanced at on a phone, not studied. Text budget: each card says **one thing in ≤ 2 lines**; no paragraph longer than 2 lines in the main views; a task = one line + one small subline. Whatever reads better drawn gets drawn:

   | Job | Visual |
   |---|---|
   | Today's state | Colored hero band with one huge word (34-54 px) + one line |
   | The numbers that define the situation | 3-4 figures at 34-40 px, each with a one-word reading in semantic color |
   | The next days | One card per day, today's outlined in the accent |
   | What to say or ask the doctor | Large quote (21-27 px) with an accent left border |
   | Choosing between paths | Two side-by-side columns, steps as blocks joined by arrows, who proposes each |
   | The evidence that decides | Two facing numbers (A ≈ B / A > B) at 44-64 px |
   | Procedures on the body | Inline SVG schematic with numbered markers + a one-line legend per marker |
   | A time against a benchmark | To-scale bar with the references marked and labeled |
   | The history | Dot timeline: done · today · next |

   SVGs take their colors from the theme tokens (`fill="var(--accent)"`) so they work in both themes. Long analysis (sourced Q&A, quick-reference data, detailed scenarios) leaves the main views: it lives in the patient's index/MEMORY and, if wanted on the board, in a "Background" tab of collapsed `<details>`. Whatever is removed from the board is archived first — the dashboard is never the only place a fact lives.

**Reference implementation: `assets/dashboard-reference.html`** (next to this SKILL.md). It is the owner-approved design of 2026-09-22 filled with a fictitious example case: theme tokens for both themes, the tabs/theme/checkbox/tooltip script, and one block of every component (hero, figures, day cards, quote, side-by-side paths, facing numbers, scenario bar, per-stage bars, trajectory, anatomical schematic, benchmark bar, timeline, tasks, glossary, collapsed sources). **Every new dashboard starts by copying it** and replacing the content, written in the owner's language; unused components are deleted. The prompt that produced it is a good way to ask for it: *"few words, big visuals, and a tooltip on every technical term"*.

## Structure of a living dashboard (pattern of 2026-09-22)

Top-level tabs, each 1-2 phone screens; a tab exists only if it has content:

1. **Private banner**, one line (the owner's document, not for patients).
2. **Header**: mono eyebrow (patient · age · condition), title, one line "Updated: <date>" — updated on EVERY edit.
3. **Today**: hero band with the day's state (what, when, where) · 3-4 big figures with a one-word reading · the week as day cards · the question to ask, as a large quote. Emergency signs go here as a red card when active.
4. **Decision** (when one is open): the paths side by side with who proposes each · the deciding evidence as two facing numbers · what would tip the balance, in 3 cards.
5. **What they'll do / the body** (when procedures are coming): SVG schematic with numbered markers + one-line legend · care points for these days, in 3 cards.
6. **Route**: to-scale bar of the time that matters against its benchmark · dot timeline (done / today / next).
7. **Tasks**: grouped by when (today · day X · this week), checkboxes persisted in `localStorage`. **Checkbox `id`s are stable and never reused** (t1…t99) — recycling an id inherits another task's saved state in the owner's browser.
8. **Glossary**: the single source for the tooltips (rule 8).
9. **Background** (optional): long Q&A and analysis in collapsed `<details>`, with sources.
10. **Footer**: disclaimer (informational, doesn't replace the treating team) + source of truth (the patient's folder in Drive).

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
- [ ] Rule 9: no card exceeds 2 lines in the main views; what can be drawn is drawn (hero, figures, days, paths, schematic, bar, timeline).
- [ ] Rule 8: every visible technical term has a glossary row and is underlined on every occurrence.
- [ ] New clinical answers have sources; case data has file and date.
- [ ] Republished to the SAME URL; the link is handed to the owner in chat.
