import type { TransformedAtom } from "../../../api/types";
import { ConceptDiagram } from "../ConceptDiagram";
import { Illustration } from "../Illustration";
import { useTTS } from "../hooks/useTTS";
import { MicroPoll } from "./ADHDFormat";

/**
 * Blended layout: gamified goal + visual anchor (ADHD support) combined with a
 * numbered, predictable step structure (ASD support), optional audio, and the
 * one-question micro-poll.
 */
export function BlendedFormat({
  atom,
  onAudioPlay,
  onPollAnswered,
}: {
  atom: TransformedAtom;
  onAudioPlay?: () => void;
  onPollAnswered?: (correct: boolean) => void;
}) {
  const meta = atom.meta ?? {};
  const lines = atom.transformed_text.split("\n").map((l) => l.trim()).filter(Boolean);
  const goal = meta.goal ?? lines.find((l) => /mission brief/i.test(l))?.replace(/^mission brief:/i, "").trim();
  const steps = lines.filter((l) => /^step\s*\d/i.test(l)).map((l) => l.replace(/^step\s*\d+:/i, "").trim());
  const cue = lines.find((l) => /progress cue/i.test(l));

  const { speak, stop, isPlaying, supported } = useTTS({ format: "blended" });
  const script = atom.audio_script || atom.transformed_text;

  return (
    <div className="fmt fmt-blended">
      <div className="anchor-wrap">
        <Illustration kind={meta.illustration} />
      </div>
      {goal && <div className="mission-brief">🎯 {goal}</div>}
      <ConceptDiagram code={meta.diagram} />


      {supported && (
        <div className="audio-bar">
          {!isPlaying ? (
            <button className="btn btn-sm" onClick={() => { onAudioPlay?.(); speak(script); }}>
              ▶ Listen
            </button>
          ) : (
            <button className="btn btn-sm btn-ghost" onClick={stop}>
              ■ Stop
            </button>
          )}
        </div>
      )}

      <ol className="asd-steps">
        {steps.map((step, i) => (
          <li key={i}>{step}</li>
        ))}
      </ol>

      {meta.poll && <MicroPoll poll={meta.poll} onAnswered={onPollAnswered} />}
      {cue && <div className="progress-cue">⚡ {cue.replace(/^progress cue:/i, "").trim()}</div>}
    </div>
  );
}
