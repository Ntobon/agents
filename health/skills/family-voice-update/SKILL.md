---
name: family-voice-update
description: Turns a status update, a day summary or any short report about a patient into a voice note and sends it to the family's WhatsApp group (or one relative) as a NATIVE voice note — waveform and play button, exactly like one recorded on a phone — never as a file attachment. The voice is synthesized locally with Kokoro, so health information never leaves the computer. Use when the user says "mándalo como audio", "envía una nota de voz", "haz un audio con el resumen", "cuéntales por audio", "mándale un audio al grupo", "dilo en un audio", or when an update for a family chat lands better heard than read.
---

# Family voice update

## Purpose

When a family coordinates a patient's care through a WhatsApp group — relatives, a case coordinator, and the owner's agents all feeding the same chat — the fastest way to keep everyone aligned is a short voice note: people listen while driving, at work, or at the hospital. This skill produces that note from the agent's own summary and drops it into the chat as if a person had recorded it.

Three steps: script → local voice (Kokoro) → native voice note in WhatsApp Web. **Never send the audio as a Document**: it arrives as an `.ogg` file people have to open, which defeats the point.

## Where the specifics live

Which chat to post in, who is in it, what the group's conventions are (e.g. "facts only", "don't assign tasks to named people"), which Chrome profile holds WhatsApp Web, and where audios are archived all live in the patient's `CLAUDE.md` (or the root context), never in this skill. If the chat is not defined there, ask once and record it.

## 1. Script

- Spoken, not read: short sentences, no bullets, no abbreviations or symbols. Numbers as they are said ("a la una y quince de la tarde", "el nueve de octubre"). Long numbers (filing numbers, IDs) do not go in the audio: say "les dejo el número en el chat" and send them in writing.
- Opens by saying who is speaking when the user asks for it (e.g. "Les habla el agente de …, con el resumen de hoy").
- Order: what happened → what was done → what helps now → what comes next. 45 s to 2 min (≈ 120-300 words).
- One paragraph per idea, separated by a blank line: the script adds a short pause between paragraphs.
- Same rules as a written message to that chat: facts only, no clinical alarmism, no tasks assigned to specific people unless the user asks, nothing the group's context forbids.
- Every claim must be true at sending time (do not say "we filed" before the filing exists). Show the script to the user or archive it next to the audio.

## 2. Local voice with Kokoro

- Engine: Kokoro-82M (ONNX). **Do not use cloud TTS (ElevenLabs or similar) for health content**: it ships the patient's information to a third party, and permission classifiers rightly block it. Kokoro sounds natural in Spanish.
- One-time setup: `pip install kokoro-onnx soundfile numpy` and download `kokoro-v1.0.onnx` and `voices-v1.0.bin` from the kokoro-onnx releases into `~/.cache/kokoro/` (or point `KOKORO_MODEL` / `KOKORO_VOICES` at them). Record the actual paths in the root context once installed.
- Spanish voices: `em_alex` (male, default) and `ef_dora` (female). Other languages: pass the voice and `lang` (see the kokoro-onnx voice list).
- Run: `python scripts/kokoro_tts.py script.txt note.wav [voice] [speed] [lang]`. Prints the duration. Upload the `.wav` in step 3 (it decodes reliably in the browser).
- If Python runs inside WSL and is called from Windows, write full paths inside `wsl.exe -- bash -lc '…'`: shell variables in that string are expanded (empty) by the WSL login shell before `bash -c` sees them.

## 3. Send as a native voice note (WhatsApp Web)

WhatsApp Web only creates voice notes by recording from the microphone. The technique: hand the page the audio as if it were the microphone, and record with WhatsApp's own button.

Browser: the user's Chrome with WhatsApp Web (Claude in Chrome), in the profile named in the context file. Steps:

1. **Open the right chat and verify it** before touching anything: `document.querySelector('#main header').innerText` must show the chat name. The chat list reorders itself — do not trust coordinates or stale refs, and never type before verifying (if something was typed into another chat, clear it before continuing).
2. **Inject an own file input**: run block 1 of `scripts/whatsapp_ptt.js` (creates `#claude-audio`), locate it with `find` ("file input with aria-label claude-audio-input") and upload the `.wav` with `file_upload`.
3. **Fake microphone**: run block 2 of `scripts/whatsapp_ptt.js`. It decodes the audio, replaces `navigator.mediaDevices.getUserMedia`, and schedules a click on "Send" ~0.7 s after the audio ends (no trailing silence). Returns the duration.
4. **Record**: click the chat's "Voice message" button. Check `window._voice.started`.
5. **Wait** the duration plus a few seconds (chain 10 s waits) and confirm `window._voice.sent === true` and that the last message shows the duration (e.g. "1:20").
6. Close the tab opened for the task.

Notes:
- If a recording is cancelled ("Cancel"), run block 2 again before recording.
- Pressing Send by hand after waiting by eye leaves seconds of silence at the end: always use block 2's automatic send.
- Posting to a chat is an outward action: do it only when the user asked to send to that chat.

## 4. Archive

Keep the `.wav` (or a light `.ogg`: `ffmpeg -i note.wav -c:a libopus -b:a 32k note.ogg`) and the script in the patient's raw-originals folder with date and time in the name, and log the send wherever the patient's context keeps its management log.

## Related

- `shift-handoff` is the reverse direction (voice notes from caregivers → transcribed record); both keep health audio local.
- `channel-monitoring` and `eps-status-package` produce the facts a voice update usually summarizes.
