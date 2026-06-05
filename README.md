# Adaptive Learning Platform for Neurodivergent Students

**Empowering neurodivergent learners through AI-powered, personalized curriculum transformation.**

---

## About

This project is a full-stack platform that:
1. **Ingests** curriculum files (PDF, DOCX, TXT)
2. **Extracts** logical content chunks (curriculum atoms)
3. **Transforms** content for three cognitive profiles:
   - **ADHD**: Gamified, mission-based, short bursts with rewards
   - **Dyslexia**: Large fonts, simple language, audio-ready
   - **ASD**: Structured, numbered, literal, predictable

Teachers upload once. Students see content tailored to their learning profile.

---

## Quick Start

### Backend Setup

```bash
cd backend

# 1. Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add:
#   OPENAI_API_KEY=sk-...

# 4. Start the server
uvicorn main:app --reload --port 8000
```

**Backend:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start dev server
npm run dev
```

**Frontend:** http://localhost:5173

---

## API Endpoints

### Health Check
```bash
GET /
```
```json
{
  "status": "ok",
  "message": "API is running 🧠",
  "version": "1.0.0",
  "endpoints": {
    "upload": "POST /api/upload",
    "transform": "POST /api/transform",
    "batch_transform": "POST /api/transform/batch"
  }
}
```

### Upload Curriculum Files
```bash
POST /api/upload
```

**Request:** `multipart/form-data` with field `file`
- Accepts: PDF, DOCX, TXT, MD
- Max size: 10 MB

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@lesson.pdf"
```

**Response:**
```json
{
  "filename": "lesson.pdf",
  "atom_count": 5,
  "atoms": [
    {
      "id": "atom_001",
      "text": "The human brain contains approximately 86 billion neurons...",
      "word_count": 142
    },
    {
      "id": "atom_002",
      "text": "Neurons communicate through synaptic connections...",
      "word_count": 118
    }
  ]
}
```

### Transform Content by Profile
```bash
POST /api/transform
```

**Request:**
```json
{
  "atom_id": "atom_001",
  "text": "The human brain contains approximately 86 billion neurons.",
  "profile": "adhd"
}
```

**Response:**
```json
{
  "atom_id": "atom_001",
  "profile": "adhd",
  "original_text": "The human brain contains approximately 86 billion neurons.",
  "rewritten_text": "🎯 MISSION: DISCOVER THE BRAIN'S NEURAL NETWORK\nStep 1 › The brain has about 86 BILLION tiny brain cells.\n⚡ XP EARNED: +25 XP — Neuroscience Novice"
}
```

### Batch Content Transformation
```bash
POST /api/transform/batch
```

**Request:**
```json
{
  "atoms": [
    {"id": "atom_001", "text": "..."},
    {"id": "atom_002", "text": "..."}
  ],
  "profile": "dyslexia"
}
```

**Response:**
```json
{
  "results": [
    {
      "atom_id": "atom_001",
      "profile": "dyslexia",
      "original_text": "...",
      "rewritten_text": "..."
    }
  ],
  "count": 2
}
```

---

## Project Structure

### Backend (Python + FastAPI)

```
backend/
├── main.py                    # Unified entry point
├── requirements.txt
├── .env.example
├── api/
│   ├── __init__.py
│   └── routes/
│       ├── __init__.py
│       ├── upload.py          # Document parsing and ingestion
│       └── transform.py       # Content transformation by profile
│
└── core/
    ├── __init__.py
    ├── config.py              # Settings from .env
    ├── parsers/
    │   ├── __init__.py
    │   └── document.py        # PDF, DOCX, TXT extraction
    ├── transformers/
    │   ├── __init__.py
    │   └── cognitive.py       # OpenAI/Anthropic calls
    ├── prompts/
    │   ├── __init__.py
    │   └── templates.py       # ADHD, Dyslexia, ASD prompts
    └── models/
        ├── __init__.py
        └── schemas.py         # Pydantic validation models
```

### Frontend (React + Vite)

```
frontend/
├── index.html
├── vite.config.js
├── package.json
└── src/
    ├── main.jsx               # React entry point
    ├── App.jsx                # Router component
    ├── styles.css             # Global styles
    ├── pages/                 # Full-page components
    │   ├── TeacherLogin.jsx
    │   ├── StudentLogin.jsx
    │   ├── TeacherDash.jsx    # Upload & manage
    │   ├── Quiz.jsx           # Profile assessment
    │   ├── ADHDDash.jsx       # ADHD-friendly view
    │   ├── DyslexiaDash.jsx   # Dyslexia-friendly view
    │   └── ASDDash.jsx        # ASD-friendly view
    ├── components/            # Reusable UI (future)
    ├── utils/
    │   ├── api.js             # Backend HTTP client
    │   └── helpers.js         # Profile utilities
    ├── hooks/                 # Custom hooks (future)
    └── styles/
        └── theme.js           # Design tokens
```

---

## Cognitive Profiles

### ADHD-Friendly (Missions)
- **Goal:** Combat attention fatigue with gamification
- **Format:** 
  - Bold mission title: `🎯 MISSION: DISCOVER CELLULAR ENERGY`
  - 3-6 short mission steps
  - Progress tracking: `⚡ XP EARNED: +50 XP`
- **Language:** Action-oriented, energetic, no jargon

### Dyslexia-Friendly (Audio)
- **Goal:** Reduce cognitive load for reading
- **Format:**
  - Large OpenDyslexic font
  - Short sentences (max 12 words)
  - One idea per line, wide spacing
  - "Listen" button for text-to-speech
- **Language:** Simple, plain words, no metaphors

### ASD-Friendly (Structured)
- **Goal:** Provide predictability and clarity
- **Format:**
  - Strict numbered structure:
    - Topic: [single sentence]
    - 1. [fact]
    - 2. [fact]
    - ...
    - Summary: [closing sentence]
  - Explicit transitions: "First," "Next," "Finally,"
- **Language:** Literal, concrete, unambiguous

---

## Configuration

Create a `.env` file in `backend/`:

```bash
# Required: Choose one AI provider
OPENAI_API_KEY=sk-your-openai-key
# OR
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key

# Optional
MODEL=gpt-4o
# or: claude-3-5-sonnet-20241022

# Optional
CORS_ORIGINS=*,http://localhost:5173
```

---

## User Flows

### Teacher Flow
1. Login with email/password
2. Upload PDF/DOCX → Backend extracts atoms
3. Auto-transform → ADHD, Dyslexia, ASD versions generated
4. Review queue → Approve AI-generated content
5. Publish → Students access personalized curriculum

### Student Flow
1. Login with name (optional: class code)
2. Option A: Take 5-question quiz → Profile determined
3. Option B: Skip if already diagnosed → Select profile
4. Dashboard → View curriculum in personalized format
5. Learn → ADHD students see missions, Dyslexia students get audio, ASD students see structure

---

## Testing

### Backend
```bash
# Health check
curl http://localhost:8000/

# Upload test
curl -X POST http://localhost:8000/api/upload \
  -F "file=@sample.pdf"

# Transform test
curl -X POST http://localhost:8000/api/transform \
  -H "Content-Type: application/json" \
  -d '{
    "atom_id": "a1",
    "text": "Hello world",
    "profile": "adhd"
  }'
```

### Frontend
- Visit http://localhost:5173
- Teacher: Login → Upload PDF → See transformation
- Student: Login → Take quiz → View dashboard

---

## Development

### Adding a New Parser
```python
# backend/core/parsers/custom.py
def extract_text_from_custom(data: bytes) -> str:
    # Your extraction logic
    return text

# Update __init__.py
from .custom import extract_text_from_custom
```

### Adding a New Prompt Template
```python
# backend/core/prompts/templates.py
MY_PROFILE_SYSTEM = """Your system message here"""
_SYSTEM_MESSAGES["my_profile"] = MY_PROFILE_SYSTEM
```

### Adding a Student Dashboard
```jsx
// frontend/src/pages/MyProfileDash.jsx
export default function MyProfileDash({ studentName, atoms }) {
  // Your component
}

// Update App.jsx to add route
if (screen === 'my_profile')
  return <MyProfileDash ... />
```

---

## Documentation

- **[INTEGRATION_COMPLETE.md](./INTEGRATION_COMPLETE.md)** — What was reorganized
- **[REORGANIZATION_GUIDE.md](./REORGANIZATION_GUIDE.md)** — Detailed structure
- **[README_NEW.md](./README_NEW.md)** — Alternative quick start
- **API Docs:** http://localhost:8000/docs (Swagger/OpenAPI)

---

## Troubleshooting

### Backend won't start
```bash
python --version  # Should be 3.9+
pip list | grep fastapi
cat backend/.env  # Verify OPENAI_API_KEY is set
```

### Upload returns 400
- Check file size (max 10 MB)
- Verify format (PDF, DOCX, TXT)
- Check backend logs

### Transform returns 503
- Verify API key in `.env`
- Check API key validity
- Verify network connectivity

### Frontend won't connect
- Verify backend is running on port 8000
- Check CORS in `backend/core/config.py`
- Verify VITE_API_BASE in frontend `.env`

---

## Dependencies

### Backend
- FastAPI 0.100+
- PyMuPDF (fitz)
- python-docx
- pydantic
- openai
- anthropic

### Frontend
- React 18+
- Vite 4+

---

## What's Included

**Document Processing**
- PDF, DOCX, TXT parsing with PyMuPDF and python-docx
- Boilerplate stripping (headers, footers, page numbers)
- Smart chunking into curriculum atoms (60-200 words)

**Content Transformation**
- OpenAI GPT-4o and Anthropic Claude support
- Three cognitive profile templates (ADHD, Dyslexia, ASD)
- Single and batch transformation endpoints
- Personalized content generation at scale

**Web Interface**
- Teacher dashboard with file upload and content review
- Student login with cognitive profile assessment
- Three profile-specific content viewers
- Responsive design for all devices

**Backend Architecture**
- Semantic folder organization (parsers, transformers, prompts, models)
- Type-safe Pydantic validation
- CORS-enabled for frontend integration
- Auto-generated OpenAPI documentation

---

## Next Steps

1. Start backend: `uvicorn main:app --reload` 
2. Start frontend: `npm run dev`
3. Visit http://localhost:5173
4. Teacher login → Upload a PDF
5. See atoms extracted and transformed
6. Student login → Complete quiz → View personalized dashboard

---

## License

MIT

---
