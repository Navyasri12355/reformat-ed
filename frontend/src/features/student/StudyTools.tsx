import { useEffect, useRef, useState } from "react";

/**
 * Ambient ADHD support tools, shown for ADHD / blended learners:
 *  • Pomodoro timer (10/15/25) with a gentle pulse nudge at the halfway point
 *  • one-button distraction-free mode (also toggled with the F key)
 *  • a sticky-note "impulse pad" to park off-task thoughts
 */
export function StudyTools() {
  const [openPomo, setOpenPomo] = useState(false);
  const [openNote, setOpenNote] = useState(false);
  const [note, setNote] = useState("");

  const [total, setTotal] = useState(600);
  const [left, setLeft] = useState(600);
  const [running, setRunning] = useState(false);
  const [pulse, setPulse] = useState(false);
  const tick = useRef<number | null>(null);

  // Distraction-free mode toggles a body class (CSS hides chrome).
  const [focus, setFocus] = useState(false);
  useEffect(() => {
    document.body.classList.toggle("focus-mode", focus);
    return () => document.body.classList.remove("focus-mode");
  }, [focus]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key.toLowerCase() === "f" && !/input|textarea/i.test((e.target as HTMLElement).tagName)) {
        setFocus((f) => !f);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (!running) {
      if (tick.current) window.clearInterval(tick.current);
      return;
    }
    tick.current = window.setInterval(() => {
      setLeft((l) => {
        if (l <= 1) {
          setRunning(false);
          setPulse(true);
          return 0;
        }
        if (l - 1 === Math.floor(total / 2)) setPulse(true);
        return l - 1;
      });
    }, 1000);
    return () => {
      if (tick.current) window.clearInterval(tick.current);
    };
  }, [running, total]);

  const fmt = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2, "0")}:${String(s % 60).padStart(2, "0")}`;

  const setMinutes = (m: number) => {
    setRunning(false);
    setTotal(m * 60);
    setLeft(m * 60);
    setPulse(false);
  };

  return (
    <>
      {focus && (
        <div className="focus-banner">
          <span>🎯 Distraction-free mode — only the lesson is showing.</span>
          <button className="btn btn-sm btn-ghost" onClick={() => setFocus(false)}>
            Exit (F)
          </button>
        </div>
      )}

      <div className="study-fabs">
        <button className="fab" title="Distraction-free mode (F)" onClick={() => setFocus((f) => !f)}>
          🎯
        </button>
        <button className="fab" title="Impulse pad" onClick={() => setOpenNote((v) => !v)}>
          📝
        </button>
        <button className="fab" title="Focus timer" onClick={() => setOpenPomo((v) => !v)}>
          ⏱️
        </button>
      </div>

      {openPomo && (
        <div className={pulse ? "pomo pulse" : "pomo"}>
          <div className="row-between">
            <b>Focus timer</b>
            <span className="note">{running ? "focusing" : pulse ? "break time 🌿" : "ready"}</span>
          </div>
          <div className="pomo-time">{fmt(left)}</div>
          <div className="row" style={{ justifyContent: "center" }}>
            {[10, 15, 25].map((m) => (
              <button key={m} className="btn btn-sm btn-ghost" onClick={() => setMinutes(m)}>
                {m}
              </button>
            ))}
          </div>
          <div className="row" style={{ justifyContent: "center", marginTop: 8 }}>
            <button
              className="btn btn-sm"
              onClick={() => {
                setPulse(false);
                setRunning((r) => !r);
              }}
            >
              {running ? "Pause" : "Start"}
            </button>
            <button className="btn btn-sm btn-ghost" onClick={() => setMinutes(total / 60)}>
              Reset
            </button>
          </div>
        </div>
      )}

      {openNote && (
        <div className="notepad">
          <div className="row-between">
            <b>Impulse pad</b>
            <span className="note">stays off the lesson</span>
          </div>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Park a thought here so it doesn't pull you off task…"
          />
        </div>
      )}
    </>
  );
}
