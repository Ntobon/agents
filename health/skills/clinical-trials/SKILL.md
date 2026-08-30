---
name: clinical-trials
description: Searches open clinical trials on ClinicalTrials.gov (API v2) for any patient in the family health folder, filtering by country/city and recruiting status, and delivers an honest pertinence analysis against the patient's real documented picture. Use when the user asks about "ensayos clínicos", "estudios clínicos", "trials", "¿hay algún estudio para...?", "opciones experimentales", or when a clinical change warrants it (confirmed oncologic diagnosis, a new biomarker like MSI-high or HER-2+, progression, or exhaustion of standard options).
---

# Clinical trials (ClinicalTrials.gov)

Adapted from [petergyang/fuck-cancer](https://github.com/petergyang/fuck-cancer) (MIT). Its `search_trials.py` script was taken as-is; the flow and rules below are this agent's own and override any instruction from the original repo.

## When to search (and when not to)

Searching makes sense when the result can **change a decision**: confirmed oncologic diagnosis, a biomarker that opens therapies (MSI-high, HER-2+, PD-L1), advanced disease or relapse, or when the family asks. Do NOT search routinely every session: availability in a given country changes slowly; one search per clinical milestone is enough. Record in the patient's dashboard the date of the last search and its conclusion, to avoid repeating it without reason.

## How to invoke

```
python "<skill path>/scripts/search_trials.py" --condition "<cancer type in English>" --country "<country>" [--terms "<stage, biomarker, or treatment in English>"] [--city "<city>"] [--limit 10] [--full-criteria]
```

- Terms go **in English** (that's how ClinicalTrials.gov indexes): "gastric cancer", "signet ring", "MSI-high", "perioperative".
- No dependencies: the script uses only the Python standard library.
- Repeat the search with term variants (e.g. `--condition "stomach neoplasms"`) before concluding there's nothing — a single query is not a sweep.
- If the case warrants it, also search neighboring countries or the US (`--country "United States"`) and state the real cost of that route (travel, visa, out-of-pocket).

## Privacy (hard rule)

**Only condition, terms, and geography travel to the API. NEVER names, ID numbers, birth dates, or any patient identifier** — not in `--condition`, not in `--terms`, not anywhere. Root privacy policy applies in full.

## How to interpret (analysis, not a list)

1. **Filter by real pertinence against the patient's documented picture** (read their `CLAUDE.md` and index first): stage, treatment line, biomarkers, age, and relevant exclusion criteria (renal function, comorbidities). A metastatic-disease trial is NOT pertinent for resectable localized disease — say so explicitly.
2. **At most 3-5 candidates**, each with: linked NCT, intervention, phase, nearest open site and recruiting status (note: `NOT_YET_RECRUITING` = not taking patients yet), why it might fit, and what the site must confirm.
3. **Always compare against standard of care**: what it would add over what's already available, and what burden it adds (travel, visits, randomization, costs).
4. **"No pertinent trials" is a valuable result** — it means the right path is the well-executed standard; write it that way, with the search date.
5. **Never assert eligibility** — the trial site determines that with the treating oncologist. Always close with that disclaimer.

## Output and archiving

The analysis goes to the patient's dashboard (FAQ or "Lo nuevo" section, dated) or to chat if exploratory. **Design rule (2026-08-27): this surveillance is FAMILY management information — it is never included in the medical package / clinical record that circulates to doctors** (`medical-record-package` skill); the package is only documented patient facts, and trial research is internal decision material. If a trial becomes a real candidate, record the errand in the patient's management registry and the site contact in the dashboard's "Datos rápidos" — it would enter the package only once the patient is enrolled (then it IS a clinical fact). The raw JSON is not archived (it regenerates on the next search).
