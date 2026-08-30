# Health — per-person health reports

Agent for generating personalized health reports (PDF, in Spanish) for each family member, from lab results and medical context. The core is the `personal-health-report` skill.

**Three-layer architecture**: the engine (this plugin, 100% agnostic) / the instance (the per-person spaces, see below) / the data (each person's exams and reports — NEVER in this repo).

## How the instance is organized (each person's data)

Two equivalent modes — the skill detects context on its own, without interrogating the user:

1. **One Claude Project per person** (web/mobile, recommended): a Project per family member ("Salud Papá", "Mi salud"), with their lab PDFs and prior reports as project files and their description in the project instructions.
2. **One local folder per person** (Claude Code): `local/people/<name>/` with exams and prior reports. `local/` is gitignored — never versioned or shared.

## Agent rules

- The report is for the **patient**, not for whoever requested it: tone and form of address by age (see the skill).
- Never invent values; cite figures and dates from the documents.
- Exactly one disclaimer per report; don't dilute the content with repeated hedging.
- The deliverable is the **PDF**; the .docx is kept only as regeneration source.
- Quick questions about a single exam → answer inline, no full report.

## Skills

| Skill | When |
|---|---|
| `personal-health-report` | "informe de salud", "analiza estos exámenes para [persona]", "genera el informe actualizado" |
