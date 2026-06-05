"""
NeuraCore — Document Parsing Utilities
========================================
Handles PDF (PyMuPDF), DOCX (python-docx), and plain text.
Produces clean curriculum atoms — logical chunks of ~100-200 words.
"""
import re
import fitz          # PyMuPDF
from docx import Document
from io import BytesIO


# ---------------------------------------------------------------------------
# Low-level extractors
# ---------------------------------------------------------------------------

def extract_text_from_pdf(data: bytes) -> str:
    """Extract text from a PDF file given raw bytes."""
    parts = []
    with fitz.open(stream=data, filetype="pdf") as doc:
        for page in doc:
            parts.append(page.get_text())
    return "\n".join(parts)


def extract_text_from_docx(data: bytes) -> str:
    """Extract text from a DOCX file given raw bytes."""
    doc = Document(BytesIO(data))
    return "\n".join(para.text for para in doc.paragraphs)


def extract_text_from_txt(data: bytes) -> str:
    """Decode plain text bytes, trying common encodings."""
    for encoding in ("utf-8", "latin-1", "cp1252"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not decode text file with any known encoding.")


# ---------------------------------------------------------------------------
# Boilerplate stripping
# ---------------------------------------------------------------------------

_BOILERPLATE_PATTERNS = [
    r"^\s*page\s+\d+\s*(of\s+\d+)?\s*$",          # "Page 1 of 4"
    r"^\s*\d+\s*$",                                  # lone page numbers
    r"^[-=]{3,}\s*$",                                # divider lines
    r"^\s*(confidential|draft|internal use only)\s*$",  # common footers
]
_BOILERPLATE_RE = re.compile(
    "|".join(_BOILERPLATE_PATTERNS),
    flags=re.IGNORECASE | re.MULTILINE,
)


def strip_boilerplate(text: str) -> str:
    """Remove common headers, footers, and page numbers from extracted text."""
    lines = text.splitlines()
    cleaned = [line for line in lines if not _BOILERPLATE_RE.match(line)]
    return "\n".join(cleaned)


# ---------------------------------------------------------------------------
# Curriculum atom chunking
# ---------------------------------------------------------------------------

_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


def _split_into_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_END_RE.split(text) if s.strip()]


def chunk_into_atoms(
    text: str,
    min_words: int = 60,
    max_words: int = 200,
) -> list[dict]:
    """
    Break text into curriculum atoms — logical chunks of ~100-200 words.

    Strategy:
    1. Split on double newlines (paragraphs) first.
    2. If a paragraph is too long, split by sentences and accumulate.
    3. If a paragraph is too short, merge with the next.

    Returns a list of dicts: {id, text, word_count}
    """
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]

    atoms: list[str] = []
    buffer = ""

    def flush(buf: str) -> None:
        cleaned = " ".join(buf.split())
        if cleaned:
            atoms.append(cleaned)

    for para in paragraphs:
        para_words = len(para.split())

        if para_words > max_words:
            if buffer:
                flush(buffer)
                buffer = ""
            sentences = _split_into_sentences(para)
            for sentence in sentences:
                candidate = (buffer + " " + sentence).strip() if buffer else sentence
                if len(candidate.split()) >= min_words:
                    flush(candidate)
                    buffer = ""
                else:
                    buffer = candidate
        else:
            candidate = (buffer + "\n\n" + para).strip() if buffer else para
            if len(candidate.split()) >= min_words:
                flush(candidate)
                buffer = ""
            else:
                buffer = candidate

    if buffer:
        flush(buffer)

    return [
        {"id": f"atom_{i + 1:03d}", "text": atom, "word_count": len(atom.split())}
        for i, atom in enumerate(atoms)
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SUPPORTED_MIME_TYPES = {
    "application/pdf": extract_text_from_pdf,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": extract_text_from_docx,
    "text/plain": extract_text_from_txt,
}

EXTENSION_FALLBACKS = {
    ".pdf":  extract_text_from_pdf,
    ".docx": extract_text_from_docx,
    ".txt":  extract_text_from_txt,
    ".md":   extract_text_from_txt,
}


def parse_document(data: bytes, filename: str, content_type: str) -> list[dict]:
    """
    Parse a curriculum document and return a list of atoms.

    Tries content_type first, then falls back to file extension.
    Raises ValueError for unsupported types.
    """
    extractor = SUPPORTED_MIME_TYPES.get(content_type)

    if extractor is None:
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        extractor = EXTENSION_FALLBACKS.get(ext)

    if extractor is None:
        raise ValueError(
            f"Unsupported file type: '{content_type}' / '{filename}'. "
            f"Supported: PDF, DOCX, TXT."
        )

    raw_text   = extractor(data)
    clean_text = strip_boilerplate(raw_text)
    return chunk_into_atoms(clean_text)
