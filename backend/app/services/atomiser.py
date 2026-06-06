"""Curriculum atomiser — breaks parsed document text into the smallest coherent
content units ("atoms") and tags each with subject, grade level, Bloom's level
and an estimated reading time.

Uses spaCy for sentence segmentation when available, and falls back to a robust
regex sentence splitter otherwise, so the pipeline runs with no model download.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# Optional spaCy backend
# --------------------------------------------------------------------------- #
_NLP = None
try:  # pragma: no cover - depends on environment
    import spacy

    try:
        _NLP = spacy.load("en_core_web_sm")
    except OSError:
        _NLP = spacy.blank("en")
        if "sentencizer" not in _NLP.pipe_names:
            _NLP.add_pipe("sentencizer")
except ImportError:  # spaCy not installed — use regex fallback
    _NLP = None


_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def split_sentences(text: str) -> list[str]:
    """Segment text into sentences using spaCy if present, else regex."""
    text = text.strip()
    if not text:
        return []
    if _NLP is not None:
        doc = _NLP(text)
        return [s.text.strip() for s in doc.sents if s.text.strip()]
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]


# --------------------------------------------------------------------------- #
# Classification heuristics
# --------------------------------------------------------------------------- #
BLOOM_PATTERNS = {
    "remember": r"\b(define|defines|list|lists|recall|name|names|identify|state|states|recognise|recognize|label)\b",
    "understand": r"\b(explain|explains|describe|describes|summarise|summarize|paraphrase|classify|compare|interpret|discuss)\b",
    "apply": r"\b(use|uses|solve|solves|demonstrate|calculate|calculates|operate|implement|apply|applies|compute)\b",
    "analyse": r"\b(analyse|analyze|differentiate|examine|distinguish|infer|categorise|categorize|investigate)\b",
    "evaluate": r"\b(evaluate|judge|justify|critique|assess|argue|defend|appraise|recommend)\b",
    "create": r"\b(design|construct|develop|formulate|compose|plan|produce|generate|invent)\b",
}

SUBJECT_KEYWORDS = {
    "mathematics": r"\b(equation|function|integral|derivative|polynomial|matrix|algebra|geometry|theorem)\b",
    "biology": r"\b(cell|cells|organism|dna|protein|photosynthesis|evolution|enzyme|chromosome|mitosis)\b",
    "chemistry": r"\b(element|compound|reaction|molecule|bond|valence|atom|acid|alkali|ion)\b",
    "physics": r"\b(force|velocity|energy|mass|acceleration|momentum|gravity|voltage|current|wavelength)\b",
    "history": r"\b(century|war|revolution|empire|colonialism|treaty|dynasty|civilisation|civilization)\b",
    "literature": r"\b(narrative|theme|metaphor|protagonist|symbolism|genre|poem|character|prose)\b",
    "computer_science": r"\b(algorithm|function|variable|compiler|database|recursion|array|pointer|software)\b",
}

AVERAGE_WORDS_PER_MINUTE_READING = 200


@dataclass
class AtomCandidate:
    sequence_index: int
    raw_text: str
    subject: str
    grade_level: str
    bloom_level: str
    estimated_reading_minutes: float


class CurriculumAtomiser:
    def __init__(
        self,
        # Higher thresholds keep complete ideas together so a segment is never
        # cut off mid-explanation. A single sentence is only ever split if it
        # alone exceeds `max_words_per_atom` (rare for real prose).
        target_words_per_atom: int = 220,
        max_words_per_atom: int = 500,
        min_words_per_atom: int = 40,
    ):
        if not (min_words_per_atom <= target_words_per_atom <= max_words_per_atom):
            raise ValueError("Require min <= target <= max words per atom")
        self.target = target_words_per_atom
        self.max = max_words_per_atom
        self.min = min_words_per_atom

    def atomise(self, pages: list[dict]) -> list[AtomCandidate]:
        """Split a document into coherent, topic-respecting atoms.

        Works on whole paragraphs (not fixed character windows): short heading
        lines are attached to the content they introduce, paragraphs are grouped
        up to the target size on natural boundaries, a paragraph is only ever
        split between whole sentences, and junk (page numbers, codes, stray
        fragments) is dropped — so every atom reads as a complete idea.
        """
        paragraphs = self._merge_headings(self._extract_paragraphs(pages))

        atoms: list[AtomCandidate] = []
        chunk: list[str] = []
        chunk_words = 0
        seq = 0

        def flush() -> None:
            nonlocal chunk, chunk_words, seq
            if not chunk:
                return
            text = "\n".join(chunk).strip()
            if self._is_meaningful(text):
                atoms.append(self._build_atom(seq, text))
                seq += 1
            chunk = []
            chunk_words = 0

        for para in paragraphs:
            words = len(para.split())

            # A single very long paragraph → split between whole sentences.
            if words > self.max:
                flush()
                for piece in self._pack_sentences(para):
                    if self._is_meaningful(piece):
                        atoms.append(self._build_atom(seq, piece))
                        seq += 1
                continue

            # Start a new atom once adding this paragraph would exceed the target
            # and we already have enough content — keeps related paragraphs together.
            if chunk_words + words > self.target and chunk_words >= self.min:
                flush()
            chunk.append(para)
            chunk_words += words

        flush()
        return atoms

    @staticmethod
    def _extract_paragraphs(pages: list[dict]) -> list[str]:
        paragraphs: list[str] = []
        for page in pages:
            text = page.get("text", "")
            if not isinstance(text, str) or not text.strip():
                continue
            for block in re.split(r"\n\s*\n", text):
                para = " ".join(block.split())  # collapse internal newlines/spaces
                if para:
                    paragraphs.append(para)
        return paragraphs

    @staticmethod
    def _merge_headings(paragraphs: list[str]) -> list[str]:
        """Attach short heading-like lines to the paragraph they introduce, so a
        heading never becomes a meaningless stand-alone atom."""
        out: list[str] = []
        pending = ""
        for para in paragraphs:
            # Drop page furniture: pure numbers / symbols (e.g. "1", "- 2 -").
            if re.fullmatch(r"[\d\W]+", para.strip()):
                continue
            looks_like_heading = len(para.split()) <= 8 and not para.rstrip().endswith((".", "!", "?"))
            if looks_like_heading:
                pending = f"{pending} {para}".strip() if pending else para
                continue
            if pending:
                sep = " " if pending.rstrip().endswith((":", "-")) else " — "
                para = f"{pending}{sep}{para}"
                pending = ""
            out.append(para)
        if pending:
            out.append(pending)
        return out

    def _pack_sentences(self, text: str) -> list[str]:
        """Pack whole sentences into <= max-word pieces (never splits a sentence)."""
        out: list[str] = []
        buf: list[str] = []
        buf_words = 0
        for sentence in split_sentences(text) or [text]:
            sw = len(sentence.split())
            if buf_words + sw > self.max and buf:
                out.append(" ".join(buf))
                buf = [sentence]
                buf_words = sw
            else:
                buf.append(sentence)
                buf_words += sw
        if buf:
            out.append(" ".join(buf))
        return out

    @staticmethod
    def _is_meaningful(text: str) -> bool:
        """Drop junk atoms (page numbers, codes, dotted TOC lines) while keeping
        any real prose — even short sentences."""
        words = text.split()
        if not words:
            return False
        real_words = [w for w in words if sum(ch.isalpha() for ch in w) >= 3]
        if len(real_words) < 3:
            return False  # e.g. "1", "031", "Subject Code 031"
        numeric_words = [w for w in words if any(ch.isdigit() for ch in w)]
        if len(numeric_words) > len(words) * 0.5:
            return False  # mostly numbers → tables / page furniture
        return True

    def _build_atom(self, seq: int, text: str) -> AtomCandidate:
        word_count = len(text.split())
        return AtomCandidate(
            sequence_index=seq,
            raw_text=text.strip(),
            subject=self._classify_subject(text),
            grade_level=self._infer_grade(text),
            bloom_level=self._classify_bloom(text),
            estimated_reading_minutes=round(word_count / AVERAGE_WORDS_PER_MINUTE_READING, 2),
        )

    def _classify_bloom(self, text: str) -> str:
        lower = text.lower()
        for level, pattern in BLOOM_PATTERNS.items():
            if re.search(pattern, lower):
                return level
        return "understand"

    def _classify_subject(self, text: str) -> str:
        lower = text.lower()
        scores = {
            subject: len(re.findall(pattern, lower))
            for subject, pattern in SUBJECT_KEYWORDS.items()
        }
        scores = {s: c for s, c in scores.items() if c}
        if not scores:
            return "general"
        return max(scores, key=scores.get)

    def _infer_grade(self, text: str) -> str:
        """Flesch–Kincaid grade-level approximation mapped to a band."""
        words = text.split()
        sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
        if not sentences or not words:
            return "unknown"
        avg_sentence_length = len(words) / len(sentences)
        syllables = sum(self._count_syllables(w) for w in words)
        avg_syllables = syllables / len(words)
        fk_grade = (0.39 * avg_sentence_length) + (11.8 * avg_syllables) - 15.59
        grade = max(1, min(16, round(fk_grade)))
        if grade <= 5:
            return "elementary"
        if grade <= 8:
            return "middle"
        if grade <= 12:
            return "high-school"
        return "university"

    @staticmethod
    def _count_syllables(word: str) -> int:
        word = word.lower().strip(".,!?;:\"'()[]")
        if len(word) <= 3:
            return 1 if word else 0
        vowels = "aeiouy"
        count = sum(
            1
            for i, ch in enumerate(word)
            if ch in vowels and (i == 0 or word[i - 1] not in vowels)
        )
        if word.endswith("e"):
            count -= 1
        return max(1, count)
