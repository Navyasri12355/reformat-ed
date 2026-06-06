import { useMemo, useState } from "react";
import type { TransformedAtom } from "../../../api/types";
import { ConceptDiagram } from "../ConceptDiagram";
import { Illustration } from "../Illustration";
import { useTTS } from "../hooks/useTTS";
import { colourise } from "./textColor";

/**
 * Audio-first layout for dyslexia: OpenDyslexic font, colour-coded syllables,
 * highlighted key words, and content broken into chunked + NUMBERED sections,
 * with whole-lesson and per-chunk text-to-speech.
 */
export function DyslexiaFormat({
  atom,
  onAudioPlay,
}: {
  atom: TransformedAtom;
  onAudioPlay?: () => void;
}) {
  const script = atom.audio_script || atom.transformed_text;

  // Break the transformed text into readable chunks: keep UPPERCASE headings
  // as their own labelled block, otherwise one short paragraph per chunk.
  const chunks = useMemo(
    () => splitChunks(atom.transformed_text),
    [atom.transformed_text],
  );

  const keywords = atom.meta?.keywords ?? [];
  const [active, setActive] = useState(-1);
  const { speak, stop, isPlaying, supported, engine } = useTTS({
    format: "dyslexia_audio",
    onEnd: () => setActive(-1),
  });

  const playAll = () => {
    onAudioPlay?.();
    speak(script);
  };

  return (
    <div className="fmt fmt-dyslexia">
      <div className="dys-controls">
        {!isPlaying ? (
          <button className="btn" onClick={playAll} disabled={!supported}>
            Listen to all
          </button>
        ) : (
          <button
            className="btn btn-ghost"
            onClick={() => {
              stop();
              setActive(-1);
            }}
          >
            Stop
          </button>
        )}
        <span className="legend">
          Colour key: <b className="syl-a">syllables</b>{" "}
          <b className="syl-b">alternate</b> <b className="kw">key words</b>
        </span>
        <span className="voice-tag">slow &amp; clear voice · {engine}</span>
        {!supported && (
          <span className="muted">Audio not supported in this browser.</span>
        )}
      </div>

      <div className="anchor-wrap">
        <Illustration simulator={atom.meta?.simulator} />
      </div>
      <ConceptDiagram
        simulator={atom.meta?.simulator}
        keywords={atom.meta?.keywords}
        diagram={atom.meta?.diagram}
        defaultOpen={false}
      />

      {chunks.map((chunk, i) =>
        chunk.heading ? (
          <h4 className="dys-heading" key={i}>
            {chunk.text}
          </h4>
        ) : (
          <div
            className={
              active === i ? "dys-chunk dys-chunk-active" : "dys-chunk"
            }
            key={i}
          >
            <div className="dys-num">{numberOf(chunks, i)}</div>
            <div style={{ flex: 1 }}>
              <p className="dys-text">{colourise(chunk.text, keywords)}</p>
              <button
                className="btn btn-sm btn-ghost"
                disabled={!supported}
                onClick={() => {
                  onAudioPlay?.();
                  setActive(i);
                  speak(chunk.text);
                }}
              >
                Listen to this part
              </button>
            </div>
          </div>
        ),
      )}
    </div>
  );
}

interface Chunk {
  text: string;
  heading: boolean;
}

function splitChunks(text: string): Chunk[] {
  const lines = text
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const out: Chunk[] = [];
  for (const line of lines) {
    const isHeading =
      /^[A-Z0-9 ]{3,}$/.test(line) && line === line.toUpperCase();
    if (isHeading) {
      out.push({ text: line, heading: true });
    } else {
      // Split a paragraph into one chunk per sentence for digestible pieces.
      for (const sentence of line.split(/(?<=[.!?])\s+/)) {
        if (sentence.trim())
          out.push({ text: sentence.trim(), heading: false });
      }
    }
  }
  return (out.length ? out : [{ text, heading: false }]).slice(0, 5);
}

/** Sequential number among non-heading chunks only. */
function numberOf(chunks: Chunk[], index: number): number {
  let n = 0;
  for (let i = 0; i <= index; i++) if (!chunks[i].heading) n++;
  return n;
}
