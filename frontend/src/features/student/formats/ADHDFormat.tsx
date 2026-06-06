import { useState } from "react";
import type { TransformedAtom } from "../../../api/types";
import { ConceptDiagram } from "../ConceptDiagram";
import { Illustration } from "../Illustration";

/**
 * Gamified layout: a single 3–5 min micro-segment with one explicit goal, a
 * visual anchor before the text, and a one-question micro-poll (not a big test).
 * Answering correctly unlocks completion via `onPollAnswered`.
 */
export function ADHDFormat({
  atom,
  onPollAnswered,
  pollPassed = false,
}: {
  atom: TransformedAtom;
  onPollAnswered?: (correct: boolean) => void;
  pollPassed?: boolean;
}) {
  const meta = atom.meta ?? {};
  const lines = atom.transformed_text.split("\n").filter((l) => l.trim());
  const goal =
    meta.goal ?? strip(lines.find((l) => /mission brief|goal/i.test(l)) ?? "");
  const cue = lines.find((l) => /progress cue/i.test(l));
  // Group each "Challenge N:" with its following explanation lines; fall back to
  // sentence chunks if the model used no markers, so content is never dropped.
  const grouped = groupChallenges(atom.transformed_text);
  const body = (
    grouped.length
      ? grouped
      : lines
          .filter((l) => !/mission brief|progress cue/i.test(l))
          .join(" ")
          .split(/(?<=[.!?])\s+/)
          .map((s) => s.trim())
          .filter((s) => s.length > 1)
  ).slice(0, 3);

  return (
    <div className="fmt fmt-adhd">
      <div className="anchor-wrap">
        <Illustration simulator={meta.simulator} />
      </div>
      {goal && <div className="goal">Goal: {goal}</div>}

      <ConceptDiagram simulator={meta.simulator} keywords={meta.keywords} diagram={meta.diagram} />

      <div className="challenge-grid">
        {body.map((line, i) => (
          <div className="challenge-card" key={i}>
            <span className="challenge-num">{i + 1}</span>
            <p>{line}</p>
          </div>
        ))}
      </div>

      {meta.poll && <MicroPoll poll={meta.poll} onAnswered={onPollAnswered} />}
      {cue && (!meta.poll || pollPassed) && (
        <div className="progress-cue">{strip(cue)}</div>
      )}
    </div>
  );
}

export function MicroPoll({
  poll,
  onAnswered,
}: {
  poll: NonNullable<TransformedAtom["meta"]>["poll"];
  onAnswered?: (correct: boolean) => void;
}) {
  const [picked, setPicked] = useState<number | null>(null);
  const [solved, setSolved] = useState(false);
  if (!poll) return null;

  return (
    <div className="poll">
      <b>Quick check — 1 question, not a big test:</b>
      <div className="poll-q">{poll.q}</div>
      {poll.options.map((opt, i) => {
        let cls = "opt";
        if (picked === i) cls += i === poll.answer ? " right" : " wrong";
        else if (solved && i === poll.answer) cls += " right";
        return (
          <button
            key={i}
            className={cls}
            disabled={solved}
            onClick={() => {
              setPicked(i);
              const correct = i === poll.answer;
              if (correct) setSolved(true);
              onAnswered?.(correct);
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

function strip(line: string): string {
  return line
    .replace(/^(mission brief:|challenge\s*\d+:|progress cue:|goal:)/i, "")
    .trim();
}

/** Group each "Challenge N:" marker with the explanation lines that follow it. */
function groupChallenges(text: string): string[] {
  const out: string[] = [];
  let current: string | null = null;
  for (const raw of text.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    if (/^progress cue/i.test(line)) break;
    if (/^mission brief/i.test(line)) continue;
    const m = line.match(/^challenge\s*\d+\s*[:.)-]?\s*/i);
    if (m) {
      if (current) out.push(current.trim());
      current = line.slice(m[0].length).trim();
    } else if (current !== null) {
      current += " " + line;
    }
  }
  if (current) out.push(current.trim());
  return out.filter(Boolean);
}
