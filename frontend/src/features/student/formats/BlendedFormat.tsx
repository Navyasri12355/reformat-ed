import type { TransformedAtom } from "../../../api/types";
import { useTTS } from "../hooks/useTTS";

/** Blended layout: gamified mission + structured steps, with optional audio. */
export function BlendedFormat({
  atom,
  onAudioPlay,
}: {
  atom: TransformedAtom;
  onAudioPlay?: () => void;
}) {
  const lines = atom.transformed_text.split("\n").map((l) => l.trim()).filter(Boolean);
  const mission = lines.find((l) => /mission brief/i.test(l));
  const willLearn = lines.find((l) => /^what you will learn/i.test(l));
  const steps = lines.filter((l) => /^step\s*\d/i.test(l));
  const cue = lines.find((l) => /progress cue/i.test(l));

  const { speak, stop, isPlaying, supported } = useTTS();
  const script = atom.audio_script || atom.transformed_text;

  return (
    <div className="fmt fmt-blended">
      {mission && <div className="mission-brief">🎯 {mission.replace(/^mission brief:/i, "").trim()}</div>}
      {willLearn && <p className="muted">{willLearn.replace(/^what you will learn:/i, "What you'll learn:").trim()}</p>}

      {supported && (
        <div className="audio-bar">
          {!isPlaying ? (
            <button className="btn" onClick={() => { onAudioPlay?.(); speak(script); }}>▶ Listen</button>
          ) : (
            <button className="btn btn-ghost" onClick={stop}>■ Stop</button>
          )}
        </div>
      )}

      <ol className="asd-steps">
        {steps.map((line, i) => (
          <li key={i}>{line.replace(/^step\s*\d+:/i, "").trim()}</li>
        ))}
      </ol>
      {cue && <div className="progress-cue">⚡ {cue.replace(/^progress cue:/i, "").trim()}</div>}
    </div>
  );
}
