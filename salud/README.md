# Salud

Personalized, printable health reports (PDF, in Spanish) per family member, from lab results. Adapts recommendations to the patient's age (pediatric → elderly, with evidence-based screening de-intensification) and to the Colombian health system context (EPS).

## Installation

This agent is lightweight (no backend). It installs as part of the `Ntobon/agents` marketplace:
- **claude.ai** (web + mobile): Customize → Plugins → Add → Add marketplace → *Add from a repository* → `Ntobon/agents` → **Sync automatically** → Sync → Add.
- **Claude Code**: `claude plugin marketplace add Ntobon/agents` + `claude plugin install salud@ntobon-agents`.

## Usage

1. Create one Claude Project per family member (e.g. "Salud Papá") and upload their exams (PDF) there.
2. Say: **"hazme el informe de salud"** — the skill auto-detects identity, age, and prior reports from the project.
3. You get a PDF ready to read, print, or take to the doctor. When new exams arrive, ask for "el informe actualizado": it compares against the previous one and leads with what changed.

Each person's data lives in their Project (or in `local/personas/` when used in Claude Code) — never in this repo.

## What it does NOT do

It doesn't diagnose, doesn't replace a medical consultation, doesn't dose medication, doesn't extrapolate beyond the documents.
