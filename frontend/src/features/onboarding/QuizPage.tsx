import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { profilesApi } from "../../api";
import type { QuizAnswer, QuizQuestion } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";

const OPTIONS: { value: QuizAnswer; label: string }[] = [
  { value: "never", label: "Never" },
  { value: "sometimes", label: "Sometimes" },
  { value: "often", label: "Often" },
  { value: "always", label: "Always" },
];

export function QuizPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<string, QuizAnswer>>({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    profilesApi.quizQuestions().then(setQuestions);
  }, []);

  const allAnswered = questions.length > 0 && questions.every((q) => answers[q.id]);

  const submit = async () => {
    if (!user) return;
    setSubmitting(true);
    try {
      await profilesApi.submitQuiz(user.id, answers);
      navigate("/");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="quiz">
      <h2>Let's learn how you learn</h2>
      <p className="muted">
        There are no right or wrong answers. This sets up your learning profile — your
        teacher can adjust it any time.
      </p>
      {questions.map((q, i) => (
        <div className="card quiz-q" key={q.id}>
          <p>
            <strong>{i + 1}.</strong> {q.text}
          </p>
          <div className="quiz-options">
            {OPTIONS.map((opt) => (
              <button
                key={opt.value}
                className={answers[q.id] === opt.value ? "chip chip-active" : "chip"}
                onClick={() => setAnswers((a) => ({ ...a, [q.id]: opt.value }))}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      ))}
      <button className="btn btn-lg" disabled={!allAnswered || submitting} onClick={submit}>
        {submitting ? "Saving…" : "Build my profile"}
      </button>
    </div>
  );
}
