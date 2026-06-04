# NeuraCore Backend — Phase 0 & 1

## Quick Start

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY or ANTHROPIC_API_KEY

# 3. Start the server
uvicorn main:app --reload --port 8000
```

Server starts at **http://localhost:8000**

---

## Endpoints

### `GET /`
Health check.
```json
{ "status": "ok", "message": "NeuraCore API is running 🧠" }
```

### `POST /api/upload`
Upload a curriculum file and get curriculum atoms back.

**Accepted formats:** PDF, DOCX, TXT, MD  
**Max size:** 10 MB

**Request:** `multipart/form-data` with field `file`

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
    ...
  ]
}
```

---

## File Structure

```
backend/
├── main.py          # FastAPI app + CORS setup
├── config.py        # Settings loaded from .env
├── parser.py        # Document parsing + atom chunking
├── routers/
│   └── upload.py    # POST /api/upload endpoint
├── requirements.txt
└── .env.example
```

---

## What's Next (Phase 2)

- `POST /api/transform` — accepts an atom + cognitive profile, returns rewritten content
- Prompt templates for ADHD / Dyslexia / ASD profiles
- 5-question onboarding quiz on the frontend
