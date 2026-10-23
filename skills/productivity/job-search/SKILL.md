---
name: job-search
description: >-
  Search technology jobs and relevant recruiters using the professional profile
  provided in the session. Use when the user wants job opportunities, recruiters,
  or both.
disable-model-invocation: true
icon: briefcase
color: blue
---

# Job search (technology vacancies and recruiters)

Find current opportunities and recruiters for the session profile. Do not invent
data. Cap at 10 vacancies and 10 recruiters. Confirm vacancies are still open.
Skip recruiters already connected or previously suggested.

## Professional profile source

Do **not** embed a fixed personal profile. Obtain profile from the current
session, then a short clarifying question if needed. Do not invent seniority,
certifications, languages, or experience.

## Workflow (thin orchestrator)

1. Search rules, vacancy/recruiter criteria, validation, deduplication, response tables → [references/search-rules-and-format.md](references/search-rules-and-format.md)
2. Execute web search; return factual fit only (no scores/stars).
3. Record the search date at the end.

## Important

- Do not invent vacancies, recruiters, companies, dates, or requirements
- Do not contact anyone or apply automatically
- Prefer fewer strong results over padding to 10

## Token economy

Keep the injectable surface small. Load the search-rules reference once per run;
do not paste entire result pages into the skill context.
