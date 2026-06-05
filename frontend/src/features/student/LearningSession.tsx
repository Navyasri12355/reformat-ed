import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { sessionsApi, transformsApi } from "../../api";
import type { StudentContent, TransformedAtom } from "../../api/types";
import { AtomRenderer } from "./AtomRenderer";
import { StudyTools } from "./StudyTools";
import { useSessionTracker } from "./hooks/useSessionTracker";
import { percent } from "../../utils/progress";

export function LearningSession() {
  const { documentId = "" } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState<StudentContent | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [data, session] = await Promise.all([
          transformsApi.studentContent(documentId),
          sessionsApi.start(documentId),
        ]);
        if (!active) return;
        setContent(data);
        setSessionId(session.id);
      } catch {
        if (active) setError("Could not load your content. Has it been approved yet?");
      }
    })();
    return () => {
      active = false;
    };
  }, [documentId]);

  if (error) return <div className="card center">{error}</div>;
  if (!content || !sessionId) return <div className="center muted">Preparing your lesson…</div>;
  if (content.atoms.length === 0)
    return (
      <div className="card center">
        <p>No approved content yet. Your teacher needs to approve it first.</p>
        <button className="btn" onClick={() => navigate("/")}>Back</button>
      </div>
    );

  const atoms = content.atoms;
  const total = atoms.length;
  // ADHD support tools appear when ADHD is the dominant trait or any atom is
  // delivered in a gamified/blended format.
  const snap = content.profile_snapshot;
  const adhdDominant =
    (snap.adhd_weight ?? 0) >= (snap.dyslexia_weight ?? 0) &&
    (snap.adhd_weight ?? 0) >= (snap.asd_weight ?? 0) &&
    (snap.adhd_weight ?? 0) > 0;
  const showTools =
    adhdDominant || atoms.some((a) => a.output_format === "adhd_gamified" || a.output_format === "blended");

  if (done) {
    return (
      <div className="card center">
        <h2>Lesson complete! 🎉</h2>
        <p className="muted">Great work. We'll keep tuning this to how you learn best.</p>
        <button className="btn" onClick={async () => { await sessionsApi.end(sessionId); navigate("/"); }}>
          Finish
        </button>
      </div>
    );
  }

  const goNext = () => {
    if (index + 1 >= total) setDone(true);
    else setIndex((i) => i + 1);
  };

  return (
    <div className="learn">
      <ProgressBar current={index} total={total} />
      <AtomStep
        key={atoms[index].id}
        sessionId={sessionId}
        atom={atoms[index]}
        onNext={goNext}
      />
      <div className="learn-meta muted">
        Segment {index + 1} of {total}
        {showTools && " · 3–5 min micro-segment"}
      </div>
      {showTools && <StudyTools />}
    </div>
  );
}

function ProgressBar({ current, total }: { current: number; total: number }) {
  const pct = percent(current, total);
  return (
    <div className="progress-track" aria-label="progress">
      <div className="progress-fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

function AtomStep({
  sessionId,
  atom,
  onNext,
}: {
  sessionId: string;
  atom: TransformedAtom;
  onNext: () => void;
}) {
  const tracker = useSessionTracker({
    sessionId,
    atomId: atom.atom_id,
    transformedAtomId: atom.id,
  });

  const hasPoll =
    (atom.output_format === "adhd_gamified" || atom.output_format === "blended") &&
    !!atom.meta?.poll;
  const [pollPassed, setPollPassed] = useState(!hasPoll);

  const onPollAnswered = (correct: boolean) => {
    if (correct) setPollPassed(true);
    else tracker.markRetry();
  };

  return (
    <div className="card atom-card">
      <AtomRenderer
        atom={atom}
        onAudioPlay={tracker.markAudioPlay}
        onPollAnswered={onPollAnswered}
      />
      <div className="atom-controls">
        <button className="btn btn-ghost" onClick={() => { tracker.markSkip(); onNext(); }}>
          Skip
        </button>
        <button className="btn btn-ghost" onClick={tracker.markRetry}>
          I didn't get that
        </button>
        <button
          className="btn"
          disabled={!pollPassed}
          title={pollPassed ? "" : "Answer the quick check first"}
          onClick={() => {
            tracker.markComplete();
            onNext();
          }}
        >
          Got it ✓
        </button>
      </div>
    </div>
  );
}
