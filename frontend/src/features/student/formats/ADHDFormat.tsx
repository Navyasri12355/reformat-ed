import type { TransformedAtom } from "../../../api/types";

/** Gamified layout: mission brief, numbered challenges, progress cue. */
export function ADHDFormat({ atom }: { atom: TransformedAtom }) {
  const lines = atom.transformed_text.split("\n").filter((l) => l.trim());
  const mission = lines.find((l) => /mission brief/i.test(l));
  const challenges = lines.filter((l) => /^challenge\s*\d/i.test(l));
  const cue = lines.find((l) => /progress cue/i.test(l));

  return (
    <div className="fmt fmt-adhd">
      {mission && <div className="mission-brief">🎯 {strip(mission)}</div>}
      <div className="challenge-grid">
        {(challenges.length ? challenges : lines).map((line, i) => (
          <div className="challenge-card" key={i}>
            <span className="challenge-num">{i + 1}</span>
            <p>{strip(line)}</p>
          </div>
        ))}
      </div>
      {cue && <div className="progress-cue">⚡ {strip(cue)}</div>}
    </div>
  );
}

function strip(line: string): string {
  return line.replace(/^(mission brief:|challenge\s*\d+:|progress cue:)/i, "").trim();
}
