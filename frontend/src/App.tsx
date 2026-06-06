import { useState } from "react";
import { Link, Route, Routes, useNavigate } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { LoginPage } from "./features/auth/LoginPage";
import { QuizPage } from "./features/onboarding/QuizPage";
import { StudentHome } from "./features/student/StudentHome";
import { LearningSession } from "./features/student/LearningSession";
import { EducatorDashboard } from "./features/educator/EducatorDashboard";
import { ReviewQueue } from "./features/educator/ReviewQueue";
import { AnalyticsPage } from "./features/educator/AnalyticsPage";

function TopBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  return (
    <header className="topbar">
      <Link to="/" className="brand sm">
        Neura<span>Core</span>
      </Link>
      <nav>
        {user.role === "student" && <Link to="/">My lessons</Link>}
        {(user.role === "educator" || user.role === "admin") && (
          <>
            <Link to="/educator">Dashboard</Link>
            <Link to="/educator/review">Review</Link>
          </>
        )}
      </nav>
      <div className="topbar-right">
        <span className="muted">{user.display_name}</span>
        <button
          className="btn btn-sm btn-ghost"
          onClick={() => {
            logout();
            navigate("/login");
          }}
        >
          Log out
        </button>
      </div>
    </header>
  );
}

function ThemeToggle() {
  const [theme, setTheme] = useState<string>(
    () => document.documentElement.getAttribute("data-theme") || "light",
  );
  const toggle = () => {
    const next = theme === "dark" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
  };
  return (
    <button className="theme-toggle" onClick={toggle} aria-label="Toggle dark mode">
      {theme === "dark" ? "Light mode" : "Dark mode"}
    </button>
  );
}

export default function App() {
  return (
    <>
      <TopBar />
      <ThemeToggle />
      <main className="container">
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute roles={["student"]}>
                <StudentHome />
              </ProtectedRoute>
            }
          />
          <Route
            path="/onboarding"
            element={
              <ProtectedRoute roles={["student"]}>
                <QuizPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/learn/:documentId"
            element={
              <ProtectedRoute roles={["student"]}>
                <LearningSession />
              </ProtectedRoute>
            }
          />

          <Route
            path="/educator"
            element={
              <ProtectedRoute roles={["educator", "admin"]}>
                <EducatorDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/educator/review"
            element={
              <ProtectedRoute roles={["educator", "admin"]}>
                <ReviewQueue />
              </ProtectedRoute>
            }
          />
          <Route
            path="/educator/analytics/:documentId"
            element={
              <ProtectedRoute roles={["educator", "admin"]}>
                <AnalyticsPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </>
  );
}
