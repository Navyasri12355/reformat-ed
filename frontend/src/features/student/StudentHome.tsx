import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { documentsApi, profilesApi, transformsApi } from "../../api";
import type { DocumentOut, ProfileWeights } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";

export function StudentHome() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [docs, setDocs] = useState<DocumentOut[]>([]);
  const [profile, setProfile] = useState<ProfileWeights | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    documentsApi.list().then(setDocs).catch(() => setDocs([]));
    profilesApi.get(user.id).then(setProfile).catch(() => setProfile(null));
  }, [user]);

  // Clean up speech synthesis when component unmounts
  useEffect(() => {
    return () => {
      window.speechSynthesis.cancel();
    };
  }, []);

  const needsQuiz =
    profile &&
    profile.adhd_weight === 0 &&
    profile.dyslexia_weight === 0 &&
    profile.asd_weight === 0;

  const prepare = async (docId: string) => {
    setBusy(docId);
    try {
      await transformsApi.request(docId);
      alert("Your version is being prepared. Your teacher will approve it shortly.");
    } catch (e) {
      alert("Could not start preparation. Complete your profile quiz first.");
    } finally {
      setBusy(null);
    }
  };

  const adhdActive = profile ? profile.adhd_weight > 0.40 : false;
  const dyslexiaActive = profile ? profile.dyslexia_weight > 0.40 : false;
  const asdActive = profile ? profile.asd_weight > 0.40 : false;

  const speakProgress = () => {
    if (!profile) return;
    const completedCount = docs.filter((d) => d.parse_status === "complete").length;
    const text = `Hello. Here is your learning progress summary. You have ${docs.length} lessons available, and ${completedCount} of them are ready to learn. Your cognitive profile weights are: ADHD ${Math.round(profile.adhd_weight * 100)} percent, Dyslexia ${Math.round(profile.dyslexia_weight * 100)} percent, and Autism ${Math.round(profile.asd_weight * 100)} percent. Keep up the great work!`;
    
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.85; // slightly slower for better comprehensibility
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className={dyslexiaActive ? "fmt-dyslexia" : ""}>
      {needsQuiz && (
        <div className="banner">
          You haven't set up your learning profile yet.{" "}
          <button className="btn btn-sm" onClick={() => navigate("/onboarding")}>
            Take the quick quiz
          </button>
        </div>
      )}

      {profile && !needsQuiz && (
        <div className="card profile-strip">
          <span>Your profile:</span>
          <Bar label="ADHD" value={profile.adhd_weight} color="#ff7a59" />
          <Bar label="Dyslexia" value={profile.dyslexia_weight} color="#3aa7ff" />
          <Bar label="ASD" value={profile.asd_weight} color="#7c5cff" />
          <button className="btn btn-sm btn-ghost" onClick={() => navigate("/onboarding")}>
            Retake quiz
          </button>
        </div>
      )}

      {/* Trait-Specific Personalization Section */}
      {profile && !needsQuiz && (
        <div style={{ marginBottom: "24px" }}>
          {/* ADHD Personalization Widget */}
          {adhdActive && (
            <div className="streak-card">
              <span className="streak-fire" role="img" aria-label="fire">🔥</span>
              <div>
                <h4 style={{ margin: "0 0 4px 0", color: "#ff7a59" }}>4-Day Learning Streak!</h4>
                <p style={{ margin: 0, fontSize: "15px" }}>You are in the zone. Keep up the momentum to secure your achievements today!</p>
                <div className="tips-box">
                  <h5>💡 ADHD Focus Tip</h5>
                  <p style={{ margin: 0 }}>To stay focused, clear your desk, put your phone on silent, and complete one small challenge at a time.</p>
                </div>
              </div>
            </div>
          )}

          {/* Dyslexia Personalization Widget */}
          {dyslexiaActive && (
            <div className="card" style={{ borderLeft: "5px solid #3aa7ff", backgroundColor: "#f6faff" }}>
              <h4 style={{ color: "#2f8fe0", margin: "0 0 6px 0" }}>🔊 Audio Reader Assistant</h4>
              <p style={{ fontSize: "15px", margin: "0 0 12px 0" }}>
                You have dyslexia mode active. OpenDyslexic font has been applied across the whole dashboard. If you'd like, we can read out your progress.
              </p>
              <button className="btn btn-sm" style={{ backgroundColor: "#3aa7ff" }} onClick={speakProgress}>
                Listen to my progress
              </button>
            </div>
          )}

          {/* ASD Personalization Widget */}
          {asdActive && (
            <div className="card" style={{ borderLeft: "5px solid #7c5cff", backgroundColor: "#faf9ff" }}>
              <h4 style={{ color: "#7c5cff", margin: "0 0 8px 0" }}>🧩 Visual Learning Schedule</h4>
              <p className="muted" style={{ marginBottom: "12px", fontSize: "14px" }}>
                Here is your literal, step-by-step structure for completing lessons. There are no time limits or surprises.
              </p>
              <div className="schedule">
                <div className="st"><b>1</b> Select a lesson from your structured list.</div>
                <div className="st"><b>2</b> Click <strong>Prepare</strong> if it's not ready.</div>
                <div className="st"><b>3</b> Click <strong>Start lesson</strong> to learn.</div>
                <div className="st"><b>4</b> Review the concept flowchart.</div>
                <div className="st"><b>5</b> Take the check-in quiz.</div>
              </div>
              <div className="asd-panel" style={{ marginTop: "14px", border: "1px solid #e2dfff" }}>
                <h4>📋 Study Rubric & Guidelines</h4>
                <ul className="asd-steps" style={{ margin: "6px 0 0 0", paddingLeft: "20px" }}>
                  <li>Read paragraphs slowly. All idioms are rewritten with literal meanings.</li>
                  <li>Toggle the concept flowchart to see links between keywords.</li>
                  <li>Submit your check-in answer. Multiple attempts are allowed.</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="row-between">
        <h2>Your lessons</h2>
        <a className="btn btn-sm btn-ghost" href="/simulator.html" target="_blank" rel="noreferrer">
          Explore all formats ↗
        </a>
      </div>
      
      {docs.length === 0 && <p className="muted">No lessons yet. Your teacher will upload some.</p>}

      {/* Lesson View: Personalized List vs Grid */}
      {asdActive && docs.length > 0 ? (
        <div className="asd-schedule-list">
          {docs.map((d, index) => (
            <div className="card asd-schedule-item" key={d.id}>
              <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                <div style={{
                  width: "36px",
                  height: "36px",
                  borderRadius: "50%",
                  backgroundColor: "#7c5cff",
                  color: "#fff",
                  display: "grid",
                  placeItems: "center",
                  fontWeight: "bold",
                  fontSize: "15px"
                }}>
                  {index + 1}
                </div>
                <div>
                  <h4 style={{ margin: "0 0 2px 0" }}>{d.file_name}</h4>
                  <span className="muted" style={{ fontSize: "13px" }}>
                    Status: {d.parse_status === "complete" ? "Ready" : d.parse_status}
                  </span>
                </div>
              </div>
              <div className="row" style={{ flexWrap: "nowrap" }}>
                <button
                  className="btn btn-ghost btn-sm"
                  disabled={busy === d.id || d.parse_status !== "complete"}
                  onClick={() => prepare(d.id)}
                >
                  {busy === d.id ? "Preparing…" : "Prepare"}
                </button>
                <button className="btn btn-sm" style={{ backgroundColor: "#7c5cff" }} onClick={() => navigate(`/learn/${d.id}`)}>
                  Start lesson
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="doc-grid">
          {docs.map((d) => (
            <div className="card doc-card" key={d.id}>
              {adhdActive && (
                <span className="format-badge badge-adhd" style={{ marginBottom: "10px" }}>
                  ⚡ ACTIVE CHALLENGE
                </span>
              )}
              {dyslexiaActive && (
                <span className="format-badge badge-dyslexia" style={{ marginBottom: "10px" }}>
                  📖 READABLE LESSON
                </span>
              )}
              <h4>{d.file_name}</h4>
              <p className="muted">{d.parse_status === "complete" ? "Ready" : d.parse_status}</p>
              <div className="row" style={{ marginTop: "12px" }}>
                <button
                  className="btn btn-ghost btn-sm"
                  disabled={busy === d.id || d.parse_status !== "complete"}
                  onClick={() => prepare(d.id)}
                >
                  {busy === d.id ? "Preparing…" : "Prepare for me"}
                </button>
                <button className="btn btn-sm" onClick={() => navigate(`/learn/${d.id}`)}>
                  Start learning
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Bar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="mini-bar">
      <span className="mini-bar-label">{label}</span>
      <div className="mini-bar-track">
        <div className="mini-bar-fill" style={{ width: `${value * 100}%`, background: color }} />
      </div>
      <span className="mini-bar-val">{Math.round(value * 100)}%</span>
    </div>
  );
}

