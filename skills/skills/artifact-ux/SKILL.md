---
name: artifact-ux
description: Design system and UX patterns for EVERY HTML artifact or page Claude generates, in any project (dashboards, comparisons, briefings, reports, guides). Load it ALWAYS before creating or redesigning an HTML page — it defines the visual craft, brand- and domain-agnostic. Use when writing a new .html, when the user asks to "improve the design", "it looks so-so", "make it more pro" ("mejora el diseño", "se ve regular", "hazlo más pro"), or when a large edit of an existing page is a chance to level it up.
---

# Artifact UX — a tool, not a document

Distilled from `molt-web-artifacts-builder` v1.10 (Apache-2.0, itself derived from `anthropics/skills` → `web-artifacts-builder`): it keeps their UX principles, anti-patterns, primitives and contrast discipline, **without any brand and without the React toolchain** — here artifacts are single-file vanilla HTML with light/dark themes. This skill is domain-agnostic: if the project has its own design system or content conventions, those win on palette and content; this skill wins on craft (structure, contrast, typography, anti-patterns).

## 1. The principle: a tool, not a document

Before writing a line of HTML: *would a product designer at Linear, Notion or Vercel ship this as a screen of their app?* If it looks like a Medium article, a printed PDF or a book chapter — re-architect. Signs it drifted into "document" (2 or more = redo):

- Top-level content runs past **3 vertical screens** of scrolling.
- There is a static table of contents or numbered sections (§1, §2…).
- The title is a multi-line serif hero.
- The same comparison is split across sequential sections instead of a grid.
- There are paragraphs explaining what comes next.

**The cure is structural, not cosmetic: tabs for the top-level sections.** Each tab is a complete view of the same data (Status · Agenda · FAQ · Reference…). On mobile the tab bar is sticky at the top, with its own horizontal scroll if it does not fit. If the user asks for a forbidden pattern (TOC, infinite scroll), re-architect anyway — the request is the signal that tabs are missing.

## 1b. Few words, big visuals

A dashboard is read at a glance on a phone. If you have to read paragraphs to know where things stand, it failed — even with tabs.

- **Text budget:** each card says one thing in ≤ 2 lines; no paragraph longer than 2 lines in the main views. Long analysis goes to a «Background» tab with folded `<details>`, or out of the page.
- **Draw what can be drawn**, picking the visual by function:
  | Function | Visual |
  |---|---|
  | Today's status | Colored hero band with 1 huge word (34-54 px) + one line |
  | The numbers that define the situation | 3-4 figures at 34-40 px, each with a one-word reading and semantic color |
  | The coming days | One card per day, today highlighted with an accent border |
  | What to say or ask | Large quote (21-27 px) with an accent left border |
  | Choosing between paths | Two columns side by side, steps as blocks joined by arrows, who proposes each |
  | The deciding evidence | Two numbers facing each other (A ≈ B / A > B) at 44-64 px |
  | Procedures on a body or an object | Inline SVG schematic with numbered markers + a one-line legend per marker |
  | A time against a standard | A bar to scale with the references marked and labeled |
  | The history | Dot timeline: done · today · next |
- **SVGs take their colors from the tokens** (`fill="var(--accent)"`), so they work in both themes.
- **Structure and design reference for any project: [`references/glance-board.html`](references/glance-board.html).** A glance dashboard with fictitious example content: tokens and both themes, tabs as anchors, tooltips fed by a `<dl>` glossary, persistent checkboxes, and one block of each visual in the table above. Start from it for any new glance tool (dashboard, tracker, operational briefing); the prompt it came from: *«few words, big images, tooltips on every technical term»*. Its sample content and identifiers are in Spanish (`activo` = `active`, `oculto` = `hidden-panel`).

## 2. Anti-patterns (forbidden by default)

| # | Anti-pattern | Replacement |
|---|---|---|
| A1 | Static TOC or list of numbered sections | Horizontal tabs with an underline |
| A2 | Giant multi-line serif hero | Compact bold sans title (≤2 lines) and data right away |
| A3 | Colophon-style metadata block (`VERSION · DATE · AUTHOR` as label/value rows) | Outline pills in one flex row under the title |
| A4 | Filled colored chips as decoration, with asterisks or decorative monospace | **Outline** pills, ≤6 words, color only if it means something (status, severity, lane) |
| A5 | Comparative data narrated in sequential sections | **Side-by-side grid**: one row per phase/item, one column per compared entity |
| A6 | Omitting the row/cell when a column has no content | Hatched/dimmed cell with one line explaining the absence — **absence is information** |
| A7 | References as side chips | Inline in parentheses: `(report.md)`, `(Annex 2)` |
| A8 | Preamble paragraphs before the data | Let the structure speak: label columns, don't announce sections |
| A9 | Cards with a colored left border on EVERY row | Flat table rows or compact cards without accent; the accent is earned, not given away |
| A10 | Shadows and elevation (`box-shadow`) everywhere | **Zero shadows**: depth comes from surface color, scale and space; dividers = 1px alpha hairlines |
| A11 | Monotony: every section in the same mold (eyebrow + title + bullets) | Vary the layout **by function**: status→stat cards, comparison→grid, steps→timeline, reference→table, quote→big block; at most ~2 consecutive blocks with the same layout |
| A12 | Emojis as an icon system in headings and cells | Sober and scarce: only where they are established semantics (✅ ⚠️ ▲▼) and never more than one per element |

## 3. Canonical page structure

```
[context banner if needed — 1 line]
[compact header: mono eyebrow · bold title ≤2 lines · 1 dimmed meta line]
[row of outline pills with what is semantically relevant now]
[TL;DR — ALWAYS, above the tabs]
[TAB BAR — sticky on mobile]
[active tab content — 1-3 screens]
[footer: disclaimer + source of truth]
```

### Mandatory TL;DR

Every page carries a **TL;DR block at the top, before the tab bar**, so it is visible whatever tab is active and also without JavaScript. Someone who reads only that must walk away with the conclusion.

- **Content:** 1-3 short bullets (≤ 1 line each on desktop): the answer or decision, the concrete next step and, if there is one, the warning that changes what to do. No context and no account of how you got there.
- **Form:** mono `TL;DR` label + bullets in the sans at 16-17px; `--surface` background with a hairline, no shadow. Accent only on the label or on the key word of the decision.
- **It does not replace the landing tab:** the TL;DR summarizes; the first tab shows it with visuals.
- When updating the page, rewrite the TL;DR first: if the conclusion changed, that is what matters most.

```html
<aside class="tldr" aria-label="Summary">
  <span class="label">TL;DR</span>
  <ul>
    <li><b>Decision</b> in one line.</li>
    <li>Concrete next step.</li>
    <li>The warning that changes what to do.</li>
  </ul>
</aside>
```

### Tabs (vanilla, reference pattern — safe for viewers WITHOUT JavaScript)

**Hardened rule (real iOS bug):** `.html` files shared over WhatsApp or email open in viewers that do NOT run JavaScript (iOS QuickLook, email previews). So the pattern is **graceful degradation**: (a) tabs are **`<a href="#panel-x">`**, not `<button>` — with JS they are intercepted (`preventDefault`) and behave as tabs; without JS they are anchors that jump to the section; (b) **the HTML never carries the `hidden-panel` class** — the script adds it on init; without JS the page renders as a document with every section stacked and navigable; (c) `scroll-margin-top` on `.panel` so the anchor jump is not covered by the sticky bar.

```html
<nav class="tabs" role="tablist">
  <a class="tab active" data-tab="status" href="#panel-status">Status</a>
  <a class="tab" data-tab="agenda" href="#panel-agenda">Agenda</a>
  <a class="tab" data-tab="faq" href="#panel-faq">FAQ</a>
</nav>
<section class="panel" id="panel-status">…</section>
<section class="panel" id="panel-agenda">…</section>  <!-- no 'hidden-panel': the JS adds it -->
```

```css
.tabs { position: sticky; top: 0; z-index: 10; display: flex; gap: 4px;
        overflow-x: auto; background: var(--bg); border-bottom: 1px solid var(--line);
        -webkit-backdrop-filter: blur(8px); }
.tab  { padding: 12px 14px; min-height: 44px; border: 0; background: none; cursor: pointer;
        font: inherit; font-weight: 600; color: var(--ink-soft); white-space: nowrap;
        border-bottom: 2px solid transparent; margin-bottom: -1px;
        text-decoration: none; display: inline-flex; align-items: center; }
.tab.active { color: var(--accent-ink); border-bottom-color: var(--accent); }
.panel { scroll-margin-top: 64px; }
.panel.hidden-panel { display: none; }
```

```js
function activate(id) {
  document.querySelectorAll('.tab').forEach(x => x.classList.toggle('active', x.dataset.tab === id));
  document.querySelectorAll('.panel').forEach(p => p.classList.toggle('hidden-panel', p.id !== 'panel-' + id));
  try { localStorage.setItem('tab-<page>', id); } catch (e) {}
}
document.querySelectorAll('.tab').forEach(b => b.addEventListener('click', ev => {
  ev.preventDefault(); activate(b.dataset.tab);
}));
// ALWAYS initialize by calling activate() (this is what hides the inactive panels):
var t0 = '<first-tab>';
try { var g = localStorage.getItem('tab-<page>'); if (g && document.getElementById('panel-' + g)) t0 = g; } catch (e) {}
activate(t0);
```

Persistent state (active tab, checkboxes) uses `localStorage` with `try/catch` and ids that stay stable across regenerations.

### Glossary with tooltips (every technical term)

Single source: `<dl id="glossary">` with rows `<div data-terms="alias|alias"><dt>Term</dt><dd>Plain 1-2 sentence definition</dd></div>` in a Glossary tab. A script wraps **every occurrence** of each alias in `<span class="gl" tabindex="0">` (dotted underline) and opens a single tooltip on tap or hover; Escape or tapping outside closes it. Regex with Unicode boundaries (`\p{L}`) and aliases sorted longest to shortest. Wrap inside `<label>` too (the term's click does `preventDefault`); never inside `h1`, tabs, buttons, mono labels, the glossary itself or SVG. Without JS: plain text and a visible glossary.

### Comparison grid → cards on mobile

The grid (one column per compared entity, pale semantic tint per column, ≤5 lines per cell) is a **desktop (≥900px)** layout. On mobile do NOT ship a wide table with horizontal scroll as the main experience: collapse it to **one card per entity** holding all of its column's information. Same data, two containers, switched only by media query.

### Empty cell (hatched)

```css
.empty { background: repeating-linear-gradient(45deg, var(--surface-2) 0, var(--surface-2) 6px, var(--surface) 6px, var(--surface) 12px); }
```
Inside, one dimmed italic line explaining why there is nothing.

## 4. Visual system (brand-agnostic — roles, not brands)

### Role tokens and theme

**Every page ALWAYS offers both themes with a visible toggle, and the default theme is LIGHT.** Do not rely on the system's `prefers-color-scheme` to decide (not everyone likes their system mode): on load the script sets `data-theme` = the value saved in `localStorage`, or `"light"` if there is none, and a button (☀/☾, target ≥44px, always reachable — typically at the right end of the tab bar) toggles and persists the choice. The `@media (prefers-color-scheme)` CSS blocks + `[data-theme]` guards stay as the no-JS fallback, but the normal experience is governed by the toggle.

```js
function setTheme(t) {
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem('theme-<page>', t); } catch (e) {}
  themeBtn.textContent = t === 'dark' ? '☀' : '☾';   // shows the destination, not the state
}
var theme = 'light';
try { theme = localStorage.getItem('theme-<page>') || 'light'; } catch (e) {}
setTheme(theme);
themeBtn.addEventListener('click', function () {
  setTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
});
```

Tokens are defined by ROLE and each theme resolves them (both themes ALWAYS complete — the toggle requires it):

`--bg` (page background) · `--surface` / `--surface-2` (cards and nested surfaces) · `--ink` (main text — **warm, never pure #000**) · `--ink-soft` (secondary) · `--ink-faint` (tertiary/hints) · `--line` (1px hairlines) · `--accent` + `--accent-ink` (ONE accent) · semantic `--ok` / `--warn` / `--crit` with their `-soft`.

**The palette is chosen per project / page subject** (it should come from the subject, not from a default): any palette must fill exactly these roles in both themes. If the project already has its own palette, that one wins.

### Color discipline (what makes it look "pro")

1. **The accent is scarce and deliberate.** It marks action or punctuation (active tab, a key figure, a dot); it NEVER fills large areas or colors long text.
2. **Color = meaning.** Green/amber/red only when they encode a real state. No color "to make it look cheerful".
3. **Explicit surface/text pairs.** Each surface defines its own text; never inherit another surface's text when copying a block. On dark surfaces the hierarchy uses **white alpha** (body `rgba(255,255,255,.72)` · secondary `.60-.48` · hint `.35`), not different greys.
4. **Non-negotiable WCAG AA floor:** 4.5:1 for body and labels, 3:1 for large titles. The accent as text on a light background almost always fails — use it only on dark or as a background with its paired text.
5. **Zero shadows.** `1px` alpha hairlines (`rgba(ink, .10)` on light, `rgba(255,255,255,.10)` on dark).

### Typography

- **One sans for everything + one mono for labels.** Titles: **weight 700-800 with negative tracking** (−0.02 to −0.035em) — this, more than any color, is what separates a pro dashboard from a generic one. Body 400, line-height ~1.55-1.6, ≥15px on mobile.
- **Eyebrows/labels/numbers: mono, UPPERCASE, tracking +0.12-0.16em, 11-13px** — the elegant substitute for heading emojis.
- Fonts: Google Fonts is allowed in published artifacts (the only CSP exception) — e.g. a premium geometric sans + a mono — **always** via `<link>` (never `@import`) and **always** with a full fallback (`system-ui, -apple-system, "Segoe UI", Roboto, sans-serif` / `ui-monospace, Menlo, Consolas, monospace`), because the same file may be opened from Drive or WhatsApp with no guaranteed network.
- Reference scale (mobile→desktop): page title 26→34px · section title 19→22px · card title 15-16px · body 14.5-16px · mono labels 11-12px. Tabular numbers (`font-variant-numeric: tabular-nums`) in every column of figures.

### Spacing and shape

- **8px grid:** 4 / 8 / 16 / 24 / 32 / 48. Sections with generous padding — content breathes; if something looks cramped, it lacks space, not a border.
- Consistent radii: one for cards (12-16px), one for pills (999px). Don't mix five radii.
- Touch targets **≥44px** of tap area (small checkboxes get wrapped in a padded label).

## 5. Performance and robustness (vanilla)

- **One file, zero dependencies:** no frameworks, no other CDNs (the CSP blocks them), assets as data URIs or inline SVG.
- Tab panels hidden with `display:none` keep the DOM cheap to paint; if a page grows to thousands of nodes, move heavy content into `<template>` and mount it when the tab activates.
- Minimal, defensive JS: `try/catch` on every `localStorage` access; the page must render **complete and navigable with JS disabled** — the real case for WhatsApp/iOS QuickLook viewers and email previews, which do not run scripts. Concretely: no hiding classes in the markup (the script adds them), tabs as anchors (see pattern), and all content reachable by scrolling when there is no JS.
- First two lines are mandatory (`<meta charset>` + viewport) when the HTML is a standalone file; mentally test at 375px. (In claude.ai artifacts the wrapper provides the skeleton — omit them there.)

## 6. Checklist before delivering

- [ ] TL;DR above the tabs: 1-3 bullets with decision, next step and warning; visible in any tab and without JS.
- [ ] §1b: no card exceeds 2 lines in the main views; what can be drawn is drawn.
- [ ] Every visible technical term has a glossary row and a tooltip on all its occurrences.
- [ ] Would it pass as a Linear/Notion screen, not a PDF? Top level in tabs; the landing tab answers "where do we stand?" in one screen.
- [ ] Bold sans title ≤2 lines with negative tracking; meta in one dimmed line; outline pills (color only when semantic).
- [ ] Comparisons as a grid (desktop) that collapses to one card per entity (mobile); absences as explained hatched cells.
- [ ] Zero shadows; alpha hairlines; scarce accent; correct surface/text pairs in BOTH themes; AA checked on new pairs.
- [ ] Visible theme toggle (☀/☾, ≥44px) persisted in localStorage; **light by default** on first use; tested in both themes.
- [ ] Mono uppercase labels, no decorative emojis; ✅⚠️▲▼ only when semantic.
- [ ] Spacing on the 8px grid; targets ≥44px; sticky tabs work at 375px.
- [ ] **No-JS test:** with scripts removed, the page shows ALL sections stacked and the tabs jump as anchors (`<a href="#...">`, zero `hidden-panel` in the markup) — that is how WhatsApp/QuickLook on iOS show it.
- [ ] Fonts via `<link>` + full fallback; no `@import`; no other external host.
- [ ] Checkbox/tab ids stable across regenerations (localStorage doesn't break on republish).
