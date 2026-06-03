import React, { useState } from 'react'

/*
  Default questions — the teacher / developer can replace these.
  Each question has a set of options, each option gives points toward a profile.
*/
const DEFAULT_QUESTIONS = [
  {
    id: 1,
    text: 'When you\'re learning something new, which feels easiest?',
    options: [
      { label: 'Quick bullet points or short summaries',        scores: { adhd: 3, dyslexia: 1, asd: 0 } },
      { label: 'Listening to someone explain it out loud',      scores: { adhd: 1, dyslexia: 3, asd: 0 } },
      { label: 'A clear numbered list of steps to follow',      scores: { adhd: 0, dyslexia: 0, asd: 3 } },
      { label: 'Reading a well-organised document',             scores: { adhd: 0, dyslexia: 0, asd: 1 } },
    ],
  },
  {
    id: 2,
    text: 'How do you feel about long blocks of text?',
    options: [
      { label: 'I lose focus and start skimming after a few lines', scores: { adhd: 3, dyslexia: 1, asd: 0 } },
      { label: 'The letters sometimes blur or jump around',          scores: { adhd: 0, dyslexia: 3, asd: 0 } },
      { label: 'Fine, as long as it\'s structured and consistent',   scores: { adhd: 0, dyslexia: 0, asd: 3 } },
      { label: 'I\'m okay with them if I\'m interested',            scores: { adhd: 1, dyslexia: 1, asd: 1 } },
    ],
  },
  {
    id: 3,
    text: 'Which kind of task feels most satisfying to complete?',
    options: [
      { label: 'A short challenge with a clear reward at the end', scores: { adhd: 3, dyslexia: 0, asd: 0 } },
      { label: 'Listening and answering questions verbally',        scores: { adhd: 0, dyslexia: 3, asd: 0 } },
      { label: 'Following a predictable routine with no surprises', scores: { adhd: 0, dyslexia: 0, asd: 3 } },
      { label: 'Solving a puzzle step by step',                     scores: { adhd: 1, dyslexia: 0, asd: 2 } },
    ],
  },
  {
    id: 4,
    text: 'How do you feel about open-ended tasks with no clear instructions?',
    options: [
      { label: 'I jump right in — I\'ll figure it out as I go',  scores: { adhd: 3, dyslexia: 1, asd: 0 } },
      { label: 'I prefer someone to talk me through it first',    scores: { adhd: 0, dyslexia: 2, asd: 0 } },
      { label: 'I need a detailed list of steps before I start',  scores: { adhd: 0, dyslexia: 0, asd: 3 } },
      { label: 'Slightly uncomfortable but manageable',           scores: { adhd: 1, dyslexia: 1, asd: 1 } },
    ],
  },
  {
    id: 5,
    text: 'In a classroom, which bothers you most?',
    options: [
      { label: 'Sitting still for too long without doing something active', scores: { adhd: 3, dyslexia: 0, asd: 0 } },
      { label: 'Being asked to read aloud in front of others',              scores: { adhd: 0, dyslexia: 3, asd: 0 } },
      { label: 'Unexpected changes to the schedule or routine',             scores: { adhd: 0, dyslexia: 0, asd: 3 } },
      { label: 'Noisy or chaotic environments',                             scores: { adhd: 1, dyslexia: 0, asd: 2 } },
    ],
  },
]

export default function Quiz({ studentName, onComplete }) {
  const [questions]  = useState(DEFAULT_QUESTIONS)
  const [current, setCurrent] = useState(0)
  const [answers, setAnswers] = useState({})   // { questionId: optionIndex }
  const [done, setDone]       = useState(false)
  const [result, setResult]   = useState(null)

  const q = questions[current]
  const selected = answers[q.id]

  const choose = (idx) => setAnswers(a => ({ ...a, [q.id]: idx }))

  const next = () => {
    if (current < questions.length - 1) {
      setCurrent(c => c + 1)
    } else {
      // Tally
      const totals = { adhd: 0, dyslexia: 0, asd: 0 }
      Object.entries(answers).forEach(([qid, optIdx]) => {
        const qs = questions.find(q => q.id === +qid)
        const scores = qs.options[optIdx].scores
        Object.entries(scores).forEach(([k, v]) => { totals[k] += v })
      })
      const winner = Object.entries(totals).sort((a, b) => b[1] - a[1])[0][0]
      setResult({ totals, winner })
      setDone(true)
    }
  }

  const pct = Math.round(((current + (selected !== undefined ? 1 : 0)) / questions.length) * 100)

  if (done && result) {
    const labels = { adhd: '⚡ ADHD', dyslexia: '🎧 Dyslexia', asd: '🧩 ASD' }
    const descs = {
      adhd:     'Your content will be rewritten as short, gamified missions with clear goals and progress tracking.',
      dyslexia: 'Your content will be audio-first with dyslexia-friendly fonts, wide spacing, and word-by-word highlighting.',
      asd:      'Your content will be structured as numbered, predictable steps with no visual noise or surprises.',
    }
    return (
      <div className="quiz-screen page-enter">
        <div className="quiz-box" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '3rem', marginBottom: 16 }}>
            {{ adhd: '⚡', dyslexia: '🎧', asd: '🧩' }[result.winner]}
          </div>
          <div style={{
            fontFamily: 'var(--font-display)', fontWeight: 800,
            fontSize: '1.6rem', marginBottom: 8,
          }}>
            {labels[result.winner]} Profile
          </div>
          <p style={{ color: 'var(--muted)', fontSize: '0.92rem', marginBottom: 28, lineHeight: 1.7 }}>
            {descs[result.winner]}
          </p>

          {/* Score breakdown */}
          <div style={{ textAlign: 'left', marginBottom: 32 }}>
            {Object.entries(result.totals).map(([k, v]) => {
              const max = Math.max(...Object.values(result.totals))
              return (
                <div key={k} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, textTransform: 'capitalize' }}>{k}</span>
                    <span style={{ color: 'var(--muted)' }}>{v} pts</span>
                  </div>
                  <div className="progress-track">
                    <div className="progress-fill" style={{
                      width: `${(v / max) * 100}%`,
                      background: k === result.winner ? 'var(--accent-green)' : 'var(--border)',
                    }} />
                  </div>
                </div>
              )
            })}
          </div>

          <button className="btn btn-primary" onClick={() => onComplete(result.winner)}
            style={{ width: '100%', justifyContent: 'center' }}>
            Go to My Dashboard →
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="quiz-screen page-enter">
      <div className="quiz-box">
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <div className="quiz-step">Question {current + 1} of {questions.length}</div>
          <div className="progress-track" style={{ marginBottom: 0 }}>
            <div className="progress-fill" style={{ width: `${pct}%`, background: 'var(--accent-blue)' }} />
          </div>
        </div>

        <div style={{
          fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: '0.9rem',
          color: 'var(--muted)', marginBottom: 6,
        }}>Hey {studentName} —</div>
        <div className="quiz-q">{q.text}</div>

        <div className="quiz-options">
          {q.options.map((opt, i) => (
            <button
              key={i}
              className={`quiz-option ${selected === i ? 'selected' : ''}`}
              onClick={() => choose(i)}
            >
              {opt.label}
            </button>
          ))}
        </div>

        <div className="quiz-nav">
          {current > 0 ? (
            <button className="btn btn-outline btn-sm" onClick={() => setCurrent(c => c - 1)}>← Back</button>
          ) : <div />}
          <button
            className="btn btn-primary btn-sm"
            disabled={selected === undefined}
            onClick={next}
            style={{ opacity: selected === undefined ? 0.4 : 1, cursor: selected === undefined ? 'not-allowed' : 'pointer' }}
          >
            {current < questions.length - 1 ? 'Next →' : 'See My Profile →'}
          </button>
        </div>
      </div>
    </div>
  )
}