import React, { useState, useEffect, useRef } from 'react'

const LESSONS = [
  {
    id: 1, title: 'What is Photosynthesis?',
    duration: '4 min read', subject: 'Biology',
    text: `Plants make their own food using sunlight.

They take in carbon dioxide from the air. They take in water from the soil. They use sunlight to turn these into glucose. Glucose is the plant's food.

This process is called photosynthesis. It happens inside the leaves. The leaves are green because of a substance called chlorophyll. Chlorophyll captures sunlight.

When photosynthesis happens, oxygen is released. This is the oxygen we breathe.`,
  },
  {
    id: 2, title: 'How Cells Divide', duration: '5 min read', subject: 'Biology', text: 'Cells divide to grow and repair. This is called mitosis.',
  },
  {
    id: 3, title: 'Newton\'s First Law', duration: '3 min read', subject: 'Physics', text: 'An object at rest stays at rest. An object in motion stays in motion.',
  },
]

export default function DyslexiaDash({ studentName, onLogout }) {
  const [lesson, setLesson]         = useState(LESSONS[0])
  const [playing, setPlaying]       = useState(false)
  const [wordIdx, setWordIdx]       = useState(-1)
  const [fontSize, setFontSize]     = useState(1.15)
  const [openDyslexic, setOpenDyslexic] = useState(true)
  const utterRef = useRef(null)
  const words = lesson.text.split(/(\s+)/).filter(w => w.trim().length > 0)

  // Stop speech on unmount
  useEffect(() => () => window.speechSynthesis?.cancel(), [])

  const speak = () => {
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const utter = new SpeechSynthesisUtterance(lesson.text)
    utter.rate = 0.85
    utterRef.current = utter

    let i = 0
    utter.onboundary = (e) => {
      if (e.name === 'word') {
        setWordIdx(i)
        i++
      }
    }
    utter.onend = () => { setPlaying(false); setWordIdx(-1) }

    setPlaying(true)
    window.speechSynthesis.speak(utter)
  }

  const stopSpeak = () => {
    window.speechSynthesis?.cancel()
    setPlaying(false)
    setWordIdx(-1)
  }

  const togglePlay = () => playing ? stopSpeak() : speak()

  return (
    <div className="dys-root page-enter">
      <nav className="dys-topnav">
        <div className="dys-logo">🎧 NeuroLearn</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: '0.88rem', color: '#4a4a6a', fontFamily: openDyslexic ? 'OpenDyslexic' : 'inherit' }}>
            Hi, {studentName}!
          </span>
          <button onClick={onLogout} style={{
            background: 'none', border: '2px solid #c8d9f8',
            borderRadius: 999, padding: '6px 14px',
            fontSize: '0.82rem', cursor: 'pointer', color: 'var(--dys-primary)',
            fontFamily: openDyslexic ? 'OpenDyslexic' : 'inherit',
          }}>Exit</button>
        </div>
      </nav>

      <div className="dys-body">
        <h1 className="dys-greeting">Hello, <span>{studentName}</span>!</h1>
        <p className="dys-sub">Here is today's lesson. Press play to listen along.</p>

        {/* Lesson selector */}
        <div style={{ marginBottom: 28 }}>
          <div style={{ fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--dys-primary)', marginBottom: 10 }}>
            All Lessons
          </div>
          <div className="dys-lesson-list">
            {LESSONS.map(l => (
              <div key={l.id}
                className="dys-lesson-card"
                style={{ borderColor: lesson.id === l.id ? 'var(--dys-primary)' : '' }}
                onClick={() => { setLesson(l); stopSpeak() }}
              >
                <div className="dys-lesson-title" style={{ fontFamily: openDyslexic ? 'OpenDyslexic' : 'var(--font-display)' }}>
                  {l.title}
                </div>
                <div className="dys-lesson-meta">{l.subject} · {l.duration}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Main reading card */}
        <div className="dys-audio-card">
          <div className="dys-audio-label">📖 {lesson.subject} — {lesson.title}</div>

          {/* Rendered text with word highlighting */}
          <div className="dys-content-text" style={{
            fontSize: `${fontSize}rem`,
            fontFamily: openDyslexic ? 'OpenDyslexic, sans-serif' : 'var(--font-body)',
          }}>
            {words.map((word, i) => (
              <span key={i} className={`dys-word ${wordIdx === i ? 'highlight' : ''}`}>
                {word}{' '}
              </span>
            ))}
          </div>

          {/* Controls */}
          <div className="dys-controls">
            <button className={`dys-btn ${playing ? 'active' : ''}`} onClick={togglePlay}>
              {playing ? '⏹ Stop' : '▶ Listen'}
            </button>
            <button className="dys-btn dys-font-btn" onClick={() => setFontSize(f => Math.min(f + 0.1, 1.7))}>
              A+
            </button>
            <button className="dys-btn dys-font-btn" onClick={() => setFontSize(f => Math.max(f - 0.1, 0.9))}>
              A−
            </button>
            <button
              className={`dys-btn dys-font-btn ${openDyslexic ? 'active' : ''}`}
              onClick={() => setOpenDyslexic(v => !v)}
            >
              {openDyslexic ? 'Standard Font' : 'OpenDyslexic'}
            </button>
          </div>
        </div>

        {/* Accessibility note */}
        <div style={{
          background: '#eef3fd', border: '2px solid #c8d9f8',
          borderRadius: 12, padding: '14px 18px',
          fontSize: '0.88rem', color: '#2a2a5a',
          fontFamily: openDyslexic ? 'OpenDyslexic, sans-serif' : 'var(--font-body)',
        }}>
          💡 <strong>Tip:</strong> You can use the font and size buttons above to adjust reading comfort anytime.
        </div>
      </div>
    </div>
  )
}