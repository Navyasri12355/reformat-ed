import type { TransformedAtom } from "../../api/types";
import { ADHDFormat } from "./formats/ADHDFormat";
import { ASDFormat } from "./formats/ASDFormat";
import { BlendedFormat } from "./formats/BlendedFormat";
import { DyslexiaFormat } from "./formats/DyslexiaFormat";

const FORMAT_LABEL: Record<string, string> = {
  adhd_gamified: "ADHD · Gamified",
  dyslexia_audio: "Dyslexia · Audio-first",
  asd_structured: "ASD · Structured",
  blended: "Blended",
};

export function AtomRenderer({
  atom,
  onAudioPlay,
  onPollAnswered,
  pollPassed = false,
}: {
  atom: TransformedAtom;
  onAudioPlay?: () => void;
  onPollAnswered?: (correct: boolean) => void;
  pollPassed?: boolean;
}) {
  return (
    <div className="atom-renderer">
      <div className="format-badge">
        {FORMAT_LABEL[atom.output_format] ?? atom.output_format}
      </div>
      {atom.output_format === "adhd_gamified" && (
        <ADHDFormat
          atom={atom}
          onPollAnswered={onPollAnswered}
          pollPassed={pollPassed}
        />
      )}
      {atom.output_format === "dyslexia_audio" && (
        <DyslexiaFormat atom={atom} onAudioPlay={onAudioPlay} />
      )}
      {atom.output_format === "asd_structured" && <ASDFormat atom={atom} />}
      {atom.output_format === "blended" && (
        <BlendedFormat
          atom={atom}
          onAudioPlay={onAudioPlay}
          onPollAnswered={onPollAnswered}
          pollPassed={pollPassed}
        />
      )}
    </div>
  );
}
