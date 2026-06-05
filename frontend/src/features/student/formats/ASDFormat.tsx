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
  const steps = lines.filter((l) => /^step\s*\d/i.test(l)).map((l) => l.replace(/^step\s*\d+:/i, "").trim());
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
            <button className="btn btn-sm btn-ghost" onClick={() => speak(steps.join(". "))}>
              🔊 Listen (calm voice)
            </button>
          ) : (
            <button className="btn btn-sm btn-ghost" onClick={stop}>
              ■ Stop
            </button>
          )}
        </div>
        <ol className="asd-steps">
          {steps.map((step, i) => (
            <li key={i}>{withIdioms(step, meta.idioms ?? [])}</li>
          ))}
        </ol>
        {meta.real_world && (
          <>
            <button className="btn btn-sm btn-ghost" onClick={() => setShowExample((v) => !v)}>
              Show me a real-world example
            </button>
            {showExample && <div className="example open">🔎 {meta.real_world}</div>}
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
