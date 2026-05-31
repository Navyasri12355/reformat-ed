# NeuraCore — Hackathon Implementation Plan
**Adaptive Learning for Neurodivergent Students**
*Team: Navyasri Pulipati · Shreya Mohan · Ksheeraja K Adya · Dhruthi*

---

## Overview

The goal is to ship a working, demo-ready prototype that proves the core value proposition: **upload any curriculum file → get a personalised, neurodivergent-friendly version of it**. Resist the urge to build everything. Win on depth of one flow, not breadth.

---

## Phase 0 — Alignment & Setup (Hour 0–1)

### Goals
Lock in scope, divide responsibilities, and get every machine ready to code.

### Tasks
- Agree on the single demo scenario you will present (recommended: a teacher uploads a one-page science lesson → student with ADHD sees it as a gamified quest, student with dyslexia sees it audio-first)
- Assign roles: **Backend/AI lead**, **Frontend lead**, **Prompt engineering lead**, **Demo/pitch lead** (can overlap)
- Create a shared GitHub repo with a monorepo structure: `/backend`, `/frontend`, `/prompts`
- Set up a shared `.env` file with the OpenAI API key (or switch to Claude API — same pattern)
- Stand up a basic FastAPI skeleton and a Create React App / Vite project

### Milestone ✅
Everyone has cloned the repo, the API returns `"hello world"`, and roles are clear.

---

## Phase 1 — Document Ingestion (Hour 1–3)

### Goals
Accept a file upload and extract clean, structured text from it.

### Tasks
- Build a `/upload` endpoint in FastAPI that accepts PDF, DOCX, and plain text
- Use **PyMuPDF** (`fitz`) for PDF text extraction — simpler than Tika for a hackathon
- Use **python-docx** for DOCX parsing
- Strip boilerplate (headers, footers, page numbers) with basic regex
- Break extracted text into **curriculum atoms**: paragraphs or logical sections of ~100–200 words each
- Return a JSON list of atoms with a simple ID and raw text field

### Cut for now
Bloom's taxonomy tagging, subject/grade classification, OCR for scanned PDFs (assume digital files in the demo)

### Milestone ✅
Uploading a sample PDF returns a clean JSON array of text chunks in under 5 seconds.

---

## Phase 2 — Cognitive Profile & Prompt Routing (Hour 3–5)

### Goals
Capture the student's neurodivergent profile and route each curriculum atom to the right prompt template.

### Tasks
- Build a **5-question onboarding quiz** on the frontend (hardcode the questions; no DB needed yet)
  - Example: "Do you prefer listening over reading?", "Do you like tasks broken into small steps with clear goals?"
- Map quiz answers to a simple profile object: `{ adhd: 0.8, dyslexia: 0.3, asd: 0.2 }` (weights sum to 1 or are independent — either works)
- Write **three prompt templates** (this is the core IP, spend real time here):
  - **ADHD prompt**: rewrite content as a short gamified challenge with a clear goal, one mission at a time, and a progress marker
  - **Dyslexia prompt**: rewrite as short sentences, plain language, no jargon, formatted for word-by-word reading; include a note to the UI to enable audio
  - **ASD prompt**: rewrite as a structured, numbered, predictable layout; no idioms, no ambiguous language, explicit signposting ("First… Next… Finally…")
- For blended profiles, pick the **dominant trait** (highest weight) for the hackathon — multi-modal blending can be a future milestone
- Build a `/transform` endpoint that accepts an atom + profile and calls GPT-4o with the right prompt

### Milestone ✅
Posting a paragraph + a profile object returns three meaningfully different rewrites, each clearly suited to its profile.

---

## Phase 3 — Frontend Student View (Hour 5–8)

### Goals
A clean, functional UI where a student can see their personalised content.

### Tasks
- Build two screens: **Teacher upload view** and **Student learning view**
- Teacher view: drag-and-drop file upload + a "processing" spinner
- Student view: render the transformed atom content according to profile
  - **ADHD**: card with a bold mission title, progress bar (fake it with static HTML for demo), chunked bullet points
  - **Dyslexia**: large OpenDyslexic font (load from Google Fonts or CDN), wide line spacing, a "Listen" button that calls `window.speechSynthesis` (browser built-in, zero setup)
  - **ASD**: white background, numbered steps, zero decorative elements, clear section labels
- Add the **5-question quiz flow** before the student view renders
- Wire the frontend to the `/upload` and `/transform` API endpoints

### Cut for now
Real auth, multiple students, educator review queue, passive signal tracking

### Milestone ✅
A judge can upload a file, complete the quiz as an ADHD student, and see a visually distinct gamified version of the content.

---

## Phase 4 — Polish & Demo Hardening (Hour 8–10)

### Goals
Make the demo resilient, fast, and persuasive. A broken demo kills good ideas.

### Tasks
- Pre-load a **known-good demo file** (a one-page excerpt from a public domain science textbook) so you never fumble with uploads during the pitch
- Cache the API response for that file so the demo works even if the internet drops
- Add loading states and error messages everywhere (network errors should not show blank screens)
- Make all three profile views accessible from a **toggle/switcher** so judges can flip between ADHD/Dyslexia/ASD instantly — this is your most powerful demo moment
- Do a full run-through with someone outside the team; time it; cut anything that adds friction
- Record a 60-second screen recording as a backup in case live demo fails

### Milestone ✅
The demo runs end-to-end in under 90 seconds with zero dead ends.

---

## Phase 5 — Pitch Preparation (Hour 10–12 / Final Hour)

### Goals
Tell the story as compellingly as the tech deserves.

### Narrative arc
1. **Hook** — "1 in 5 students is neurodivergent. Most EdTech still builds for the other 4."
2. **Problem** — 58% graduation rate, 65% never disclose, they fail because the format fails them
3. **Demo** — upload file, flip through three profiles live; let the UI speak
4. **How it works** — one slide: Ingest → Transform → Deliver (show the pipeline slide from your deck)
5. **Why now / why us** — LLMs make real-time curriculum rewriting feasible for the first time
6. **Ask / next steps** — what you'd build next (educator review queue, passive signal tracking, LMS integration via LTI 1.3)

### Roles
- One person drives the laptop during the demo
- One person narrates
- Keep it under 5 minutes; leave 2 minutes for questions

### Milestone ✅
Every team member can answer: "What's your biggest technical risk?" and "How do you ensure the AI output is accurate?"

---

## Backlog (If You Have Extra Time)

These are good but not essential for a winning hackathon demo. Tackle in this order if time allows:

1. **Educator review queue** — a simple table showing pending AI-generated content with an Approve button
2. **Passive signal tracking** — log time-on-page and button clicks to localStorage; show a fake "profile recalibration" graph
3. **Blended profiles** — when two traits are close in weight, merge the two prompt outputs using a second LLM call
4. **Audio playback** — for the dyslexia view, add word-by-word highlighting synced to `speechSynthesis` using `boundary` events
5. **LMS mockup** — a static screen showing the portal embedded inside a fake Google Classroom iframe

---

## Risk Register

| Risk | Likelihood | Mitigation |
|---|---|---|
| GPT-4o API is slow / rate-limited | Medium | Cache demo responses; use streaming for perceived speed |
| File parsing fails on complex PDFs | Medium | Use a simple, clean PDF as the demo file; test it early |
| Prompt output is inconsistent | High | Lock the prompt templates in Phase 2 and do not change them after Phase 3 begins |
| Frontend and backend integration breaks late | Medium | Integrate in Phase 3, not at the end; test with real API calls not mocks |
| Demo machine has no internet | Low | Pre-cache all API responses; have the screen recording ready |

---

## Tech Decisions for the Hackathon

| Layer | Hackathon Choice | Why |
|---|---|---|
| PDF parsing | PyMuPDF (`fitz`) | Simpler install than Apache Tika, no JVM needed |
| AI | GPT-4o via OpenAI SDK | Fast, reliable, great at instruction-following |
| Backend | FastAPI + Python | Fast to write, async-friendly |
| Frontend | React + Vite | Fast HMR, easy component structure |
| DB | None (in-memory dict) | No setup time; atoms live in server memory for the demo |
| Audio | Web Speech API | Zero dependencies, works in every modern browser |
| Fonts | OpenDyslexic via CDN | One CSS line, immediately visible impact |

---

*Ship the demo. Tell the story. The rest is a roadmap.*
