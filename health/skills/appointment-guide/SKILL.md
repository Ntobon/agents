---
name: appointment-guide
description: Prepares the "appointment guide" — the 1-2 page sheet the companion takes to a medical appointment to know which decision they must walk out with, at which moments they can intervene, and the only 2-3 questions that fit, ranked by priority and aware of the care route (previous and upcoming appointments). For any patient in the family health folder. Use when the user asks "qué le pregunto al médico", "preguntas para la cita", "qué decido mañana", "cómo manejo la consulta", "con qué tengo que salir de la cita", "guía para la cita", or when the medical package for an appointment already exists and what is missing is the conversation strategy. It is not the medical package (`medical-record-package`) nor the private dashboard (`internal-html-dashboard`).
---

# Appointment guide (what to walk out with, and what to ask)

## The problem it solves

A companion arrives at the appointment with a stack of documents and a list of twenty questions a model generated. In practice they ask none: the doctor has 15-20 minutes, talks to **the patient** (not the companion), examines, dictates the note and closes. Most doctors do not welcome being interrogated, and a long list reads as distrust. The companion gets **two or three real interventions** in the whole consultation.

This skill inverts the logic: it first defines **which decision the visit must end with** (one, written in the clinical record), and only then derives the **2-3 questions** that secure it — as a ladder, so that if only one fits, it is the right one. Everything else (context, scenarios, checklist, what not to do) serves that exit.

## Inputs

- **Patient and appointment:** specialty, physician if known, date, time, site, authorization number. Taken from the patient's `CLAUDE.md`, the index and folder 05 (scheduling sheets).
- **The route around the appointment:** which appointments came before and which come after, with dates. **This is what almost no question list accounts for and what changes the questions the most**: if the surgeon's appointment is on Friday, today's question is not "will you operate?" but "what do you leave in writing for Friday's surgeon?".
- **The medical package for the appointment** (if it exists, from `medical-record-package`): its pages are cited in the guide ("show page 17") so the companion points at a document instead of arguing.
- **The pending decision** per the patient's index and dashboard (`internal-html-dashboard`, script and FAQ): the long analysis lives there; the guide distills it, never repeats it.
- **Who accompanies and how much they can intervene.** Ask if unknown: it changes the tone of the scripts.

## Content rules

1. **One exit only.** The guide opens with the card "What I walk out with today (or the visit was useless)": the decision that must be **written in the clinical record** and whom it must reach. If the companion reads only that card, they already know what to do. Anything that does not serve that exit is cut.
2. **At most 3 questions, as a ladder.** Question 1 closes the decision and **connects with the next appointment on the route**. Questions 2 and 3 are **conditional** ("only if they say X"), never a list to read through. Each question carries a one-line "why" underneath in 9 pt, so the companion asks it with conviction rather than from memory. **Questions follow the root policy on strategic questions:** question 1 is open and general, asked from the doctor's standpoint ("what is the plan?"); the next ones go one step down only if the doctor opens the door; technical findings from the analysis are never put to the doctor as questions (they become a neutral request, such as asking for the medication sheet, or a single plain-language doubt if it is a safety matter).
3. **Intervention moments, not communication advice.** Three concrete moments: (a) one sentence on entering — hand over the package open at page 1, name the next appointment, stop talking; (b) while the doctor talks to the patient: do not interrupt, contribute only facts the patient does not know; (c) at the close, when the doctor summarizes the plan: question 1, and the others only if there is room.
4. **Scenario table "If they say… / what it means / what I ask to be written".** The most valuable part after the exit: it anticipates 3-5 possible answers and, for each, the exact sentence that must land in the record so the route does not roll back. Always include the scenario where the doctor **hands the decision to someone else** ("the surgeon/oncologist decides that"): it only works if they write that they see no indication for the alternative.
5. **Critical thinking, without arguing in the office (root policy 8).** If the conduct the doctor may propose contradicts what the family expects, the guide says so **beforehand** ("chemo before surgery is standard conduct, not a delay in itself") and gives the **single legitimate objection** as a question ("do you see her tolerating it with the obstruction?"), grounded in facts already in the package. Never quote clinical guidelines to the doctor nor bring other doctors' opinions as authority — point at the document's page, not at the person.
6. **Exit checklist** (5-6 ☐ boxes): conduct written (photo before leaving), correct diagnostic code, orders on paper with codes, dates, and the note mentioning the next appointment.
7. **"What NOT to do today"**: whatever contaminates this specific visit — mentioning insurer proceedings or litigation in front of the doctor, asking for prognosis in front of the patient, handing over more than two documents, arguing conduct.
8. **"What I bring"**: short table with each document and **which page to open it at**; what stays in the bag and comes out only if requested (originals, imaging discs).
9. **One line for the patient** at the end, if applicable: how to explain before entering what this doctor decides and what the next one decides, in the tone the treating physician already set with them.
10. **No new clinical data.** Every fact comes from the medical package or the index, dated. The guide does not diagnose nor recommend treatment; the footer says so.

## Format (root policy 15: cards, not text blocks)

- **1-2 letter pages**, grayscale, bordered cards; the exit card is **black with large white type** — the only one that must be readable from afar.
- Fixed order: exit → how to intervene · the 3 questions (side by side) → scenario table → checklist · what not to do (side by side) → what I bring → footer.
- Header with date, time, physician, site, arrival time and authorization number.
- Footer: "Internal family guide · <date> · Clinical data come from the medical package generated on <date>; the conduct is the treating physician's decision."

## Technical flow

1. Read the patient's `CLAUDE.md`, `00 Índice general.md` (open clinical pendings and appointments), the appointment's scheduling sheet in folder 05 and the `resumen.html` of the current medical package (for page numbers).
2. Write the HTML with the cards (use the latest `AAAA-MM-DD Guía para la consulta de … (para <companion>).html` in the patient's folder as the model).
3. Convert with Edge headless, verify it stays within **≤ 2 pages** and look at both rendered pages (headers that wrap badly, wrong page references).
4. Save in the **patient folder's root** as `AAAA-MM-DD Guía para la consulta de <specialty> (para <companion>).pdf` + `.html` source (the date is the appointment's). It is a **private family document**: it does not circulate and never goes into packages.
5. Register it in the patient's `00 Índice general.md` and send the PDF.

## Verification before delivery

- [ ] The exit card fits in two lines and names where it must be written and whom it must reach.
- [ ] No more than 3 questions; 2 and 3 are conditional; 1 connects with the next appointment on the route.
- [ ] The scenario table includes the "hands the decision to another doctor" case.
- [ ] Zero clinical guidelines quoted to the doctor, zero other doctors' opinions as authority, zero insurer proceedings/litigation in the office.
- [ ] Every "p. N" reference points at the real page of the current package.
- [ ] ≤ 2 pages, prints in black and white, archived with its source beside it and listed in the index.
