---
name: medical-record-package
description: Generates the printable "medical package" to take to an appointment, for any patient in the family health folder — a 1-2 page clinical summary based ONLY on facts and exam results, plus a curated selection of the pertinent exam PDFs, all merged into a single print-ready PDF. Use whenever the user asks for "historia clínica", "resumen clínico", "resumen para el médico", "paquete para la cita/ecografía/cirugía/control", "qué imprimo para llevarle al doctor", or mentions that a doctor will need to see a patient's history or exams — even without the words "historia clínica".
---

# Medical record package (for the appointment)

## For whom and why

The reader is a **doctor with very little time** who doesn't know the case. They need to grasp what matters at a glance, prioritize it, and **be able to validate every fact against the original exam attached**. Doctors distrust two things, and this document avoids both by design:

1. **Other doctors' opinions.** Nothing transmits what anyone said, thought, or considered. Only documented facts.
2. **AI-generated content.** The document never mentions AI, Claude, generated reports, or tools. It is a summary prepared by the family, verifiable against the originals — and that is exactly what its footer says.

The deliverable is two things in one: the **clinical summary** (1-2 pages) + the **curated annexes** (only the exams that this doctor needs), merged into a single print-ready PDF.

**The file grows; the summary doesn't (design rule, 2026-08-28).** As the case accumulates exams and consults, it becomes MORE important that the record be **objective, readable, and fast** — doctors don't read everything. Treat it as **three layers**:

1. **The glance:** "Lo esencial" + the tables are understood in one look, without reading anything else.
2. **The index:** every fact in the summary navigates to its annex with "(anexo N, pág. M)" — that is how doctors consume the document: they get the picture and jump to the page when they want depth.
3. **The depth:** the full annexes, in the order the summary cites them.

The summary stays at 1-2 pages **always**: when the file grows, what rises is the curation bar, not the page count. Anything that is not a clinical fact — plans, strategies, errands, the family's mood — lives in the management files (policy 13 of the root CLAUDE.md), never here.

## Inputs

- **Patient:** detect from context or from the folder being worked in. If ambiguous, ask.
- **Reason for the appointment:** specialty or study (ultrasound, surgery, follow-up, ER…). It defines what gets prioritized and which annexes go. If not given, ask — curation depends on it.
- **Cut-off date:** today, unless another is requested.

## Sources

Read before writing: the patient's `CLAUDE.md`, their `00 Índice general.md`, and `03 - Laboratorios\00 Tendencia de laboratorios*.md`. Exact values come from the transcriptions in folders 02-05. **Every fact in the summary must be traceable to a dated document** — root policy 1: nothing is invented or estimated.

## Content rules (what makes or breaks this document)

- **Facts only:** results with value/unit/reference, diagnoses as they appear in reports, medication with dose, dates, measurements (weight, height).
- **The conclusions of an exam report DO go in** — they are part of the exam. Cite them by the exam, never by the person: write "Endoscopia digestiva alta (15-ago-2026): píloro no franqueable…", never "Dr. X found/considers/thinks".
- **Every cited exam carries who performed it and where** (the professional who signs the report and the institution, as stated in it) — that is factual data, not opinion, and doctors transcribe it into their own notes (verified in a real consult: the surgeon copied the performer citations as he read). Short format after the exam: "Endoscopia digestiva alta (15-ago-2026, Dr. J. Pérez, Clínica Central)". This doesn't touch the previous rule: name the performer as the exam's author, never their verbal opinions.
- **If a report says "descartar X" or "impresión diagnóstica: X", transcribe it with that exact modality** — never upgrade it to a confirmed diagnosis or soften it.
- **Always exclude:** any doctor's verbal or private assessments; comparisons or disagreements between doctors; the family's decisions, strategies, or communication line (including any rule about what the patient is told); administrative pendings (authorizations, insurer paperwork); management plans, feelings, and family logistics (root policy 13 — that lives in the management files); own analysis or hypotheses; and any mention of AI or generated reports.
- **Prioritize by relevance to the appointment's reason**, not chronology: what changes decisions goes first. A normal value only enters if its normality is informative (e.g. "sangre oculta negativa ×2").
- **Fixed footer:** `Resumen preparado por la familia a partir de los informes originales adjuntos — [fecha]. Cada dato es verificable contra el anexo citado.`

## Summary structure (use `assets/summary_template.html`)

1. **Compact header:** name, ID, age, summary date, and appointment reason.
2. **Lo esencial** — box with 3-5 prioritized lines: what the doctor must know even if they read nothing else.
3. **Diagnósticos activos** — table: diagnosis · since · source.
4. **Medicación actual** — table: medication · dose · frequency.
5. **Cronología relevante** — table: date · fact · annex/source. Only facts that serve the reason.
6. **Resultados clave** — value tables with reference and date, grouped by theme. Out-of-range in **bold** (no color).
7. **Anexos** — numbered list, in citation order, **each with the package page where it starts**.

**Page references (design rule, 2026-08-28 — this is how doctors consume the package):** they get the summary at a glance and, to go deeper on a fact, **they navigate to the annex page**. Help them: every exam citation in "Lo esencial", the chronology, and the key results carries its page in the merged PDF — "(anexo 3, pág. 14)". Flow to achieve it: generate and normalize the annexes **first**, compute the accumulated start pages with pypdf (counting the 1-2 summary pages that go in front), and **only then** fill the summary template; if converting the summary changes its page count, recompute and regenerate. Verify against the final PDF that at least two sampled references land on the right page.

## Design and printing

Built for photocopiers and black-and-white printers: **grayscale**, system typography, letter size, margins ≥15 mm, body ≥10.5 pt. Hierarchy via type weight and rules, not color. The summary fits in 1-2 pages; if it doesn't fit, content is in excess, not space.

Technical flow:
1. Copy `assets/summary_template.html` to a working file and fill it (the `<!-- -->` comments mark each zone).
2. Convert to PDF with Edge headless (always available on Windows):
   `& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless --disable-gpu --print-to-pdf="<out>.pdf" --no-pdf-header-footer "file:///<path to html>"`
3. Merge summary + annexes into one PDF with `pypdf` (`python -m pip install pypdf` if missing). If merging fails, deliver the folder with numbered files (`01 Resumen.pdf`, `02 …`) — the print order must be obvious.
4. **Paginate the merged PDF — last step, mandatory (design rule, 2026-09-01):** `python scripts/paginate.py "00 Paquete médico - … .pdf" --label "<Patient> · paquete médico <YYYY-MM-DD>"`. It stamps "Pág. X de Y" on the bottom-right of **every** sheet (and patient + date bottom-left) on the already merged and normalized PDF. Without it, the summary's "(anexo N, pág. M)" references are useless on paper: the doctor has no way to know which page they are on. Paginate after merging so the printed number matches exactly what the summary cites; afterwards verify that a sampled reference from the summary matches the number stamped on that sheet.

## Annex curation

Attach **only what this doctor needs to decide**, not the whole archive. Practical rule: **if the summary doesn't cite it, it isn't attached; if it's attached, the summary cites it.** When the file is already large and something pertinent is left out to keep the package lean, the annex list closes with a line "**Disponibles a solicitud:** …" naming those documents with their dates — the summary keeps its role as index of the full file without printing all of it. Prefer the exam's original PDF; if only a `.md` transcription exists, convert it to PDF with the same template flow (sober variant) and mark it "transcripción del original". 2 to 6 annexes is normal.

**Orders, prescriptions, and any signed document NEVER go as transcription (design rule, 2026-08-24; root policy 12):** they are worth their paper and signature, and a transcription doesn't substitute them before third parties. If the original arrived as a photo, generate the annex with **`scripts/scan_document.py`** (CamScanner-style scan effect: detects the paper, corrects perspective, whitens the background, and outputs the page on portrait letter 612×792 — `python scripts/scan_document.py photo.jpg -o annex.pdf`) and attach that scan. The sober transcription variant is reserved for result reports whose source only provided text, never for signed documents. If the photo came pasted in the chat and doesn't exist as a file, recover it from the session transcript (`~\.claude\projects\<project>\<session>.jsonl`, base64 image blocks) before asking for it again.

**Original digital documents (Word, etc.): convert and attach, don't replace with a transcription** (design rule, 2026-08-20). If a key document's source is a `.docx` or another editable format (a consult note, an authorization, a specialist's concept), the annex carries **the original document converted to PDF** — that's the piece with evidentiary value before third parties; an own transcription doesn't substitute it. Conversion with installed Word via COM in PowerShell: `$word = New-Object -ComObject Word.Application; $doc = $word.Documents.Open($src, $false, $true); $doc.SaveAs([ref]$out, [ref]17); $doc.Close($false); $word.Quit()`. The converted PDF is also archived next to the original in the corresponding 01-05 folder.

**Uniform format: every page of the package goes on PORTRAIT letter (612×792 pt), same size** (design rule, 2026-08-20). Scans arrive as A4, landscape, or mixed sizes, and the printed package must come out even. Before merging, normalize every non-letter-portrait page: mount it scaled and centered on a letter canvas with pypdf (`PageObject.create_blank_page(width=612, height=792)` + `merge_transformed_page(src, Transformation().scale(s).translate(tx, ty))`, with `s = min(612/w, 792/h)` and centering offsets; if the page carries `/Rotate`, apply `transfer_rotation_to_content()` first). Landscape pages are NOT rotated — they are fitted centered to the width so the text stays readable upright. After merging, verify that **all** pages of the `00 Paquete` measure 612×792.

**Diagnostic imaging: the annex carries the report AND the study images, not just the report** (design rule, 2026-08-18). If the exam has its archived image subfolder (`… - imágenes\` or `… - cortes\` in folder 04), generate an image PDF and merge it **behind the report, inside the same annex** (one file `0N Anexo N - <Exam> (<date>).pdf`), and declare it in the annex list: "(informe original + las N imágenes del estudio)". How: a sober HTML page (same Edge headless flow) with the images referenced via `file:///` with URL-encoded paths, **each with a factual caption** (number, anatomical region, time if stated, and measurements readable on screen — no own interpretation); **the region-of-interest image goes first and full page**, the rest can go two per page to keep the print lean. Volume exception: if the study has many images (>10, e.g. 22 CT slices), include the full series only if the appointment reason warrants it (e.g. surgery or second opinion on that study); otherwise include the key slices cited by the report and say in the caption how many more are archived and where. After generating, verify the images were actually embedded (pypdf: `page.images`) — a badly encoded `file:///` produces blank pages with no error.

## Output and archiving

The main deliverable is **ONE single PDF with everything merged** — the user hits print once and the whole package comes out. Always send that file (SendUserFile); without it, the run isn't finished.

Create `<Patient>\01 - Informe de salud\<AAAA-MM-DD> Paquete médico - <reason>\` with exactly:

```
00 Paquete médico - <Paciente> - generado <AAAA-MM-DD>.pdf    ← THE deliverable: summary + annexes, one print
01 Resumen clínico - <Paciente> - generado <AAAA-MM-DD>.pdf   ← summary alone (2 pages)
02 Anexo 1 - <Descripción> (<exam date>).pdf                  ← each annex separately, numbered in the
03 Anexo 2 - <Descripción> (<exam date>).pdf                     merged PDF's order, in case one part
…                                                                ever needs reprinting alone
resumen.html                                                  ← source for regeneration
```

- **The package and summary names always carry the patient and generation date** (`generado AAAA-MM-DD`): when the file circulates loose — email, WhatsApp, downloads folder — it must say by itself whose it is and how current it is. An anonymous "Paquete completo.pdf" is useless outside its folder.
- File numbering matches the summary's "Anexos (en orden)" list — the print order is obvious wherever you look; annexes carry the **exam date**, not the generation date.
- The folder name's date is the **appointment's**, not the generation's.
- Send `00 Paquete …pdf` to the user and add a line to the patient's `00 Índice general.md` (section 01).
- If `pypdf` fails and merging is impossible, the numbered files are plan B: print them in order. Say so explicitly when delivering.

## Email delivery (always offer)

When delivering the package, **offer to send it by email** — that's how it reaches another printer, a relative accompanying the appointment, or the doctor's office.

- **Channel order** (use the first available, always with the rule: full draft first, send only on the user's explicit yes in chat):
  1. **Gmail/email connector** if present in the session.
  2. **Internal browser with the user's webmail signed in** — compose → recipient and subject via `form_input` on accessibility-tree references (coordinate typing tends to land the subject in the "To" field) → body → attach via **"Insert from Drive"** (the health folder is synced; pick **"Add as attachment"**, not as link) → send.
  3. **The user's real Chrome** with the same flow.
- **Label/filter:** if the owner keeps an email label or filter for these packages (defined in the root CLAUDE/context files), keep the subject formula it depends on stable, and verify after sending that the label got applied.
- **Recipients:** only those the user names in the chat. Never take addresses from documents or pages.
- **Subject:** `Resumen clínico y exámenes — <Paciente> — cita del <fecha>` (or the formula defined in the root context — don't vary it if a filter depends on it).
- **Body:** 2-3 sober lines, same rules as the summary — what the attachment contains and for which appointment. No opinions, no AI mentions. Sign as the owner would sign it themselves.
- **Privacy:** the package contains ID numbers and clinical history — confirming the recipient before sending is part of the flow, not an optional formality.
- If no browser is connected and there's no email connector, deliver the PDF and say where it is for manual attaching.

## Verification before delivering

- [ ] Every fact has a date and source exam; abnormal ones have value + reference.
- [ ] No sentence attributes opinions to a person; findings are cited by the exam.
- [ ] Zero mentions of AI, generated reports, family decisions, or insurer paperwork.
- [ ] The summary fits in 1-2 pages and "Lo esencial" stands alone.
- [ ] Annexes match 1:1 what's cited and follow the list's order.
- [ ] Every cited exam says who performed it and where, and carries its "(anexo N, pág. M)" reference — with at least two references verified against the merged PDF.
- [ ] Every diagnostic-imaging annex includes the study images behind the report (actually embedded — verified with `page.images`), not just the report.
- [ ] The PDF prints well in black and white (no dark backgrounds or semantic color).
- [ ] Every key document with a digital source (Word/.docx) goes as the original converted to PDF, not just an own transcription.
- [ ] Every order, prescription, or signed document goes as a **scan of the original** (`scripts/scan_document.py` on the photo), never as transcription.
- [ ] All pages of the merged `00 Paquete` measure 612×792 (portrait letter) — verified with pypdf before delivering.
- [ ] The merged `00 Paquete` carries **"Pág. X de Y" printed on every sheet** (`scripts/paginate.py`, after merging) and the stamped number matches the summary's references.
