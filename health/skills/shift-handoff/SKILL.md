---
name: shift-handoff
description: Processes the end-of-shift handoff for a patient who is accompanied in shifts (hospitalized or at home). Takes the voice notes (or texts) the companion or caregiver sends over WhatsApp at the end of each shift, downloads them, transcribes them LOCALLY, archives them, extracts the clinical and logistical facts, records them in the care log, the day's clinical note and the index, checks them against open items, and drafts the summary and the questions for the next shift. Use when the user says "llegó el audio del turno", "transcribe el audio de…", "registra lo que dijo la cuidadora", "qué pasó en el turno de la noche", sends an "update de…" with audios, or pastes a companion's account.
---

# Shift handoff

## Purpose

When a patient spends the day accompanied in shifts (family, hired caregivers), what happens in each shift arrives as **WhatsApp voice notes** at the end of the shift: who came by, what the patient ate, what was done, what the doctors said. If nobody brings it into the record it gets lost across chats, and what was not asked in one shift is not asked in the next. This skill closes that loop: **audio → local transcription → record → questions for the next shift**.

It is **agnostic**. It carries no names, chats or phone numbers: it takes them from the **"Relevo de turnos"** (shift handoff) section of the patient's `CLAUDE.md` (template at the end). If the section does not exist, ask the minimum and offer to create it.

## Hard limits

1. **Always ask which chat to read**, even when the context names a default: propose the configured one and wait for a yes. WhatsApp chats are personal; never open another chat on your own initiative (if the chat list shows a message from another contact that looks relevant, mention it and ask).
2. **Confirm the audios before downloading them.** List what was found (sender, time, duration; if forwarded, from whom) and wait for a yes. Download only what was confirmed.
3. **Local transcription only** (`scripts/transcribe.py`, Whisper on the machine). The audios contain health data: never upload them to external transcription services.
4. **Nothing is sent without confirmation.** The questions for the next shift are shown with the exact text and recipient; they are sent only after an explicit yes to that message.
5. **An audio is an account, not a document.** Record it as "reported by <who>", with time and source; if the transcription is doubtful, say so ("unclear audio") instead of filling in. Never invent a value (blood pressure, dose, drug name) the audio does not state.
6. **Separate facts from management** (folder policy): the day's clinical note carries clinical facts only; shifts, who is with the patient, impressions and tactics go to the care log.
7. **Originals are untouched:** the raw audio is archived as is; the transcription goes next to it.

## The handoff

### 0. Context

Read from the patient's folder: `CLAUDE.md` ("Relevo de turnos" section), `00 Índice general.md` (status line and open items), the care log of the hospitalization or home care (today's entries and the **"Por aclarar"** — to clarify — list) and the day's clinical note in `02 - Historia clínica\`. Knowing which questions were asked in the previous shift is what lets you mark which ones got answered.

### 1. Chat and audios

1. Propose the chat ("¿Leo el chat con <X>?") and wait for a yes.
2. Open WhatsApp Web in the user's browser (Chrome extension) and the confirmed chat. Read everything after the last entry recorded in the care log: texts and audios.
3. List what was found and ask for confirmation: `3:21 pm · <sender> · 0:54` · `3:23 pm · <sender> · 0:31`. Chat texts are read without downloading anything, but they are recorded too.

### 2. Download and archive

- **Downloading a voice note in WhatsApp Web:** hover over the bubble → the ˅ arrow at its top-right corner → "Download" ("Descargar" in Spanish). It lands in the downloads folder as `WhatsApp Ptt YYYY-MM-DD at H.MM.SS PM.ogg`. Verify it arrived before moving to the next one. If the menu does not open, hover again and click right on the arrow.
- **Archive:** copy (do not move) to `06 - Originales\<year>\audios <context>\` named `YYYY-MM-DD HH.MM Audio de <who> (turno <mañana|tarde|noche>) <n> de <m>.ogg`. Check it does not exist before copying.

### 3. Transcribe

```
python scripts/transcribe.py "<audio 1>" "<audio 2>" --out "<folder>\YYYY-MM-DD HH.MM-HH.MM Audios de <who> (turno X) - transcripción.md"
```

Uses `large-v3`; tries GPU and falls back to CPU if CUDA is missing (on CPU, ~1-3 min per minute of audio). The first run downloads the model (~3 GB). Complete the `.md` with a header (patient, speaker, time, what it answers) and, at the end, **the "question → answer" table** if the audio was answering questions that were sent. The model's text stays literal; corrections go in the table, not in the transcription.

### 4. Extract

Run the account through this checklist. What was not mentioned stays as "no data", never as "normal".

| Item | What to look for |
| --- | --- |
| Who and when | Companion, arrival and departure time, who takes the next shift |
| Vital signs | Blood pressure, pulse, temperature, glucose, oxygen saturation, with values if stated |
| Feeding | What was served, how much was eaten, tolerance, whether nutrition saw the patient |
| Fluids and output | What was drunk, IV fluids, urine, stool (color), vomiting |
| Procedures | Catheters (type and site), blood draws (how many punctures), wound care, imaging |
| Medications | Names, changes, chemotherapy (regimen, dose, start) |
| Doctor visits | Who came (specialty, name), what they said, what they ordered |
| Condition | Pain, sleep, mood, orientation, mobility, falls |
| Documents | What was handed over or received, what stayed in the institution's record |
| Questions | Which ones from the previous shift were answered and which were not |

**Warning signs, first in the reply and in the care log:** fever, persistent or bloody vomiting, black stools, bleeding, new severe pain, new confusion, a fall, shortness of breath, no urine during the shift, eating nothing for a whole shift, redness or pain at the catheter site. A warning sign is reported to the user immediately, before finishing the record.

### 5. Record

1. **Care log** (management): one row per event — time, who, what — with "(audio de <who>)" as the source. Update the "Por aclarar" list: close what was resolved with ✅ (keeping the reasoning) and open new items with their analysis.
2. **Day's clinical note** in `02 - Historia clínica\` (facts): a section for the shift with "Referido por <who> … por notas de voz (transcripción en 06)". Update "what is not in writing" and the plain-language summary.
3. **Index:** the day's status line with the essentials of the shift. Sweep every other place in the index that names a fact that changed.
4. Write atomically (temp file + replace) and in UTF-8. When building Windows paths in Python, use `chr(92)` for the separator: `"\2026"` in a normal string is an octal escape and corrupts the path.

### 6. Handoff to the next shift

- **Summary for the user:** question → answer table, what is new, and **what remains open, prioritized** (what is urgent and why). With clinical reasoning and sources when recommending something (critical-thinking policy).
- **Draft message** for whoever takes the next shift, in plain language: only what must be watched, requested or asked there, numbered, without repeating what is resolved. Show it with the recipient and wait for a yes.
- **Sending via WhatsApp Web (if approved):** `Shift+Enter` for line breaks (Enter sends). **WhatsApp auto-numbers lists:** type the number only on the first item (`1. …`); later items are typed without a number or they come out doubled ("2. 2."). Zoom in to check before sending and verify the ✓ afterwards.
- If a reply is expected, schedule a check of the chat (e.g. after 10-15 min) and, when it arrives, go back to step 1 with the same chat.

## Context template (section of the patient's `CLAUDE.md`)

```markdown
## Relevo de turnos

- **Chat por defecto:** <chat name as shown in WhatsApp> — <why: who consolidates the audios>. Always confirmed before reading.
- **Quiénes mandan relevos:** <names and role: family member, day caregiver, night caregiver>.
- **Turnos:** <schedule>.
- **Bitácora:** `<path to the care log>` · **Nota clínica del día:** `02 - Historia clínica\YYYY-MM-DD <name>.md`.
- **Audios archivados en:** `06 - Originales\<year>\audios <context>\`.
- **A quién va el relevo:** <who takes the next shift / who consolidates>.
- **Navegador:** <Chrome profile with WhatsApp Web and the extension>.
```
