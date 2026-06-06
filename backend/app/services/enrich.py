"""Structured per-format enrichment.

The prose rewrite (LLM or local) tells the student *what to read*. This module
derives the **interactive scaffolding** around it — directly from the source
atom, so it is deterministic and identical regardless of which transform path
ran:

* ADHD  → one-line goal, a topic-grounded HTML simulator card, a per-segment
          concept diagram, and a genuine fill-in-the-blank (cloze) check whose
          answer comes from the text
* ASD   → a fixed lesson schedule, literal rewrites of any idioms found, a
          real-world example, a concept diagram, a topic-grounded HTML simulator
          and a pre-shown rubric
* Dyslexia → the key vocabulary to highlight + a concept diagram + simulator
* Blended → goal + simulator + schedule + cloze check

The cloze question removes a real key word from a real sentence, so it is always
answerable from reading the segment; distractors are other terms from the same
subject, so every option is plausible.
"""

from __future__ import annotations

import hashlib
import json
import re

from app.services.atomiser import SUBJECT_KEYWORDS, split_sentences

# --------------------------------------------------------------------------- #
# Static knowledge
# --------------------------------------------------------------------------- #
SUBJECT_ANCHOR = {
    "biology": "🌿",
    "chemistry": "⚗️",
    "physics": "⚛️",
    "mathematics": "➗",
    "history": "📜",
    "literature": "📖",
    "computer_science": "💻",
    "general": "📘",
}

# Subject keys → the frontend renders a matching HTML simulator card.
SUBJECT_SIMULATOR = {
    "biology": "cycle",
    "chemistry": "reaction",
    "physics": "motion",
    "mathematics": "graph",
    "history": "timeline",
    "literature": "story",
    "computer_science": "logic",
    "general": "compare",
}

SUBJECT_REAL_WORLD = {
    "biology": "You can see this in living things around you — a plant on a windowsill or the food you eat.",
    "chemistry": "This happens in everyday materials, like cooking, cleaning products, or rust on metal.",
    "physics": "You meet this every day — riding a bike, dropping a ball, or switching on a light.",
    "mathematics": "You use this when shopping, measuring, or sharing things equally.",
    "history": "This still shapes the country, laws, or borders you live with today.",
    "literature": "You notice this in films and songs, not just books.",
    "computer_science": "This runs inside the apps and games you use every day.",
    "general": "You can find an example of this in your own daily life.",
}

# Plausible same-subject distractors for the cloze check.
SUBJECT_TERMS = {
    "biology": [
        "chloroplast",
        "chlorophyll",
        "mitochondria",
        "nucleus",
        "glucose",
        "oxygen",
        "enzyme",
        "membrane",
        "organism",
        "photosynthesis",
    ],
    "chemistry": [
        "atom",
        "molecule",
        "electron",
        "compound",
        "reaction",
        "ion",
        "acid",
        "base",
        "bond",
        "element",
    ],
    "physics": [
        "force",
        "energy",
        "velocity",
        "mass",
        "acceleration",
        "gravity",
        "momentum",
        "friction",
        "voltage",
        "current",
    ],
    "mathematics": [
        "equation",
        "function",
        "variable",
        "fraction",
        "integer",
        "angle",
        "ratio",
        "product",
        "factor",
        "polynomial",
    ],
    "history": [
        "empire",
        "revolution",
        "treaty",
        "monarchy",
        "democracy",
        "colony",
        "dynasty",
        "republic",
        "alliance",
        "reform",
    ],
    "literature": [
        "metaphor",
        "narrator",
        "theme",
        "plot",
        "character",
        "symbol",
        "setting",
        "stanza",
        "rhyme",
        "genre",
    ],
    "computer_science": [
        "algorithm",
        "variable",
        "function",
        "array",
        "loop",
        "compiler",
        "memory",
        "database",
        "pointer",
        "recursion",
    ],
    "general": [
        "idea",
        "process",
        "reason",
        "result",
        "method",
        "cause",
        "effect",
        "factor",
        "example",
        "pattern",
    ],
}

# Common idioms → literal meaning (for ASD literal-language support).
IDIOM_DICT: dict[str, str] = {
    "a piece of cake": "very easy",
    "costs an arm and a leg": "is very expensive",
    "hit the books": "study hard",
    "break the ice": "start a conversation",
    "under the weather": "feeling ill",
    "bite the bullet": "do something difficult you have been avoiding",
    "once in a blue moon": "very rarely",
    "the ball is in your court": "it is your turn to decide",
    "let the cat out of the bag": "reveal a secret",
    "on the same page": "in agreement",
    "back to the drawing board": "start again from the beginning",
    "cutting corners": "doing something cheaply or carelessly",
    "in a nutshell": "in summary",
    "the tip of the iceberg": "a small visible part of a much bigger thing",
    "raining cats and dogs": "raining very heavily",
}

_STOPWORDS = {
    "this",
    "that",
    "these",
    "those",
    "which",
    "their",
    "there",
    "where",
    "while",
    "about",
    "into",
    "from",
    "with",
    "they",
    "them",
    "have",
    "uses",
    "used",
    "also",
    "called",
    "inside",
    "using",
    "makes",
    "make",
    "takes",
    "take",
    "kind",
    "part",
    "parts",
    "very",
    "many",
    "more",
    "most",
    "some",
    "what",
    "when",
    "then",
    "your",
    "each",
    "other",
    "because",
    "around",
    "between",
    "things",
    "something",
}


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def build_meta(atom: dict, output_format: str) -> dict:
    text = atom.get("raw_text", "") or ""
    subject = (atom.get("subject") or "general").lower()
    if subject not in SUBJECT_ANCHOR:
        subject = "general"

    keywords = extract_keywords(text, subject)
    diagram = build_diagram(subject, keywords, text=text)
    simulator = build_simulator(subject, keywords, text)

    if output_format == "dyslexia_audio":
        return {"keywords": keywords, "simulator": simulator, "diagram": diagram}

    if output_format == "asd_structured":
        return {
            "schedule": ["Schedule", "Content", "Summary", "Quiz"],
            "idioms": detect_idioms(text),
            "real_world": SUBJECT_REAL_WORLD[subject],
            "rubric": build_rubric(subject),
            "simulator": simulator,
            "diagram": diagram,
        }

    if output_format == "adhd_gamified":
        return {
            "goal": build_goal(text, subject),
            "anchor": SUBJECT_ANCHOR[subject],
            "simulator": simulator,
            "diagram": diagram,
            "poll": build_poll(text, keywords, subject),
        }

    # blended → enough scaffolding for both gamified and structured rendering
    return {
        "goal": build_goal(text, subject),
        "anchor": SUBJECT_ANCHOR[subject],
        "simulator": simulator,
        "diagram": diagram,
        "schedule": ["Schedule", "Content", "Summary", "Quiz"],
        "poll": build_poll(text, keywords, subject),
        "keywords": keywords,
    }


# --------------------------------------------------------------------------- #
# Builders
# --------------------------------------------------------------------------- #
def extract_keywords(text: str, subject: str, limit: int = 5) -> list[str]:
    lower = text.lower()
    found: list[str] = []

    # 1. Subject-specific vocabulary actually present in the text.
    pattern = SUBJECT_KEYWORDS.get(subject)
    if pattern:
        for m in re.findall(pattern, lower):
            if m not in found:
                found.append(m)

    # 2. Long, content-bearing words as a fallback / supplement.
    if len(found) < limit:
        words = re.findall(r"[A-Za-z]{6,}", lower)
        for w in sorted(set(words), key=lambda w: -len(w)):
            if w not in _STOPWORDS and w not in found:
                found.append(w)
            if len(found) >= limit:
                break

    return found[:limit] or ["idea"]


def build_goal(text: str, subject: str) -> str:
    first = (split_sentences(text) or [text])[0].strip()
    first = re.sub(r"\s+", " ", first)
    if len(first) <= 120:
        return first.rstrip()
    trimmed = first[:120].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{trimmed}."


def build_simulator(subject: str, keywords: list[str], text: str) -> dict:
    lines = [s.strip() for s in split_sentences(text) if s.strip()]
    title = {
        "biology": "Biology process simulator",
        "chemistry": "Chemistry reaction simulator",
        "physics": "Physics motion simulator",
        "mathematics": "Math pattern simulator",
        "history": "History timeline simulator",
        "literature": "Literature structure simulator",
        "computer_science": "Code logic simulator",
        "general": "Concept comparison simulator",
    }[subject]
    concept = (
        keywords[0].replace("_", " ").title()
        if keywords
        else subject.replace("_", " ").title()
    )
    steps = [re.sub(r"\s+", " ", s) for s in lines[:4]] or [text.strip()]
    steps = [
        s if len(s) <= 120 else s[:120].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
        for s in steps
    ]
    return {
        "type": SUBJECT_SIMULATOR[subject],
        "title": title,
        "concept": concept,
        "steps": steps,
        "keywords": keywords[:4],
    }


def detect_idioms(text: str) -> list[dict]:
    lower = text.lower()
    return [
        {"phrase": phrase, "literal": literal}
        for phrase, literal in IDIOM_DICT.items()
        if phrase in lower
    ]


def build_rubric(subject: str) -> list[dict]:
    topic = subject.replace("_", " ")
    return [
        {
            "criterion": f"Explain the main idea of this {topic} concept",
            "how": "In a sentence, a numbered list, OR a labelled diagram — all accepted",
        },
        {
            "criterion": "Use the key terms correctly",
            "how": "Prose, a numbered list, or a diagram — your choice",
        },
        {
            "criterion": "Give one example",
            "how": "One real-world example, in any format",
        },
    ]


_LABEL_BREAKERS = re.compile(r"""["'`()\[\]{}|<>;#&%:]""")


def _clean_label(text: str) -> str:
    """Make a node label safe for Mermaid: letters/numbers/spaces/hyphens only."""
    text = _LABEL_BREAKERS.sub(" ", str(text))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:48] or "node"


def mermaid_from_concepts(nodes: list[str], edges: list) -> str | None:
    """Build GUARANTEED-valid Mermaid from a node/edge list. We emit the syntax
    ourselves (clean ids `N0..`, quoted+sanitised labels), so it can never carry
    a syntax error regardless of what the LLM produced."""
    labels = [_clean_label(n) for n in nodes if str(n).strip()][:6]
    if len(labels) < 2:
        return None
    lines = ["flowchart TD"]
    for i, label in enumerate(labels):
        lines.append(f'    N{i}["{label}"]')

    emitted = False
    seen: set[tuple[int, int]] = set()
    for edge in edges or []:
        try:
            a, b = int(edge[0]), int(edge[1])
        except (TypeError, ValueError, IndexError, KeyError):
            continue
        if (
            0 <= a < len(labels)
            and 0 <= b < len(labels)
            and a != b
            and (a, b) not in seen
        ):
            lines.append(f"    N{a} --> N{b}")
            seen.add((a, b))
            emitted = True
    if not emitted:  # no usable edges → chain the concepts so it stays connected
        for i in range(len(labels) - 1):
            lines.append(f"    N{i} --> N{i + 1}")
    return "\n".join(lines)


def _build_diagram_with_llm(text: str, subject: str) -> str | None:
    """Ask the LLM only for *concepts* (JSON), never for Mermaid syntax. We then
    construct the Mermaid ourselves so it is always valid."""
    from app.config import settings

    if not settings.openai_api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            timeout=settings.openai_timeout_seconds,
        )
        prompt = (
            "From the educational text, extract a simple concept map as JSON with exactly "
            'this shape: {"nodes": ["short concept", ...], "edges": [[fromIndex, toIndex], ...]}\n'
            "Rules:\n"
            "- 3 to 6 nodes. Each label is 1-4 plain words: letters and spaces only, no "
            "punctuation, brackets, or quotes.\n"
            "- edges use node indices and show how the concepts connect.\n"
            "- Output ONLY the JSON object, with no markdown fences or extra text.\n\n"
            f"Subject: {subject}\nText:\n{text}"
        )
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )
        raw = (resp.choices[0].message.content or "").strip()
        match = re.search(r"\{.*\}", raw, re.S)
        if not match:
            return None
        data = json.loads(match.group(0))
        return mermaid_from_concepts(data.get("nodes", []), data.get("edges", []))
    except Exception:
        return None


def build_diagram(subject: str, keywords: list[str], text: str = "") -> str:
    """A small Mermaid concept map for the segment. ALWAYS returns valid Mermaid:
    an LLM-derived concept map when possible, else a deterministic keyword map."""
    if text:
        llm = _build_diagram_with_llm(text, subject)
        if llm:
            return llm

    topic = _clean_label(subject.replace("_", " ").title())
    lines = ["flowchart TD", f'    TOPIC["{topic}"]']
    for i, kw in enumerate(keywords[:4]):
        lines.append(f'    TOPIC --> K{i}["{_clean_label(kw)}"]')
    return "\n".join(lines)


def build_poll(text: str, keywords: list[str], subject: str) -> dict:
    """Build a high-value quick check from the main idea, not a random noun.

    The blank should target a concept-bearing term from the earliest important
    sentence so the question checks understanding of the section's key point.
    """
    sentences = [s.strip() for s in (split_sentences(text) or [text]) if s.strip()]
    focus_sentences = sentences[:3] or sentences
    answer = ""
    blanked = ""

    candidate_terms = [kw for kw in keywords if len(kw) >= 5]
    preferred_terms = [
        term
        for term in candidate_terms
        if term.lower()
        not in {"organism", "example", "process", "result", "method", "factor"}
    ]

    for sentence in focus_sentences:
        for term in preferred_terms + candidate_terms:
            if re.search(rf"\b{re.escape(term)}\b", sentence, re.I):
                answer = term
                blanked = re.sub(
                    rf"\b{re.escape(term)}\b", "______", sentence, count=1, flags=re.I
                ).strip()
                break
        if blanked:
            break

    if not blanked:
        sentence = next(
            (s for s in focus_sentences if len(s.split()) >= 5), focus_sentences[0]
        )
        words = [
            w
            for w in re.findall(r"[A-Za-z]{5,}", sentence)
            if w.lower() not in _STOPWORDS
            and w.lower() not in {"organism", "important", "information"}
        ]
        answer = (
            words[0] if words else (candidate_terms[0] if candidate_terms else "idea")
        )
        blanked = re.sub(
            rf"\b{re.escape(answer)}\b", "______", sentence, count=1, flags=re.I
        ).strip()

    pool = SUBJECT_TERMS.get(subject, SUBJECT_TERMS["general"])
    lower_blank = blanked.lower()
    distractors = [
        t
        for t in pool
        if t.lower() != answer.lower()
        and t.lower() not in lower_blank
        and t.lower() not in {"organism", "example", "process"}
    ][:2]
    for kw in candidate_terms:
        if len(distractors) >= 2:
            break
        if (
            kw.lower() != answer.lower()
            and kw.lower() not in lower_blank
            and kw not in distractors
        ):
            distractors.append(kw)
    while len(distractors) < 2:
        distractors.append(f"{subject} term {len(distractors) + 1}")

    options = [answer, *distractors]
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
    rotate = seed % len(options)
    options = options[rotate:] + options[:rotate]

    return {
        "q": f'Fill in the blank: "{blanked}"',
        "options": options,
        "answer": options.index(answer),
    }
