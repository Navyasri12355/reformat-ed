import type { TransformedAtom } from "../../../api/types";

/** Structured, predictable layout with no visual noise. */
export function ASDFormat({ atom }: { atom: TransformedAtom }) {
  const lines = atom.transformed_text.split("\n").map((l) => l.trim());
  const willLearn = lines.find((l) => /^what you will learn/i.test(l));
  const learned = lines.find((l) => /^what you learned/i.test(l));
  const steps = lines.filter((l) => /^step\s*\d/i.test(l));

  return (
    <div className="fmt fmt-asd">
      {willLearn && (
        <div className="asd-panel asd-intro">
          <h4>What you will learn</h4>
          <p>{willLearn.replace(/^what you will learn:/i, "").trim()}</p>
        </div>
      )}
      <ol className="asd-steps">
        {steps.map((line, i) => (
          <li key={i}>{line.replace(/^step\s*\d+:/i, "").trim()}</li>
        ))}
      </ol>
      {learned && (
        <div className="asd-panel asd-outro">
          <h4>What you learned</h4>
          <p>{learned.replace(/^what you learned:/i, "").trim()}</p>
        </div>
      )}
    </div>
  );
}
