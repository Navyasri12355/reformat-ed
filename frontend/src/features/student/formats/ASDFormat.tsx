import { Fragment, useState } from "react";
import type { IdiomMeta, TransformedAtom } from "../../../api/types";
import { ConceptDiagram } from "../ConceptDiagram";
import { Illustration } from "../Illustration";
import { useTTS } from "../hooks/useTTS";

/**
 * Structured, predictable layout: a numbered visual schedule, the identical
 * schedule→content→summary→quiz template every time, idioms flagged and
 * rewritten literally, a real-world example on demand, and the rubric shown
 * before the quiz. No autoplay, no surprises.
 */
export function ASDFormat({ atom }: { atom: TransformedAtom }) {
  const meta = atom.meta ?? {};
  const schedule = meta.schedule ?? ["Schedule", "Content", "Summary", "Quiz"];
  const lines = atom.transformed_text.split("\n").map((l) => l.trim());
  const willLearn = lines.find((l) => /^what you will learn/i.test(l));
  const learned = lines.find((l) => /^what you learned/i.test(l));
  // Group each "Step N:" with the explanation lines that follow it (the model
  // puts the detail on the next lines, not on the marker line itself).
  const grouped = groupSteps(atom.transformed_text);
  // Resilient fallback: if there were no "Step N:" markers at all, turn the
  // reframed prose into sentence steps so nothing is dropped.
  const displaySteps = grouped.length ? grouped : toSentences(atom.transformed_text, [willLearn, learned]);
  const [showExample, setShowExample] = useState(false);
  const { speak, stop, isPlaying } = useTTS({ format: "asd_structured" });

  return (
    <div className="fmt fmt-asd">
      <div className="schedule">
        {schedule.map((s, i) => (
          <div className="st" key={i}>
            <b>{i + 1}</b>
            {s}
          </div>
        ))}
      </div>

      <div className="asd-sec asd-intro-row">
        <Illustration kind={meta.illustration} size={64} />
        <div>
          <h4>1 · What you will learn</h4>
          <p>{willLearn ? willLearn.replace(/^what you will learn:/i, "").trim() : "The key facts in this section."}</p>
        </div>
      </div>

      <ConceptDiagram code={meta.diagram} />

      <div className="asd-sec">
        <h4>2 · Content</h4>
        <div className="audio-bar">
          {!isPlaying ? (
            <button className="btn btn-sm btn-ghost" onClick={() => speak(displaySteps.join(". "))}>
              Listen (calm voice)
            </button>
          ) : (
            <button className="btn btn-sm btn-ghost" onClick={stop}>
              Stop
            </button>
          )}
        </div>
        <ol className="asd-steps">
          {displaySteps.map((step, i) => (
            <li key={i}>{withIdioms(step, meta.idioms ?? [])}</li>
          ))}
        </ol>
        {meta.real_world && (
          <>
            <button className="btn btn-sm btn-ghost" onClick={() => setShowExample((v) => !v)}>
              Show me a real-world example
            </button>
            {showExample && <div className="example open">{meta.real_world}</div>}
          </>
        )}
      </div>

      {learned && (
        <div className="asd-sec">
          <h4>3 · Summary</h4>
          <p>{learned.replace(/^what you learned:/i, "").trim()}</p>
        </div>
      )}

      {meta.rubric && meta.rubric.length > 0 && (
        <div className="asd-sec">
          <h4>4 · How this is assessed (shown before the task)</h4>
          <table className="rubric">
            <thead>
              <tr>
                <th>What is assessed</th>
                <th>How to show it</th>
              </tr>
            </thead>
            <tbody>
              {meta.rubric.map((r, i) => (
                <tr key={i}>
                  <td>{r.criterion}</td>
                  <td>{r.how}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="note">No timer. No auto-advance. No flashing. The layout is the same every lesson.</p>
        </div>
      )}
    </div>
  );
}

/** Group each "Step N:" marker with the explanation lines that follow it. */
function groupSteps(text: string): string[] {
  const steps: string[] = [];
  let current: string | null = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    if (/^what you learned/i.test(line)) break; // the summary section ends the steps
    const m = line.match(/^step\s*\d+\s*[:.)-]?\s*/i);
    if (m) {
      if (current) steps.push(current.trim());
      current = line.slice(m[0].length).trim();
    } else if (current !== null) {
      current += " " + line;
    }
  }
  if (current) steps.push(current.trim());
  return steps.filter(Boolean);
}

/** Split reframed text into clean sentence "steps", skipping any header lines. */
function toSentences(text: string, skip: (string | undefined)[]): string[] {
  const skipSet = new Set(skip.filter(Boolean).map((s) => (s as string).trim()));
  const body = text
    .split("\n")
    .map((l) => l.trim())
    .filter(
      (l) =>
        l &&
        !skipSet.has(l) &&
        !/^(what you will learn|what you learned|key idea|key facts|remember|schedule|content|summary|quiz)\b/i.test(l),
    )
    .join(" ");
  const sentences = body.split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter((s) => s.length > 1);
  return sentences.length ? sentences : [body];
}

/** Wrap any detected idiom in the text with its literal-meaning tooltip. */
function withIdioms(text: string, idioms: IdiomMeta[]) {
  if (idioms.length === 0) return text;
  // Build a single regex matching any idiom phrase (case-insensitive).
  const escaped = idioms.map((i) => i.phrase.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const re = new RegExp(`(${escaped.join("|")})`, "ig");
  const parts = text.split(re);
  return parts.map((part, i) => {
    const match = idioms.find((id) => id.phrase.toLowerCase() === part.toLowerCase());
    if (match) {
      return (
        <span className="idiom" key={i}>
          {part}
          <span className="tip">Literal meaning: {match.literal}</span>
        </span>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}
