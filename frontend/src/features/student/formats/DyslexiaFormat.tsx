import { useMemo, useState } from "react";
import type { TransformedAtom } from "../../../api/types";
import { useTTS } from "../hooks/useTTS";

/** Audio-first layout: dyslexia-friendly font, word-by-word highlighting, TTS. */
export function DyslexiaFormat({
  atom,
  onAudioPlay,
}: {
  atom: TransformedAtom;
  onAudioPlay?: () => void;
}) {
  const script = atom.audio_script || atom.transformed_text;
  const words = useMemo(() => script.split(/\s+/).filter(Boolean), [script]);
  const [highlight, setHighlight] = useState(-1);

  const { speak, pause, resume, stop, isPlaying, isPaused, supported } = useTTS({
    onWordHighlight: setHighlight,
    onEnd: () => setHighlight(-1),
  });

  return (
    <div className="fmt fmt-dyslexia">
      <div className="audio-bar">
        {!isPlaying && !isPaused && (
          <button
            className="btn"
            onClick={() => {
              onAudioPlay?.();
              speak(script);
            }}
            disabled={!supported}
          >
            ▶ Listen
          </button>
        )}
        {isPlaying && (
          <button className="btn" onClick={pause}>
            ⏸ Pause
          </button>
        )}
        {isPaused && (
          <button className="btn" onClick={resume}>
            ▶ Resume
          </button>
        )}
        {(isPlaying || isPaused) && (
          <button className="btn btn-ghost" onClick={() => { stop(); setHighlight(-1); }}>
            ■ Stop
          </button>
        )}
        {!supported && <span className="muted">Audio not supported in this browser.</span>}
      </div>

      <p className="dyslexia-text">
        {words.map((w, i) => (
          <span key={i} className={i === highlight ? "word word-active" : "word"}>
            {w}{" "}
          </span>
        ))}
      </p>
    </div>
  );
}
