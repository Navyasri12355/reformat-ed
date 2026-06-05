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

  return (
    <div>
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

      <h2>Your lessons</h2>
      {docs.length === 0 && <p className="muted">No lessons yet. Your teacher will upload some.</p>}
      <div className="doc-grid">
        {docs.map((d) => (
          <div className="card doc-card" key={d.id}>
            <h4>{d.file_name}</h4>
            <p className="muted">{d.parse_status === "complete" ? "Ready" : d.parse_status}</p>
            <div className="row">
              <button
                className="btn btn-ghost"
                disabled={busy === d.id || d.parse_status !== "complete"}
                onClick={() => prepare(d.id)}
              >
                {busy === d.id ? "Preparing…" : "Prepare for me"}
              </button>
              <button className="btn" onClick={() => navigate(`/learn/${d.id}`)}>
                Start learning
              </button>
            </div>
          </div>
        ))}
      </div>
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
