import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { sessionsApi, transformsApi } from "../../api";
import type { StudentContent, TransformedAtom } from "../../api/types";
import { AtomRenderer } from "./AtomRenderer";
import { StudyTools } from "./StudyTools";
import { useSessionTracker } from "./hooks/useSessionTracker";
import { useTTS } from "./hooks/useTTS";
import { percent } from "../../utils/progress";

export function LearningSession() {
  const { documentId = "" } = useParams();
  const navigate = useNavigate();
  const [content, setContent] = useState<StudentContent | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const [preparing, setPreparing] = useState(true);

  // Poll for content: segments are committed one-by-one as they generate, so we
  // keep refreshing until the count stabilises (transform finished).
  useEffect(() => {
    let active = true;
    (async () => {
      let session;
      try {
        session = await sessionsApi.start(documentId);
      } catch {
        if (active)
          setError("Could not start a learning session. Please try again.");
        return;
      }
      if (!active) return;
      setSessionId(session.id);

      let prevCount = -1;
      let stable = 0;
      for (let i = 0; i < 60 && active; i++) {
        try {
          const data = await transformsApi.studentContent(documentId);
          if (!active) return;
          setContent(data);
          const n = data.atoms.length;
          if (n > 0 && n === prevCount) {
            stable += 1;
            if (stable >= 2) break; // count steady → generation done
          } else {
            stable = 0;
          }
          prevCount = n;
        } catch {
          /* transient; keep polling */
        }
        await new Promise((r) => setTimeout(r, 2500));
      }
      if (active) setPreparing(false);
    })();
    return () => {
      active = false;
    };
  }, [documentId]);

  if (error) return <div className="card center">{error}</div>;
  if (!content || !sessionId)
    return (
      <div className="center muted">Preparing your personalised lesson…</div>
    );
  if (content.atoms.length === 0)
    return (
      <div className="card center">
        {preparing ? (
          <>
            <p>Building your personalised version…</p>
            <p className="muted">
              Segments appear here as soon as they are ready.
            </p>
          </>
        ) : (
          <p>
            No content is ready yet. Tap “Prepare for me” on the lesson first.
          </p>
        )}
        <button className="btn btn-ghost" onClick={() => navigate("/")}>
          Back
        </button>
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
    adhdDominant ||
    atoms.some(
      (a) =>
        a.output_format === "adhd_gamified" || a.output_format === "blended",
    );

  if (done) {
    return (
      <div className="card center">
        <h2>Lesson complete!</h2>
        <p className="muted">
          Great work. We'll keep tuning this to how you learn best.
        </p>
        <button
          className="btn"
          onClick={async () => {
            await sessionsApi.end(sessionId);
            navigate("/");
          }}
        >
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
    (atom.output_format === "adhd_gamified" ||
      atom.output_format === "blended") &&
    !!atom.meta?.poll;
  const [pollPassed, setPollPassed] = useState(!hasPoll);
  const [showSupport, setShowSupport] = useState(false);

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
        pollPassed={pollPassed}
      />
      <div className="atom-controls">
        <button
          className="btn btn-ghost"
          onClick={() => {
            tracker.markSkip();
            onNext();
          }}
        >
          Skip
        </button>
        <button
          className={
            showSupport ? "btn btn-ghost btn-warn-active" : "btn btn-ghost"
          }
          onClick={() => {
            setShowSupport((v) => !v);
            tracker.markRetry();
          }}
        >
          I don't understand
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
          Got it
        </button>
      </div>

      {showSupport && <SupportSection atom={atom} />}
    </div>
  );
}

function SupportSection({ atom }: { atom: TransformedAtom }) {
  const [simplifiedText, setSimplifiedText] = useState("");
  const [loadingSimplified, setLoadingSimplified] = useState(false);
  const [question, setQuestion] = useState("");
  const [tutorAnswer, setTutorAnswer] = useState("");
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  // Speed and Pitch overrides
  const [rate, setRate] = useState(1.0);
  const [pitch, setPitch] = useState(1.0);

  const { speak, stop, isPlaying, supported } = useTTS({
    format: atom.output_format,
    rateOverride: rate,
    pitchOverride: pitch,
  });

  useEffect(() => {
    let active = true;
    setLoadingSimplified(true);
    transformsApi
      .getSupport(atom.id)
      .then((res) => {
        if (active) setSimplifiedText(res.response);
      })
      .catch(() => {
        if (active)
          setSimplifiedText(
            "Could not fetch simplified summary. Try reading the original concept slowly.",
          );
      })
      .finally(() => {
        if (active) setLoadingSimplified(false);
      });
    return () => {
      active = false;
    };
  }, [atom.id]);

  const ask = async () => {
    if (!question.trim()) return;
    setLoadingAnswer(true);
    try {
      const res = await transformsApi.getSupport(atom.id, question);
      setTutorAnswer(res.response);
    } catch {
      setTutorAnswer(
        "The tutor is offline. Please try again or ask your teacher.",
      );
    } finally {
      setLoadingAnswer(false);
    }
  };

  const sendFeedback = async () => {
    if (!feedback.trim()) return;
    setSubmittingFeedback(true);
    try {
      await transformsApi.submitFeedback(atom.id, feedback);
      setFeedbackSubmitted(true);
      setFeedback("");
    } catch {
      alert("Could not send feedback. Please try again.");
    } finally {
      setSubmittingFeedback(false);
    }
  };

  return (
    <div className="support-section">
      <h3 className="support-title">Personalized Support Panel</h3>

      {/* 1. Even Simpler Summary */}
      <div className="support-block">
        <h5>Even Simpler Summary</h5>
        {loadingSimplified ? (
          <div className="loading-dots">Preparing a simpler breakdown…</div>
        ) : (
          <div>
            <p className="support-text">{simplifiedText}</p>
            {supported && (
              <button
                className="btn btn-sm btn-ghost"
                onClick={() => (isPlaying ? stop() : speak(simplifiedText))}
              >
                {isPlaying ? "Stop" : "Listen to Summary"}
              </button>
            )}
          </div>
        )}
      </div>

      {/* 2. Ask Tutor */}
      <div className="support-block">
        <h5>Ask Your Personal Tutor</h5>
        <p className="muted" style={{ fontSize: "13px", margin: "4px 0" }}>
          Type a question about this step to get a response tailored to your
          style:
        </p>
        <div className="row" style={{ marginTop: "8px", width: "100%" }}>
          <input
            placeholder="e.g. What is the main key word here?"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            style={{ flex: 1, margin: 0 }}
          />
          <button
            className="btn btn-sm"
            onClick={ask}
            disabled={loadingAnswer || !question.trim()}
          >
            {loadingAnswer ? "Thinking…" : "Ask"}
          </button>
        </div>
        {tutorAnswer && (
          <div className="tutor-bubble">
            <p style={{ margin: 0 }}>
              <strong>Tutor:</strong> {tutorAnswer}
            </p>
            {supported && (
              <button
                className="btn btn-sm btn-ghost"
                onClick={() => (isPlaying ? stop() : speak(tutorAnswer))}
                style={{ marginTop: "6px" }}
              >
                {isPlaying ? "Stop" : "Listen to Answer"}
              </button>
            )}
          </div>
        )}
      </div>

      {/* 3. Audio & Voice Modulation Controls */}
      {supported && (
        <div className="support-block">
          <h5>Voice Modulation Controls</h5>
          <p
            className="muted"
            style={{ fontSize: "13px", marginBottom: "8px" }}
          >
            Adjust speed (rate) and pitch dynamically to customize how the notes
            sound:
          </p>
          <div className="voice-controls-grid">
            <div className="voice-slider-item">
              <span className="slider-label">
                Speech Speed (Rate): <b>{rate.toFixed(2)}x</b>
              </span>
              <input
                type="range"
                min="0.5"
                max="1.5"
                step="0.05"
                value={rate}
                onChange={(e) => setRate(parseFloat(e.target.value))}
                className="slider-input"
              />
            </div>
            <div className="voice-slider-item">
              <span className="slider-label">
                Voice Pitch: <b>{pitch.toFixed(2)}</b>
              </span>
              <input
                type="range"
                min="0.5"
                max="1.5"
                step="0.05"
                value={pitch}
                onChange={(e) => setPitch(parseFloat(e.target.value))}
                className="slider-input"
              />
            </div>
          </div>
        </div>
      )}

      {/* 4. Feedback to Teacher */}
      <div className="support-block">
        <h5>Direct Feedback to Teacher</h5>
        {feedbackSubmitted ? (
          <div className="feedback-success">
            Sent. Your teacher will see this in their dashboard.
          </div>
        ) : (
          <div>
            <textarea
              placeholder="Tell your teacher exactly what was confusing about this section..."
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              style={{ fontSize: "14px", margin: "6px 0", minHeight: "60px" }}
            />
            <button
              className="btn btn-sm btn-ghost"
              onClick={sendFeedback}
              disabled={submittingFeedback || !feedback.trim()}
              style={{ marginTop: "4px" }}
            >
              {submittingFeedback ? "Sending…" : "Send to Teacher"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
