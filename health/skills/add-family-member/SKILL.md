---
name: add-family-member
description: Adds a new member (person or pet) to the family health folder — creates their folder with the full documentary pattern (01-06), their personal CLAUDE.md from the patient template, MEMORY/TAREAS, and registers them in the root CLAUDE.md's "Quién es quién" table. Use when the user says "quiero agregar un nuevo miembro", "agrega a mi mamá al sistema", "crea la carpeta de salud de <persona>", "nuevo paciente", or uploads documents for someone who doesn't have a folder yet.
---

# Add family member

Creates everything a new member needs — **the user never creates folders or files by hand**.

## Steps

1. **Ask the human minimum** (one round): name and how they're called, relationship to the owner, ID number, birth date, insurer/plan, city of care. A pet works too (species, vet instead of insurer). Any datum they don't have at hand can stay as `<pendiente>` — the audit will chase it.
2. **Create the folder** in the health root, named as the family refers to the person (`Madre\`, `Papá\`, the pet's name — whatever they actually say).
3. **Create the documentary pattern** inside (root CLAUDE.md conventions):
   ```
   <Member>\
   ├── CLAUDE.md                  ← from templates/CLAUDE.patient.template.md, filled with step 1
   ├── MEMORY.md · TAREAS.md      ← empty with headers
   ├── 00 Índice general.md       ← skeleton: index + empty timeline + no open pendings
   ├── 01 - Informe de salud\ … 05 - Órdenes y remisiones\
   │                              ← each with its "00 Sin documentos aún.md" explaining what
   │                                 goes there and how to obtain it
   └── 06 - Originales\           ← raw documents land here, by year
   ```
4. **Fill the member's `CLAUDE.md`** from [templates/CLAUDE.patient.template.md](../../templates/CLAUDE.patient.template.md): data, one-sentence clinical picture (or "sin información clínica aún"), how to address them (age → tone, usted/tú — the writing rules live in the template), and any specific rule the user states now (e.g. communication line).
5. **Register in the root `CLAUDE.md`**: add the row to "Quién es quién" (folder, person, documentation state).
6. **Offer the first ingestion**: "¿Tienes exámenes o documentos de <nombre> para archivar de una vez?" If yes, archive them per the pattern (raw + renamed copy + transcription + index) — that leaves the folder alive, not empty.

## Rules

- All personal data goes to the member's `CLAUDE.md`/context files — never into any skill (root policy 14).
- If the folder already exists, don't duplicate: offer to complete what's missing (pattern folders, CLAUDE.md, index).
- Names of pattern folders and meta files are canonical (Spanish, as the template defines them) — don't translate or vary them; the whole system navigates by them.
