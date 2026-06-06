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
        full_text = "\n\n".join(
            p["text"] for p in pages if isinstance(p.get("text"), str) and p["text"].strip()
        )
        sentences = split_sentences(full_text)

        atoms: list[AtomCandidate] = []
        chunk: list[str] = []
        chunk_words = 0
        seq = 0

        def flush(force: bool = False) -> None:
            nonlocal chunk, chunk_words, seq
            if chunk and (force or chunk_words >= self.min):
                atoms.append(self._build_atom(seq, " ".join(chunk)))
                seq += 1
                chunk = []
                chunk_words = 0

        for sentence in sentences:
            words = len(sentence.split())

            # A single sentence longer than max: split it at clause boundaries.
            if words > self.max:
                flush(force=True)
                for clause_chunk in self._split_long_sentence(sentence):
                    atoms.append(self._build_atom(seq, clause_chunk))
                    seq += 1
                continue

            if chunk_words + words > self.max and chunk_words >= self.min:
                flush(force=True)
                chunk = [sentence]
                chunk_words = words
            else:
                chunk.append(sentence)
                chunk_words += words

        # Final chunk: emit even if short (don't silently drop trailing content).
        flush(force=bool(chunk))
        return atoms

    def _split_long_sentence(self, sentence: str) -> list[str]:
        clauses = re.split(r"(?<=[,;:])\s+", sentence)
        out: list[str] = []
        buf: list[str] = []
        buf_words = 0
        for clause in clauses:
            cw = len(clause.split())
            if buf_words + cw > self.target and buf:
                out.append(" ".join(buf))
                buf = [clause]
                buf_words = cw
            else:
                buf.append(clause)
                buf_words += cw
        if buf:
            out.append(" ".join(buf))
        return out

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
