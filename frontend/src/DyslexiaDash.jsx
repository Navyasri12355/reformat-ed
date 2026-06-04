import React, { useState, useEffect, useRef } from 'react'

/*
  DyslexiaDash — Phase 2 update
  --------------------------------
  Accepts `transformedAtoms` (real AI-rewritten, dyslexia-friendly content).
  Falls back to static LESSONS if no atoms loaded.
*/

const STATIC_LESSONS = [
  {
    id: 1, title: 'What is Photosynthesis?',
    duration: '4 min read', subject: 'Biology',
    text: `Plants make their own food using sunlight.

They take in carbon dioxide from the air. They take in water from the soil. They use sunlight to turn these into glucose. Glucose is the plant's food.

This process is called photosynthesis. It happens inside the leaves. The leaves are green because of a substance called chlorophyll. Chlorophyll captures sunlight.

When photosynthesis happens, oxygen is released. This is the oxygen we breathe.`,
  },
  {
    id: 2, title: 'How Cells Divide', duration: '5 min read', subject: 'Biology',
    text: 'Cells divide to grow and repair. This is called mitosis.',
  },
  {
    id: 3, title: 'Newton\'s First Law', duration: '3 min read', subject: 'Physics',
    text: 'An object at rest stays at rest. An object in motion stays in motion.',
  },
]

function atomToLesson(atom, index) {
  const text = atom.rewritten_text || atom.text || atom.original_text || ''
  // Try to derive a title from the first non-empty line
  const firstLine = text.split('\n').find(l => l.trim().length > 0) || `Lesson ${index + 1}`
  const title = firstLine.length > 60 ? firstLine.slice(0, 57) + '…' : firstLine

  // Word count estimate for read time
  const words = text.split(/\s+/).length
  const minutes = Math.max(1, Math.ceil(words / 130))

  return {
    id: index + 1,
    title,
    duration: `${minutes} min read`,
    subject: 'Lesson',
    text,
  }
}

export default function DyslexiaDash({ studentName, onLogout, transformedAtoms = [] }) {
  const lessons = transformedAtoms.length > 0
    ? transformedAtoms.map((a, i) => atomToLesson(a, i))
    : STATIC_LESSONS

  const [lesson, setLesson]             = useState(lessons[0])
  const [playing, setPlaying]           = useState(false)
  const [wordIdx, setWordIdx]           = useState(-1)
  const [fontSize, setFontSize]         = useState(1.15)
  const [openDyslexic, setOpenDyslexic] = useState(true)
  const utterRef = useRef(null)

  const words = lesson.text.split(/(\s+)/).filter(w => w.trim().length > 0)

  // Stop speech on unmount or lesson change
  useEffect(() => () => window.speechSynthesis?.cancel(), [])

  const speak = () => {
    if (!window.speechSynthesis) return
    window.speechSynthesis.cancel()
    const utter = new SpeechSynthesisUtterance(lesson.text)
    utter.rate = 0.85
    utterRef.current = utter

    let i = 0
    utter.onboundary = (e) => {
      if (e.name === 'word') { setWordIdx(i); i++ }
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

  const selectLesson = (l) => { setLesson(l); stopSpeak() }
  const togglePlay = () => playing ? stopSpeak() : speak()

  const fontStyle = openDyslexic ? 'OpenDyslexic, sans-serif' : 'var(--font-body)'

  return (
    <div className="dys-root page-enter">
      <nav className="dys-topnav">
        <div className="dys-logo">🎧 NeuroLearn</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {transformedAtoms.length > 0 && (
            <span style={{
              fontSize: '0.72rem', fontFamily: 'var(--font-mono)',
              background: 'rgba(96,165,250,0.12)', border: '1px solid rgba(96,165,250,0.25)',
              borderRadius: 999, padding: '3px 10px', color: '#60a5fa',
            }}>
              ✦ AI-personalised
            </span>
          )}
          <span style={{ fontSize: '0.88rem', color: '#4a4a6a', fontFamily: fontStyle }}>
            Hi, {studentName}!
          </span>
          <button onClick={onLogout} style={{
            background: 'none', border: '2px solid #c8d9f8',
            borderRadius: 999, padding: '6px 14px',
            fontSize: '0.82rem', cursor: 'pointer', color: 'var(--dys-primary)',
            fontFamily: fontStyle,
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
            {lessons.map(l => (
              <div key={l.id}
                className="dys-lesson-card"
                style={{ borderColor: lesson.id === l.id ? 'var(--dys-primary)' : '' }}
                onClick={() => selectLesson(l)}
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
            fontFamily: fontStyle,
            lineHeight: 2,            // extra line height for dyslexia comfort
            letterSpacing: '0.02em',
          }}>
            {words.map((word, i) => (
              <span key={i} className={`dys-word ${wordIdx === i ? 'highlight' : ''}`}>
                {word}{' '}
              </span>
            ))}
          </div>

          {/* Controls */}
          <div className="dys-controls">
            <button id="dys-listen-btn" className={`dys-btn ${playing ? 'active' : ''}`} onClick={togglePlay}>
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

        {/* Tip */}
        <div style={{
          background: '#eef3fd', border: '2px solid #c8d9f8',
          borderRadius: 12, padding: '14px 18px',
          fontSize: '0.88rem', color: '#2a2a5a',
          fontFamily: fontStyle,
          lineHeight: 1.8,
        }}>
          💡 <strong>Tip:</strong> Use the font and size buttons above to adjust reading comfort anytime.
          Press Listen to hear the text read aloud with word highlighting.
        </div>
      </div>
    </div>
  )
}