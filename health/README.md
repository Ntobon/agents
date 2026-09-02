# Health

A complete **family health management system** run by Claude on top of Google Drive. Not just reports: one master archive for the whole family (people and pets), a strict documentary pattern per member, and the skills to manage real clinical situations end to end — in Spanish, aware of the Colombian health system (EPS), and usable from the computer, the web, and the phone against the same files.

## What it does

- **Archive**: every document that arrives (photo in chat, email, PDF) gets archived per the pattern — raw original preserved, renamed copy, plain-language transcription, lab trend table, and the member's index updated. Nothing stays loose.
- **Personal health reports** (`personal-health-report`): age-adapted printable PDF for each member, updated when new exams arrive.
- **Medical package for appointments** (`medical-record-package`): a facts-only 1-2 page clinical summary with page-referenced curated annexes, merged into one print-ready PDF; signed documents go as real scans; imaging annexes include the study images. Email delivery offered.
- **Private dashboards** (`internal-html-dashboard`): the owner's mobile-first living boards — status, agenda with persistent checkboxes, frank Q&A with sources, emergency signs — archived in Drive and republished to a stable URL.
- **Clinical trials surveillance** (`clinical-trials`): ClinicalTrials.gov search with honest pertinence analysis against the documented case.
- **EPS status package** (`eps-status-package`): the administrative counterpart of the medical package — a factual status of filings, authorizations, orders, and appointments (states written as the insurer lives them, every blocked item chained to its blocking filing number) plus annexes only from the insurer's circuit, in one PDF forwardable verbatim to an insurer coordinator. No family strategy, no private-track documents, no third-party names.
- **Recurring order** (`archive-audit`): a weekly scheduled routine that re-archives strays, resolves sync clashes, updates indexes and context files, and polices the agent/context separation.
- **Zero-friction growth** (`add-family-member`): "quiero agregar un nuevo miembro" creates the whole structure — the user never makes folders.

## The three layers

| Layer | Where it lives | Shared? |
|---|---|---|
| The engine (skills, templates, routine) | This plugin | ✅ 100% agnostic |
| The family's context (root + per-member CLAUDE.md/MEMORY/TAREAS) | The family's Google Drive folder | ❌ |
| The clinical documents | Same Drive folder (offline-enabled, connector-reachable) | ❌ |

Google Drive is the storage backbone: the same archive is available to local Claude Code sessions (mounted drive, offline mode) and to claude.ai web/mobile sessions (Drive connector, works even with the computer off).

## Installation

Say **"quiero instalarlo"** — `health-setup` guides everything with zero commands: Google Drive app + offline mode + connector, the master folder and root CLAUDE.md from the template, the plugin (synced to `Ntobon/agents`), the weekly audit, and a live verification archiving a first document.

Manual plugin install: claude.ai → Customize → Plugins → Add marketplace → *Add from a repository* → `Ntobon/agents` → Sync automatically → Add. In the Claude desktop app (Code tab), no terminal and no technical vocabulary for the person: open the health folder as the project, paste *"Instala el agente de salud familiar. Viene del marketplace Ntobon/agents, plugin health. Instala también todo lo que ese agente necesite para funcionar en este computador y avísame cuando esté listo, sin explicarme los detalles técnicos."* and approve the permission prompts (or switch the app to automatic permissions). Claude installs the plugin and every local dependency itself. Click alternative: `/plugin` → Marketplaces → Add → `Ntobon/agents` → Discover → health → Install. CLI users: `claude plugin marketplace add Ntobon/agents` + `claude plugin install health@ntobon-agents`.

## Try it with the demo family

Say **"puebla el sistema con la familia de ejemplo"** and the agent seeds a fully fictional family ([demo/](demo/README.md)): one member already archived per the pattern (two lab panels with trend, a consult note, a signed order, three open pendings) plus an inbox of two raw documents whose archiving closes those pendings. Every use case below can be run on it in minutes, with nothing real exposed. Delete the folder when done.

## Local requirements (Claude Code on a computer)

The person installs nothing: `health-setup` (Phase 1b) installs and verifies all of this itself through permission prompts. Cloud sessions (claude.ai, mobile) need nothing installed. For local sessions the skills' scripts use: **Python 3.10+** with `pymupdf`, `opencv-python`, `numpy`, `pillow`, `pypdf` (scanning, paginating and merging PDFs); **Node 18+** (the health report builder, `docx` package installed by the skill on first run); and, for the health report's PDF export, **Microsoft Word** on Windows or **LibreOffice** elsewhere. Missing pieces degrade gracefully: the agent says what it could not produce and delivers the rest.

## What it does NOT do

It doesn't diagnose, doesn't replace a medical consultation, doesn't dose medication, and never invents clinical data — every fact must trace to a dated document.
