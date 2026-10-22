---
name: job-search
description: Search technology jobs and relevant recruiters using the professional profile provided in the session. Use when the user wants job opportunities, recruiters, or both.

disable-model-invocation: true
icon: briefcase
color: blue
---

# Job search (technology vacancies and recruiters)

## Goal

Find current professional opportunities and relevant recruiters for the user's profile. Do not invent information, and do not turn the search into a huge list. Do not show recruiters the user is already connected with, or recruiters already suggested earlier. Always look for new vacancies and recruiters. Before presenting a vacancy, confirm that it is still open.

Always return at most:

- 10 vacancies
- 10 recruiters

If fewer results are truly relevant, return fewer. Never pad the list with weak results just to reach 10.

## Professional profile source

Do **not** embed a fixed personal profile in this skill.

Before searching, obtain the active professional profile from, in order:

1. The current session (what the user states now)
2. A short clarifying question if profile data is still missing

Use only skills, stack, seniority, languages, and location constraints
that are present in that profile context. Do not invent seniority,
certifications, languages, or experience.


## Search rules

### 1. Search current vacancies

Search the web for open, recent vacancies related to the profile.

Prioritize:

1. Backend Engineer
2. Software Engineer
3. Full Stack Engineer
4. Node.js / TypeScript Engineer
5. NestJS / React / React Native when there is a fit
6. Go Engineer
7. AI Engineer / AI Software Engineer
8. AI Agent Engineer / LLM Engineer
9. Applied AI / AI Platform Engineer
10. Solutions/Platform Engineer when there is a strong technical fit

Combine search terms in Portuguese and English.

Prefer:

- recently published vacancies;
- vacancies that are still open;
- CLT or PJ hiring, or the local equivalent, when that is clearly stated;
- remote work, or a location compatible with the user;
- identifiable companies and career pages;
- vacancies whose stack and responsibilities actually fit the profile.

Avoid:

- expired vacancies;
- duplicate results;
- aggregators that hide the original vacancy when a primary source exists;
- generic IT vacancies with no relation to the profile;
- vacancies that require technologies completely outside the profile, with no relevant overlap.

### 2. Search recruiters

Search for people who publicly work as:

- Tech Recruiter
- Talent Acquisition
- Technical Recruiter
- IT Recruiter
- Engineering Recruiter
- Talent Partner
- People or recruitment specialists focused on technology

Prioritize recruiters who:

- currently hire for technology roles;
- recruit for companies compatible with the profile;
- publish engineering, software, or AI vacancies;
- are in Brazil, or hire for remote roles that accept professionals in Brazil.

Do not collect or expose private personal data. Use only public professional information.

### 3. Validation

For each result, confirm the following from the source that was found:

- title;
- company;
- location or remote;
- date, or another sign that the listing is current, when available;
- source link;
- why it is relevant to the profile.

If a fact cannot be confirmed, write "not informed" instead of inferring it.

### 4. Deduplication

Do not show the same vacancy more than once, even when it appears on several sites.

When the company has an official page for the same vacancy, prefer the official source.

## Response format

Start with:

"Found X relevant vacancies and Y relevant recruiters."

### Vacancies

Table:

| # | Vacancy | Company | Location/Remote | Fit | Source |
|---|---|---|---|---|---|

In "Fit", use a short factual description, for example:

- "Node.js + TypeScript + AWS"
- "AI Agents + LLM + Python"
- "Backend + distributed systems"

Do not use scores, stars, or a ranking.

### Recruiters

Table:

| # | Recruiter | Role | Company | Focus | Profile |
|---|---|---|---|---|---|

In "Focus", state the kind of hiring that was observed.

## Important

- Do not invent vacancies, recruiters, companies, dates, or requirements.
- Do not claim a vacancy is open without current evidence.
- Do not present a vacancy as "better" or "more recommended". Explain the factual fit only.
- Do not contact anyone, apply, or send messages automatically.
- This skill researches and presents opportunities so the user can decide what to do.
- If the search finds many options, limit the result strictly to 10 vacancies and 10 recruiters.
- If a search does not find enough results, run new queries with equivalent terms before concluding.
- Record the search date at the end.
