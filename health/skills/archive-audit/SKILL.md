---
name: archive-audit
description: Audits and organizes the family health folder's document archive — per member and at the root. Detects loose or unarchived documents per the documentary pattern, "(1)" sync clashes, indexes/CLAUDE.md/MEMORY/TAREAS out of date versus the real files, missing sources next to PDFs, and drift between skill copies. Fixes the mechanical, records what needs a decision, and leaves a dated report. Use when the user asks for "auditoría", "organiza la carpeta", "revisa el archivo", or when the scheduled routine runs it.
---

# Archive audit and organization

## Why

Clinical situations are chaotic: documents arrive by chat, email, and phone; sessions (local and cloud) write in parallel; the archive drifts. This skill is the routine that restores order **without waiting to be asked**: it audits, fixes the mechanical, and leaves a trail of what it can't decide alone.

It is **member-agnostic**: it walks any folder that follows the documentary pattern of the root `CLAUDE.md`. It assumes no proper names — it takes them from the "Quién es quién" table of the root `CLAUDE.md` of the folder where it runs.

## Scope of a run

Walk in order: **the root** of the health folder and **each member folder** listed in the root `CLAUDE.md`. In each, first read its `CLAUDE.md`, `MEMORY.md`, `TAREAS.md`, and `00 Índice general.md` (if present) — the audit compares **what the context files say against what actually exists on disk**.

## The checks (per member folder)

1. **Loose files in the member's root.** Any file that isn't context (`CLAUDE.md`, `MEMORY.md`, `TAREAS.md`, `AGENTS.md`, `00` prefix) nor a dated management document (`AAAA-MM-DD …`) is a candidate for archiving per the pattern: raw to `06 - Originales\<year>\`, renamed copy to the matching 01-05 folder, transcription if it's an exam. If the destination is doubtful, don't move: note it in the report.
2. **Sync clashes.** Files with `(1)`, `(2)` suffixes: keep the newest version under the canonical name, verify no content is lost (root policy 10), and record the resolution.
3. **Structure.** Folders 01-06 exist; empty ones have their `00 Sin documentos aún.md`.
4. **Index up to date.** Every document in folders 02-06 dated after the last line of the index's timeline must be reflected (timeline + its folder's section). Pendings closed by new documents get removed.
5. **Member's CLAUDE.md up to date.** Diagnoses, medication, doctors, and the one-sentence picture against the most recent documents. Only what's specific to the member — if it repeats root policies, trim and reference (context hierarchy).
6. **MEMORY and TAREAS.** New durable facts recorded with date; done tasks moved to "Hechas"; new tasks detected by the audit noted with date.
7. **Form policies.** Generated PDFs with their source (`.md`/`.html`/`.docx`) next to them; shown/published HTML also archived (policy 11); signed documents present as scans, not just transcription (policy 12); family plans out of the clinical transcriptions in folders 02-05 (policy 13 — if mixed, move the plan to the management files).

## The checks (agent level — once per run)

8. **Zero duplicate skill copies (rule, 2026-08-28).** A skill lives in ONE place; if it needs to exist at two levels (user and project), one is the source and the other is a **reference stub** that only points to it (plus the project's particulars). If the audit finds two copies with content, consolidate into the general one and turn the other into a stub — never "sync" them and let them coexist. (Real case: a design skill drifted into different defaults; it was consolidated as user-level source + project stub.)
9. **Agent/context separation (replicability rule, 2026-08-28).** Skills, templates, and routines are **the agent** and must be agnostic: no names, phones, emails, contracts, or personal rules embedded — those live in each folder's `CLAUDE.md`/`MEMORY.md` (**the context**). If a personal datum appears in a skill, move it to the corresponding context file and leave the generic reference in the skill ("the appointments contact defined in the patient's CLAUDE"). Record each extraction in the report — it's progressive work, not to be fully solved in one run.
10. **Health folder root.** Loose items in the general root (e.g. `tmp\`): archive or propose a destination. General `TAREAS.md` and `MEMORY.md` up to date.

## Intervention rules

- **The mechanical gets fixed** (move, rename, update indexes/context), always citing the source document.
- **The doubtful is not touched**: it goes in the report with a proposal. Never delete content; the originals in `06 - Originales\` are never touched.
- No fix invents clinical data (policy 1) or changes family decisions — the audit orders the archive, it doesn't opine on the case.

## Output

1. **Dated report**: `00 Auditorías\AAAA-MM-DD Auditoría.md` at the health folder root (create `00 Auditorías\` if missing). Structure: summary (what was fixed, what's pending) → findings per member → agent-level findings. Runs with no findings leave a one-line report ("todo en orden") — the record that it ran is information too.
2. **New tasks** in the corresponding `TAREAS.md` (the ones that need the family).
3. If the run changed anything relevant, **update the affected MEMORY.md files** (policy 10: leave the delta written).
