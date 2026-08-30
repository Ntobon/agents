---
name: personal-health-report
description: Generate personalized, printable health reports in Spanish for individual family members based on lab results, medical records, or general health context. Use this skill whenever the user asks for "informe de salud", "reporte médico personal", "health report", "analizar exámenes para [persona]", uploads lab PDFs and wants a summary, or asks for a document tailored to a specific family member (papá, mamá, esposa, hijo, yo mismo). Designed for use in per-person Claude Projects — the skill auto-detects patient identity from project files, system prompt, and past conversations before asking. Adapts recommendations by age (pediatric, young adult, middle-age, elderly) and balances preventive care with avoiding unnecessary invasive testing — essential context for the Colombian EPS health system. Default output is a polished PDF the person can read alone, print, or take to their doctor (built via an intermediate .docx that is kept only as regeneration source).
---

# Personal Health Report

Generate clear, personalized health reports for family members. Each report is tailored to the person's age, sex, and findings from their medical exams. The goal is a document the person (or their primary doctor) can use — readable, actionable, and respectful of evidence on what's worth doing at each stage of life.

The user typically organizes these as one Claude Project per person (papá, mamá, esposa, themselves) with lab PDFs and prior reports stored there. Each project produces an updated report when new exams come in.

## Core philosophy

Three principles guide every report:

1. **Personalization over templates.** The report is for a specific person — name them, address them appropriately, reference their specific findings. Generic boilerplate breaks the connection.

2. **Age-appropriate medicine.** What's standard preventive care at 35 may be unnecessary at 80. What's worth screening for at 60 may not be at 80. The skill consults `references/age_recommendations.md` to apply current evidence on de-intensification of screening, fall prevention, vaccines, and lifestyle priorities for the relevant age bracket.

3. **Colombian context.** The user navigates the Colombian EPS system (Sanitas, Sura, Compensar, etc.), which has access constraints and cost considerations. Recommendations should be realistic: what can be requested in a regular EPS consult, what specialists are reasonable to push for, what is unlikely to be covered.

## Workflow

### Step 1: Detect project context FIRST (silently, before asking anything)

This skill is designed for use in per-person Claude Projects (one project per family member). Always assume context exists and try to find it before bothering the user. Run these checks in this order:

**1.1 List project files.** Inspect `/mnt/project/` (or look for `<project_files>` in the system prompt). Medical PDFs typically state the patient's full name, date of birth, sex, and address. A single document often answers everything about identity.

```
view /mnt/project/   # or scan the project_files block in system prompt
```

**1.2 Read the system prompt for project-level instructions.** Claude Projects can have custom instructions describing the person ("This project is for tracking my dad Alberto, born 1946, EPS Sanitas"). These instructions are part of the system prompt and may already answer who/what without the user repeating themselves.

**1.3 Search past conversations.** Use `conversation_search` with the patient's likely name or "informe" / "salud" / "exámenes" to find prior reports and discussions. A prior report tells you:
- The patient's identity (confirmed)
- The tone used last time (preserve consistency)
- What recommendations were made (so the new report can update them)
- What was pending (so you can check if it was resolved)

**1.4 Read any prior report in the project.** If `Informe_Salud_*.docx` or similar exists in the project files, read it. The new report is an update to that one, not a fresh start.

**1.5 Build a working profile**. After 1.1-1.4, you should know:

- **Name** and how the person should be addressed (Don/Doña, primer nombre, Mamá, etc.)
- **Age** (calculate from DOB on lab reports if needed; round to current age in years)
- **Biological sex**
- **Relationship to the user** (inferred from project name, prior chats, or system prompt — "Salud Papá" / "Mi salud" / "Mamá")
- **Known conditions and medications** mentioned anywhere in context
- **Prior report exists?** (yes → update mode, no → initial mode)

**Only ask the user to fill in what truly cannot be inferred.** If lab PDFs in the project clearly state "GOMEZ RIOS ALBERTO, 17-nov-1946, Masculino" and the project is named "Salud Papá", do not ask "who is this for?" — that wastes the user's time and feels broken. Confirm only ambiguous items briefly, like "¿Le sigo diciendo 'Don Alberto' como en el informe anterior, o prefieres otro tratamiento?"

**Self-report detection.** If the project name is generic ("Mi salud", the user's own name) or past conversations are in first person ("mis exámenes", "yo"), treat this as a self-report and adjust tone (more casual, "tú" or matching the user's prior style).

**When there is NO project context** (someone using the skill in a one-off chat without a project), ask for the missing essentials before proceeding: name, age, sex, what they want the report to focus on.

### Step 2: Analyze available documents

Read all uploaded medical documents in the project. Look for:

- **Lab trends across dates** — not just the latest value but the trajectory
- **Out-of-range values** — flagged with `*` or outside reference ranges
- **New findings** vs **stable patterns**
- **Pending items** — exams recommended but not done (hematuria workup not closed, suspicious imaging not followed up, etc.)
- **Derived calculations** when useful: eGFR from creatinine, BMI, HbA1c-to-eAG conversion

Read PDFs with the `view` tool. For each document, note the date — the same patient may have multiple visits, and ordering matters.

**Update mode (a prior report exists in the project):**
- Identify what is NEW since the last report (new labs, new findings)
- Check whether previously pending items were resolved (e.g., "the hematuria workup was recommended last report — did it happen? what was the result?")
- Preserve continuity: if the last report called the person "Don Alberto", keep that. If it used certain recommendations, evolve rather than restart.
- Lead with the change. The reader's first question is "what's different this time?"

**Initial mode (no prior report):**
- Build the full picture from scratch
- Establish the baseline that future reports will compare against

### Step 3: Apply age-appropriate framework

**Required reading before writing the report:** `references/age_recommendations.md`. Find the section for the patient's age bracket and use it to:

- Determine which screenings are appropriate (and which to actively de-intensify)
- Identify lifestyle priorities for this stage
- Check vaccine recommendations
- Calibrate red flag symptoms

Also consult `references/lab_reference_values.md` when interpreting borderline values — reference ranges shift with age (e.g., a hemoglobin of 11.8 is mild anemia in any adult but is interpreted differently at 25 vs 79).

### Step 4: Generate the report

Build the report using `scripts/build_report.js`. The script accepts a JSON content structure and produces a styled `.docx`. See `assets/example_content.json` for a complete example.

To run:

```bash
node scripts/build_report.js path/to/content.json /path/to/output.docx
```

The script handles styling — Claude only constructs the content data. This keeps reports visually consistent across people while allowing full content flexibility.

### Step 4b: Convert to PDF (the deliverable)

**The deliverable is the PDF, not the .docx** — the reports are not meant to be edited, and PDF opens everywhere (phone, WhatsApp, print shop). Convert right after building:

- **Windows with Microsoft Word installed** (the user's usual environment): run `scripts/convert_to_pdf.ps1`:

  ```
  powershell -File scripts/convert_to_pdf.ps1 -DocxPath "ruta\Informe_Salud_[Nombre].docx"
  ```

  It produces the PDF next to the .docx with the same name, preserving styling exactly.
- **Linux / claude.ai container:** use `libreoffice --headless --convert-to pdf` or the pdf skill's tooling.

Keep the .docx next to the PDF as the regeneration source (do not deliver it unless the user asks for an editable copy).

### Step 5: Present the file

Save the output next to any prior reports (or `/mnt/user-data/outputs/` on claude.ai) as `Informe_Salud_[Nombre].pdf` and surface the **PDF** to the user.

## Report structure

Every report should include these sections, adapted to age:

1. **Opening message** (info box, warm, name-first) — brief context, what to expect, disclaimer
2. **Panorama general** — three blocks: what's well, what's stable, what needs review
3. **Próximas acciones (1-3 meses)** — concrete, prioritized requests for the next medical visit
4. **Cuidados diarios** — habits relevant to this age and these findings
5. **Vacunas** — age-appropriate vaccine schedule, ask which ones are up to date
6. **Lo que probablemente NO necesita** — de-intensification with rationale, framed positively
7. **Señales de alarma** — when not to wait, age-appropriate symptoms
8. **Plan práctico** — concrete checklist for EPS + things to start today
9. **Nota final** — warm closing, perspective on overall trajectory

Sections can be added/removed/renamed if the patient profile warrants it. For example:
- Pediatric reports may add "Crecimiento y desarrollo"
- Reports for someone with no medical data may skip "Panorama general" and emphasize prevention
- Reports for high-acuity patients may add "Seguimiento de [condición]"

## Tone calibration

The report is for the **patient**, not the user who requested it. Adjust voice accordingly:

| Patient profile | Tone | Address |
|---|---|---|
| Child (0-11) | Read with a parent. Brief, simple, focused on prevention | Use first name |
| Adolescent (12-17) | Direct, respectful of emerging autonomy, mental health awareness | First name, tú |
| Young adult (18-39) | Peer-like, focus on long-term habits | First name, tú |
| Middle-aged (40-64) | Practical, direct, no condescension | Tú or usted depending on user preference |
| Early elderly (65-74) | Respectful, clear, with rationale | Usted, with respectful form of address |
| Late elderly (75+) | Warm, "usted", clear and uncluttered, larger considerations spelled out, generous spacing | Don/Doña + nombre is often appropriate |

Always confirm with the user how the patient should be addressed if it's not obvious. Default: ask once at the start.

## Critical principles

**Disclaimers, not disclaimers.** Include exactly one disclaimer in the opening box ("este documento no reemplaza la valoración médica"). Do not pepper the report with hedging on every recommendation — it dilutes the useful content.

**Specific over generic.** "Hemoglobina 11.8 (apareció en mayo 2026)" beats "tiene anemia leve". Cite numbers and dates so the doctor can verify.

**De-intensification with rationale.** When recommending NOT to do something (colonoscopy at 80, prostate biopsy with stable PSA), briefly explain why. "Las guías no recomiendan después de los 75 si las anteriores fueron normales" is more useful than just "no hace falta".

**Action over information.** Each section should leave the reader knowing what to *do*, not just what's true. Pair findings with next steps.

**Never invent values.** If a number isn't in the documents, don't put it in the report. If a calculation is approximate (like eGFR from creatinine alone without using the full CKD-EPI formula), say "aproximadamente".

**Drug names in Colombian context.** Use brand names common in Colombia alongside generic names (acetaminofén / Dolex / Winadol; ibuprofeno / Advil) so the patient recognizes them in the pharmacy.

## What this skill does NOT do

- Does not give a diagnosis. It interprets findings and suggests questions for the doctor.
- Does not replace a medical consultation.
- Does not recommend specific medication dosing.
- Does not extrapolate beyond what the documents support.

If the user asks for any of the above, redirect to "this is something to discuss with the treating physician" while still providing the report on what the documents do show.

## Examples of good triggering

- "Hazme un informe de salud para mi mamá con estos exámenes" → trigger
- "Analiza estos labs y crea un reporte" → trigger
- "Genera el informe actualizado para papá" (in a project) → trigger
- "¿Qué dice este examen?" → analyze and discuss inline, do NOT generate a full report
- "Resúmeme estos resultados" → inline summary, NOT a full report

The skill produces a full Word document. For quick questions or interpretation, answer inline without generating a file.
