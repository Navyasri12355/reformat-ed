# NeuraCore — Adaptive Learning for Neurodivergent Students

> 1 in 5 students is neurodivergent. Curricula are built for the other 4.
> NeuraCore transforms **any** curriculum file into the format that matches how
> each student actually learns — instantly, for every brain.

A teacher uploads a textbook chapter, syllabus or lesson plan. NeuraCore reads
it, breaks it into **curriculum atoms**, and rewrites each atom into the format
that fits the student's cognitive profile:

| Trait | Format | What the student gets |
|-------|--------|------------------------|
| **ADHD** | `adhd_gamified` | Short gamified challenges, a clear goal, a progress bar |
| **Dyslexia** | `dyslexia_audio` | Audio-first, dyslexia-friendly font, word-by-word highlighting |
| **ASD** | `asd_structured` | Structured, predictable, low-stimulation, numbered steps |
| Blend | `blended` | A coherent mix for students with overlapping traits |

A short onboarding quiz sets the profile; educators can adjust it any time. As
students use the platform, passive signals (session length, retries, exit
points) **quietly recalibrate the profile** over time.

---

## 👀 What each learner profile gets (live in the app)

Every lesson segment is reframed by the LLM and rendered with profile-specific
support and **concept-explaining visuals** (a subject illustration + an
interactive Mermaid concept map per segment):

- **Dyslexia** → OpenDyslexic font, colour-coded syllables, highlighted key
  words, chunked + numbered sections, click-to-listen audio.
- **ADHD** → micro-segments with one explicit goal, a visual anchor before each,
  progress, a 1-question micro-poll, and floating **Pomodoro timer**,
  **distraction-free mode** (press <kbd>F</kbd>) and a **sticky-note pad**.
- **ASD** → numbered visual schedule, identical schedule→content→summary→quiz
  template, **idioms flagged and rewritten literally**, a "show me a real-world
  example" button, rubric shown *before* the task, and zero autoplay/flashing.

A **dark-mode toggle** is available everywhere. Architecture diagrams (system
flow, sequence, class, state — Mermaid/UML) are in
**[`docs/diagrams.md`](docs/diagrams.md)**.

---

## What's in this repo

```
backend/    FastAPI + SQLAlchemy + the full AI pipeline (ingest → transform → adapt)
frontend/   React PWA (Vite + TypeScript): quiz, learning session, educator dashboard
prompts/    Versioned YAML prompt templates (backend/prompts/1.0.0/)
docker-compose.yml   Production-flavoured stack (Postgres + Redis + Celery)
```

### Built and working end-to-end
- **Document ingestion** — PDF / DOCX / PPTX / TXT parsing → NLP atomisation
  (sentence segmentation, Bloom's-level + subject classification, Flesch–Kincaid
  grade banding, reading-time estimate).
- **Cognitive profile engine** — 10-question weighted onboarding quiz mapped to
  ADHD / dyslexia / ASD trait weights.
- **AI transformation engine** — profile-driven format selection, versioned
  prompt templates, an output validator, and a **deterministic local
  transformer** so the whole product runs with **no API key** (OpenAI is used
  automatically when `OPENAI_API_KEY` is set).
- **Educator review queue** — no transformed content reaches a student until an
  educator approves it (or institution-level auto-approval is enabled).
- **Adaptive feedback loop** — append-only behavioural signals + a Bayesian-style
  weekly recalibration with full profile-snapshot history.
- **Frontend** — auth, onboarding quiz, four format renderers (with Web Speech
  TTS + word highlighting), passive signal tracking, educator upload / review /
  analytics.
- **Integrated accessibility features** (live in the React app, fed by the
  backend's structured `meta` from `services/enrich.py`):
  - *ADHD* → visual anchor + single explicit goal per micro-segment, a
    one-question micro-poll that gates completion, and floating **Pomodoro**,
    **distraction-free mode** (press <kbd>F</kbd>) and **sticky-note pad**.
  - *Dyslexia* → OpenDyslexic font, colour-coded syllables, **keyword highlights
    driven by the backend**, chunked + numbered sections, per-chunk audio.
  - *ASD* → numbered schedule, **idioms flagged + rewritten literally**,
    real-world example button, and a rubric shown before the task.
  - All verified end-to-end in the running app for ADHD, Dyslexia and ASD.
- **Meaningful questions** — the check after each segment is a real
  **fill-in-the-blank (cloze)** built by removing a key word from a sentence in
  the segment, with distractors drawn from the *same subject* (so every option
  is plausible and the question is answerable purely from reading).
- **Pictures + concept maps in the lesson** — each segment shows an inline SVG
  illustration (subject-themed) and a per-segment **Mermaid concept map**
  generated from the segment's key terms (lazy-loaded, collapsible).
- **Per-profile voice (Coqui TTS)** — `services/tts.py` defines a distinct voice
  per profile (dyslexia = slow & clear, ADHD = bright & faster, ASD = calm &
  steady). Audio is synthesised server-side by **Coqui TTS** when installed
  (`pip install TTS`, modulated with librosa), and otherwise spoken by the
  browser voice using the *same* rate/pitch — so the modulation is identical
  either way. `GET /tts/profile`, `POST /tts/audio`.
- **Concept-explaining visuals in every lesson** — a subject SVG illustration
  plus an interactive (zoom/pan) Mermaid concept map generated per segment
  (`Illustration.tsx`, `ConceptDiagram.tsx`).
- **Tests** — backend tests (incl. a full upload→deliver→signal e2e) and a
  frontend unit + build check, all green.

### Deferred (documented, not built)
LTI 1.3 launch, Kubernetes/Helm, Pinecone vector search and ClickHouse
analytics from the original plan are intentionally **not** implemented — they
require paid external services and can't run locally. The architecture leaves
clean seams for them (e.g. the storage layer mirrors an object store; the task
runner already supports Celery).

---

## Deployment

### Frontend on Vercel
- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- Environment variable:
  - `VITE_API_BASE_URL=https://your-render-backend.onrender.com`

The repository includes a root `vercel.json` SPA rewrite. If you deploy only the
`frontend` directory as a separate Vercel project, add an equivalent rewrite in
Vercel project settings so React Router routes resolve to `index.html`.

### Backend on Render
- Use the included `render.yaml`, or create a Web Service manually with:
  - Root directory: `backend`
  - Build command: `pip install -r requirements.txt`
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Required environment variables:
  - `DATABASE_URL`
  - `JWT_SECRET`
- Optional environment variables:
  - `OPENAI_API_KEY`
  - `OPENAI_BASE_URL`
  - `OPENAI_MODEL`
  - `AUTO_APPROVE_ALL=true`
  - `CORS_ORIGINS=["https://your-vercel-app.vercel.app"]`

Recommended for Render:
- `TASK_BACKEND=inline`
- Postgres database attached via `DATABASE_URL`
- persistent disk if you want uploaded document storage to survive redeploys

## Quick start (no Docker, no API key, no Redis)

The defaults use **SQLite** + an **inline task runner** + the **local
transformer**, so it runs anywhere with just Python and Node.

### 1. Backend

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe seed_demo.py            # creates demo login credentials
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

API docs: <http://localhost:8000/docs> · Health: <http://localhost:8000/health>

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open <http://localhost:3000>. The dev server proxies `/api` → `localhost:8000`.

### Demo credentials (from `seed_demo.py`)
- **Educator:** `teacher@neuracore.demo` / `password123`
- **Student:** `student@neuracore.demo` / `password123`

### Demo flow
1. Log in as the **educator** → upload a PDF/DOCX/PPTX/TXT → watch it parse.
2. Log in as the **student** → take the quiz (or use the seeded profile) →
   "Prepare for me" on the lesson.
3. Back as the **educator** → **Review queue** → approve the transforms.
4. As the **student** → "Start learning" → step through the adapted atoms.
   Signals are recorded as you go; **View analytics** shows them to the educator.

**Shortcut — jump straight into one profile.** With the backend running:

```powershell
cd backend
.\.venv\Scripts\python.exe scripts\seed_live_demo.py asd   # or: adhd | dyslexia
```

It uploads a sample lesson, builds a profile, transforms and approves the
content, then prints a `document_id` + student tokens so you can open
`/learn/<document_id>` directly.

---

## Using real LLM transforms (optional)

Set an OpenAI key and the transform engine switches from the local rule-based
generator to GPT-4o automatically — no code change:

```powershell
$env:OPENAI_API_KEY = "sk-..."
# then start the backend as above
```

Every LLM output still passes through the same validator, with a strict retry
and a guaranteed local fallback if validation fails. The interactive scaffolding
(cloze question, concept map, illustration, idioms, rubric) is computed
deterministically from the source atom, so it is identical and correct on either
path.

---

## Enabling server-side Coqui TTS (optional)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install TTS librosa
# first run downloads the model (hundreds of MB)
```

With `TTS` installed, `POST /tts/audio` returns WAV synthesised by Coqui and
modulated per profile (dyslexia slower, ADHD brighter/faster, ASD calmer). Without
it, the endpoint returns 503 and the frontend automatically uses the browser
voice with the same rate/pitch — so per-profile modulation works regardless.

## Frictionless single-user demo

The educator review queue means a student's prepared content needs approval
before they can see it. For a solo walkthrough (no second account), start the
backend with auto-approve so **Prepare for me → Start learning** works directly:

```powershell
cd backend
$env:AUTO_APPROVE_ALL = "true"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

---

## Running the production-flavoured stack (Postgres + Redis + Celery)

```bash
docker compose up --build
```

This switches `TASK_BACKEND=celery`, runs separate ingestion / transform / adapt
workers and a Beat scheduler (weekly profile recalibration), and serves the
built frontend on port 3000.

---

## Tests

```powershell
# Backend
cd backend; .\.venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend; npm run test
```

---

## Architecture notes

- **Separation of ingestion and transformation.** Atoms are stored raw; the same
  content can be re-transformed as prompt templates improve, without re-parsing.
- **Educator review is a delivery-layer gate.** Students only ever fetch
  `approved` / `auto_approved` atoms — enforced in the content endpoint.
- **Signals are append-only.** `session_events` is insert-only; recalibration
  reads it but never mutates it, and snapshots every profile change for audit.
- **Format selection** lives in `services/prompt_router.py`: the dominant trait
  picks the format, with a blended mode when the top two traits are close and a
  safe structured default when no trait is strongly expressed.

See the in-code docstrings for each service for the precise logic.
