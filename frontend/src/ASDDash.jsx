import React, { useState } from 'react'

/*
  ASDDash — Phase 2 update
  --------------------------
  Accepts `transformedAtoms` (AI-rewritten, ASD-structured content).
  Falls back to static LESSON_CONTENT if no atoms loaded.

  The ASD prompt produces a numbered, predictable format:
    🔢 Topic: <one sentence>
    1. <fact>
    2. <fact>
    ...
    Summary: <closing sentence>

  We parse that structure and display it section-by-section.
*/

const STATIC_SCHEDULE = [
  {
    id: 1, title: 'Step 1 — Review Yesterday',
    desc: 'Look at your notes from the last session. You learned about plant cells. This step takes about 3 minutes.',
    time: '~3 min', status: 'done',
  },
  {
    id: 2, title: 'Step 2 — Read Today\'s Lesson',
    desc: 'Read the text below carefully. There are 5 short paragraphs. Read one at a time. Do not skip any.',
    time: '~8 min', status: 'current',
  },
  {
    id: 3, title: 'Step 3 — Answer 3 Questions',
    desc: 'After reading, you will answer 3 questions. The questions are about what you just read. There are no trick questions.',
    time: '~5 min', status: 'upcoming',
  },
  {
    id: 4, title: 'Step 4 — Mark as Complete',
    desc: 'When you finish the questions, click the "Done" button. This saves your progress.',
    time: '~1 min', status: 'upcoming',
  },
]

const STATIC_LESSON_CONTENT = [
  {
    heading: 'First: What is Photosynthesis?',
    text: 'Photosynthesis is a process. Plants use this process to make food. The food is called glucose.',
  },
  {
    heading: 'Next: What does a plant need?',
    text: 'A plant needs three things: sunlight, water, and carbon dioxide. These are the inputs. Nothing else is required.',
  },
  {
    heading: 'Then: Where does it happen?',
    text: 'Photosynthesis happens inside the leaves. Specifically, it happens in structures called chloroplasts. Chloroplasts contain chlorophyll. Chlorophyll is green.',
  },
  {
    heading: 'Then: What is the output?',
    text: 'The plant produces glucose and oxygen. The glucose feeds the plant. The oxygen goes into the air. We breathe that oxygen.',
  },
  {
    heading: 'Finally: Why does this matter?',
    text: 'All animals depend on plants for oxygen. Without photosynthesis, there would be no oxygen on Earth. Photosynthesis is essential for life.',
  },
]

// Parse the AI-rewritten ASD text into structured sections.
// ASD prompt format:
//   🔢 Topic: ...
//   1. fact
//   2. fact
//   Summary: ...
function parseASDAtom(rewrittenText, index) {
  const lines = rewrittenText.split('\n').map(l => l.trim()).filter(Boolean)

  // Extract topic line
  const topicLine = lines.find(l => /topic:/i.test(l)) || lines[0]
  const topic = topicLine.replace(/^🔢\s*/,'').replace(/^topic:\s*/i,'').trim()

  // Extract numbered facts
  const facts = lines.filter(l => /^\d+[\.\)›]/.test(l))
    .map(l => l.replace(/^\d+[\.\)›]\s*/, '').trim())

  // Extract summary
  const summaryLine = lines.find(l => /^summary:/i.test(l))
  const summary = summaryLine ? summaryLine.replace(/^summary:\s*/i,'').trim() : null

  // Build sections — topic + each fact is a section for easy pagination
  const sections = []
  if (topic) sections.push({ heading: `Topic: ${topic}`, text: topic })
  facts.forEach((f, i) => {
    sections.push({
      heading: `${['First', 'Next', 'Then', 'Then', 'Finally', 'Next'][i] || `Step ${i + 1}`}: Fact ${i + 1}`,
      text: f,
    })
  })
  if (summary) sections.push({ heading: 'Summary', text: summary })

  return sections.length > 0 ? sections : [{ heading: `Lesson ${index + 1}`, text: rewrittenText }]
}

export default function ASDDash({ studentName, onLogout, transformedAtoms = [] }) {
  // Build lesson content from real atoms or fall back to static
  const hasRealContent = transformedAtoms.length > 0
  const allSections = hasRealContent
    ? transformedAtoms.flatMap((a, i) => parseASDAtom(a.rewritten_text || a.text || '', i))
    : STATIC_LESSON_CONTENT

  const [schedule, setSchedule]     = useState(STATIC_SCHEDULE)
  const [lessonStep, setLessonStep] = useState(0)

  const advanceSchedule = () => {
    setSchedule(prev => {
      const cur = prev.findIndex(s => s.status === 'current')
      if (cur === -1 || cur === prev.length - 1) return prev
      return prev.map((s, i) => {
        if (i === cur) return { ...s, status: 'done' }
        if (i === cur + 1) return { ...s, status: 'current' }
        return s
      })
    })
  }

  const today = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })
  const doneCount = schedule.filter(s => s.status === 'done').length

  const currentSection = allSections[lessonStep] || allSections[0]

  return (
    <div className="asd-root page-enter">
      <nav className="asd-topnav">
        <div className="asd-logo">🧩 NeuroLearn</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {hasRealContent && (
            <span style={{
              fontSize: '0.72rem', fontFamily: 'var(--font-mono)',
              background: '#e6f9f1', border: '1px solid #b7e8d2',
              borderRadius: 6, padding: '3px 10px', color: 'var(--asd-primary)',
            }}>
              AI-structured content
            </span>
          )}
          <span style={{ fontSize: '0.88rem', color: '#555' }}>Hello, {studentName}</span>
          <button onClick={onLogout} style={{
            background: 'none', border: '2px solid #ddd',
            borderRadius: 8, padding: '6px 14px',
            fontSize: '0.82rem', cursor: 'pointer', color: '#555',
          }}>Exit</button>
        </div>
      </nav>

      <div className="asd-body">

        {/* Today header */}
        <div className="asd-today-bar">
          <div>
            <div className="asd-today-label">Today</div>
            <div className="asd-today-val">{today}</div>
          </div>
          <div style={{ width: '1.5px', height: 36, background: '#d0ead8' }} />
          <div>
            <div className="asd-today-label">Subject</div>
            <div className="asd-today-val">
              {hasRealContent ? `${transformedAtoms.length} lesson${transformedAtoms.length > 1 ? 's' : ''} loaded` : 'Biology — Photosynthesis'}
            </div>
          </div>
          <div style={{ width: '1.5px', height: 36, background: '#d0ead8' }} />
          <div>
            <div className="asd-today-label">Progress</div>
            <div className="asd-today-val" style={{ color: 'var(--asd-primary)' }}>
              {doneCount} of {schedule.length} steps done
            </div>
          </div>
        </div>

        {/* Rule box */}
        <div className="asd-rule-box">
          <strong>Important:</strong> Complete each step in order. Do not skip any steps.
          You will know which step to do because it is labelled <strong>"Current Step"</strong>.
        </div>

        {/* Schedule */}
        <div style={{ marginBottom: 36 }}>
          <div className="asd-section-label">Today's Steps — Do These in Order</div>
          <div className="asd-steps">
            {schedule.map(s => (
              <div key={s.id} className={`asd-step ${s.status}`}>
                <div className="asd-step-num">
                  {s.status === 'done' ? '✓' : s.id}
                </div>
                <div className="asd-step-content">
                  <div className="asd-step-title">
                    {s.status === 'current' && (
                      <span style={{
                        display: 'inline-flex', alignItems: 'center',
                        background: '#e6f9f1', color: 'var(--asd-primary)',
                        fontFamily: 'var(--font-mono)', fontSize: '0.68rem',
                        padding: '2px 8px', borderRadius: 6,
                        marginRight: 8, letterSpacing: '0.06em', textTransform: 'uppercase',
                        fontWeight: 600, verticalAlign: 'middle',
                      }}>→ CURRENT</span>
                    )}
                    {s.title}
                  </div>
                  <div className="asd-step-desc">{s.desc}</div>
                  <div className="asd-step-time">⏱ {s.time}</div>
                  {s.status === 'current' && (
                    <button className="asd-btn" onClick={advanceSchedule}>
                      {s.id === 2 ? 'Mark Step as Done ✓' : 'Done ✓'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Lesson content — structured paragraphs */}
        <div style={{ marginBottom: 28 }}>
          <div className="asd-section-label">Lesson Content — Read One Section at a Time</div>
          <div className="asd-header" style={{ marginBottom: 16 }}>
            <div className="asd-title">
              {hasRealContent
                ? `AI-Structured Lesson — ${transformedAtoms.length} Part${transformedAtoms.length > 1 ? 's' : ''}`
                : 'Photosynthesis — What You Need to Know'
              }
            </div>
            <div className="asd-day-status">
              There are {allSections.length} section{allSections.length !== 1 ? 's' : ''}.
              You are on section {lessonStep + 1} of {allSections.length}.
            </div>
          </div>

          {/* Current section */}
          <div style={{
            background: '#f6fdf9',
            border: '2px solid #b7e8d2',
            borderRadius: 14, padding: '24px 28px',
            marginBottom: 16,
          }}>
            <div style={{
              fontFamily: 'var(--font-mono)', fontSize: '0.72rem',
              letterSpacing: '0.08em', textTransform: 'uppercase',
              color: 'var(--asd-primary)', marginBottom: 8,
            }}>Section {lessonStep + 1}</div>
            <div style={{
              fontFamily: 'var(--font-display)', fontWeight: 700,
              fontSize: '1.05rem', marginBottom: 10,
            }}>{currentSection?.heading}</div>
            <div style={{ fontSize: '0.95rem', lineHeight: 1.85, color: '#2a2a2a' }}>
              {currentSection?.text}
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
            <button className="asd-btn"
              disabled={lessonStep === 0}
              style={{ opacity: lessonStep === 0 ? 0.3 : 1 }}
              onClick={() => setLessonStep(s => Math.max(0, s - 1))}>
              ← Previous Section
            </button>
            <button className="asd-btn"
              disabled={lessonStep === allSections.length - 1}
              style={{
                background: lessonStep < allSections.length - 1 ? 'var(--asd-primary)' : '',
                color: lessonStep < allSections.length - 1 ? '#fff' : '',
                opacity: lessonStep === allSections.length - 1 ? 0.3 : 1,
              }}
              onClick={() => setLessonStep(s => Math.min(allSections.length - 1, s + 1))}>
              Next Section →
            </button>
          </div>
        </div>

        {/* Rules reminder */}
        <div style={{
          background: '#fafafa', border: '1.5px solid #e0e0e0',
          borderRadius: 12, padding: '16px 20px',
          fontSize: '0.88rem', color: '#555', lineHeight: 1.7,
        }}>
          <strong>Remember:</strong><br />
          — Read each section completely before moving to the next.<br />
          — If you do not understand something, that is okay. Keep reading.<br />
          — There are no wrong answers in this session.
        </div>

      </div>
    </div>
  )
}