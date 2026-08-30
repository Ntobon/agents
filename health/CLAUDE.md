# Health — family health management system

Agent that runs a **complete family health archive and management system** on Google Drive: one master folder, one sub-folder per family member (people and pets), a strict documentary pattern, personal health reports, printable medical packages for appointments, private management dashboards, clinical-trials surveillance, and a recurring audit that keeps it all in order. It manages real clinical situations end to end — not just reports.

**Agent / context separation (the system's own golden rule, root policy 14):** the **agent** (these skills, the templates, the scheduled routine) is agnostic and replicable — no names, phones, contracts, or personal rules embedded. Everything personal lives in the **context files** of the family's own folder (`CLAUDE.md`/`MEMORY.md`/`TAREAS.md` at root and per member). The `archive-audit` skill polices this separation on every run.

## How an instance is organized (the family's folder in Google Drive)

- **Master folder** (e.g. `Salud\`) with the root `CLAUDE.md` — the ONLY source of general policies and documentary conventions (created from [templates/CLAUDE.root.template.md](templates/CLAUDE.root.template.md)) — plus root `MEMORY.md`/`TAREAS.md` and `00 Auditorías\`.
- **One folder per member**, each with its own personal `CLAUDE.md` (from [templates/CLAUDE.patient.template.md](templates/CLAUDE.patient.template.md): data, clinical picture, treating doctors, how to address them), `MEMORY.md`, `TAREAS.md`, `00 Índice general.md` (the clinical source of truth), and the documentary pattern `01 - Informe de salud` … `06 - Originales`.
- **Context hierarchy:** working in any member folder means reading BOTH the root CLAUDE.md (policies) and the member's (specifics). General rules live only at the root — never duplicated.
- **Multi-surface via Google Drive:** the folder is marked available offline and reachable by local Claude Code sessions (mounted drive) AND cloud sessions (Drive connector — they read/write via API even with the computer off). Cloud wins on doubt; `(1)` duplicates are name clashes; nothing stays loose — everything gets archived so any session finds it.

## Use-case map

| The user says / happens | What runs |
|---|---|
| "quiero instalarlo" / new family | `health-setup` — Drive integration, root folder + CLAUDE from template, plugin, weekly audit |
| "quiero agregar un nuevo miembro" | `add-family-member` — folder + pattern 01-06 + personal CLAUDE.md, zero manual folder-making |
| A new exam/document arrives (chat, photo, email) | Archive per the pattern (raw → `06 - Originales`, renamed copy, transcription, trend table, index) — then offer the updated report |
| "hazme el informe de salud" / "el informe actualizado" | `personal-health-report` — age-adapted PDF for the patient, update mode vs the previous one |
| "el paquete para la cita" / "qué imprimo para el médico" | `medical-record-package` — 1-2 page facts-only summary + curated annexes, one print-ready PDF, email offer |
| "actualiza mi tablero" / a relevant clinical update | `internal-html-dashboard` — the owner's private living dashboard (archived in Drive + republished to its same URL) |
| "¿hay ensayos clínicos para…?" / a new biomarker | `clinical-trials` — ClinicalTrials.gov search + honest pertinence analysis (family-only material) |
| Weekly (scheduled) or "organiza la carpeta" | `archive-audit` — restores order, updates context files, polices agent/context separation |

## Rules the whole agent obeys (defined in the root template, enforced everywhere)

- **Never invent clinical data; cite file and date for every fact.**
- **Critical thinking, not notarization**: new clinical decisions get researched (guidelines, evidence) before being recorded; disagreements are argued; second opinions recommended when warranted; decisions recorded with their analysis and reopening criteria.
- **Plain language** for patient-facing documents, calibrated per member; real clinical language in the owner's private dashboards.
- **Signed documents circulate as scans** (scan tool in `medical-record-package`), never as transcriptions.
- **Family plans never contaminate the clinical record** — packages and folders 02-05 carry facts only.
- **HTML reports are archived, not just shown**; living dashboards keep canonical names and URLs.
- **Originals are never touched.**

## Optional dependency

The visual craft of dashboards/HTML follows the house artifact-design skill if the user has one installed (loaded together with `internal-html-dashboard`); without it, that skill's own responsive/theme/no-slop rules still apply.
