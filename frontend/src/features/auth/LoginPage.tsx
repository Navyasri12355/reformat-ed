import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../auth/AuthContext";

export function LoginPage() {
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [role, setRole] = useState<"student" | "educator">("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const user =
        mode === "login"
          ? await login(email, password)
          : await register({ email, password, display_name: name || email, role });
      navigate(user.role === "student" ? "/" : "/educator");
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Something went wrong");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-wrap">
      <div className="card auth-card">
        <h1 className="brand">Neura<span>Core</span></h1>
        <p className="muted">Adaptive learning for every brain.</p>

        <div className="seg">
          <button className={mode === "login" ? "seg-btn active" : "seg-btn"} onClick={() => setMode("login")}>
            Log in
          </button>
          <button className={mode === "register" ? "seg-btn active" : "seg-btn"} onClick={() => setMode("register")}>
            Sign up
          </button>
        </div>

        <form onSubmit={submit}>
          {mode === "register" && (
            <>
              <label>Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
              <label>I am a…</label>
              <div className="seg">
                <button type="button" className={role === "student" ? "seg-btn active" : "seg-btn"} onClick={() => setRole("student")}>
                  Student
                </button>
                <button type="button" className={role === "educator" ? "seg-btn active" : "seg-btn"} onClick={() => setRole("educator")}>
                  Educator
                </button>
              </div>
            </>
          )}
          <label>Email</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} />
          {error && <p className="error">{error}</p>}
          <button className="btn btn-lg" type="submit" disabled={busy}>
            {busy ? "…" : mode === "login" ? "Log in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
