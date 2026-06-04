import React, { useState } from 'react'

/*
  ADHDDash — Phase 2 update
  --------------------------
  Accepts `transformedAtoms` from the parent (real AI-generated content).
  Falls back to the static QUESTS demo data if no atoms have been loaded yet.
*/

const STATIC_QUESTS = [
  {
    id: 1, num: 'QUEST 01', title: 'The Photosynthesis Challenge',
    tag: '⚡ 5 min', xp: 50, active: true,
    steps: [
      'Plants absorb sunlight using chlorophyll — their secret energy weapon.',
      'Carbon dioxide enters through tiny pores called stomata.',
      'Water travels up from roots via the xylem highway.',
      'Light energy splits water molecules in the light-dependent reaction.',
      'ATP and NADPH are produced — the cell\'s energy currency.',
    ],
    current: 2,
  },
  {
    id: 2, num: 'QUEST 02', title: 'Cell Division: Level Up',
    tag: '🔬 8 min', xp: 80, active: false,
    steps: [], current: 0,
  },
  {
    id: 3, num: 'QUEST 03', title: 'Newton\'s Laws — Boss Fight',
    tag: '🚀 6 min', xp: 60, active: false,
    steps: [], current: 0,
  },
]

// Parse the AI-rewritten ADHD text into quest steps.
// The prompt produces lines like "Step 1 › ..." — we extract those.
function parseADHDAtom(rewrittenText, atomId, index) {
  const lines = rewrittenText.split('\n').map(l => l.trim()).filter(Boolean)

  // Extract mission title (line starting with 🎯 MISSION:)
  const titleLine = lines.find(l => l.startsWith('🎯'))
  const title = titleLine
    ? titleLine.replace(/^🎯\s*MISSION:\s*/i, '').replace(/^MISSION:\s*/i, '')
    : `Mission ${index + 1}`

  // Extract steps (lines with "Step N ›" or numbered)
  const stepLines = lines.filter(l =>
    /^step\s*\d+/i.test(l) || /^\d+[\.\)›]/.test(l)
  )
  const steps = stepLines.length > 0
    ? stepLines.map(l => l.replace(/^step\s*\d+\s*[›:.\)]\s*/i, '').replace(/^\d+[\.\)›]\s*/, ''))
    : lines.filter(l => !l.startsWith('🎯') && !l.startsWith('⚡'))

  // Extract XP line
  const xpLine = lines.find(l => l.startsWith('⚡'))
  const xp = xpLine ? parseInt(xpLine.match(/\+?(\d+)/)?.[1] || '50') : 50

  return {
    id: index + 1,
    num: `QUEST ${String(index + 1).padStart(2, '0')}`,
    title,
    tag: `⚡ ${Math.ceil(steps.length * 1.5)} min`,
    xp,
    active: index === 0,
    steps,
    current: 0,
    atomId,
  }
}

export default function ADHDDash({ studentName, onLogout, transformedAtoms = [] }) {
  // Build quest list from real atoms, or fall back to static
  const quests = transformedAtoms.length > 0
    ? transformedAtoms.map((a, i) => parseADHDAtom(a.rewritten_text || a.text, a.atom_id, i))
    : STATIC_QUESTS

  const [activeQuest, setActiveQuest] = useState(quests[0])
  const [step, setStep]               = useState(0)
  const [xp, setXp]                   = useState(120)
  const [streak, setStreak]           = useState(4)

  const totalSteps = activeQuest.steps.length
  const progress   = totalSteps ? Math.round((step / totalSteps) * 100) : 0

  const advance = () => {
    if (step < totalSteps - 1) {
      setStep(s => s + 1)
      setXp(x => x + 10)
    } else {
      setXp(x => x + activeQuest.xp)
      setStreak(s => s + 1)
    }
  }

  const selectQuest = (q) => {
    setActiveQuest(q)
    setStep(0)
  }

  const isComplete = step >= totalSteps - 1 && totalSteps > 0

  return (
    <div className="adhd-root page-enter">
      {/* Nav */}
      <nav className="adhd-topnav">
        <div className="adhd-logo">⚡ NeuroLearn</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div className="adhd-streak">🔥 {streak} day streak</div>
          <div className="adhd-xp">
            XP <span className="adhd-xp-val">{xp}</span>
          </div>
          <button onClick={onLogout} style={{
            background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.15)',
            borderRadius: 999, color: 'rgba(240,237,230,0.7)', fontSize: '0.8rem',
            padding: '7px 14px', cursor: 'pointer',
          }}>Exit</button>
        </div>
      </nav>

      <div className="adhd-body">
        {/* Live content badge */}
        {transformedAtoms.length > 0 && (
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6,
            background: 'rgba(74,222,128,0.12)', border: '1px solid rgba(74,222,128,0.3)',
            borderRadius: 999, padding: '4px 12px', marginBottom: 16,
            fontSize: '0.76rem', color: '#4ade80', fontFamily: 'var(--font-mono)',
          }}>
            <span style={{ width: 6, height: 6, background: '#4ade80', borderRadius: '50%', display: 'inline-block' }} />
            LIVE AI CONTENT — {transformedAtoms.length} missions generated
          </div>
        )}

        {/* Hero — active quest */}
        <div className="adhd-hero">
          <div className="adhd-mission-label">🎯 Active Mission</div>
          <div className="adhd-mission-title">{activeQuest.title}</div>

          {/* Current step display */}
          {totalSteps > 0 && (
            <div style={{
              background: 'rgba(255,255,255,0.06)',
              borderRadius: 12, padding: '18px 20px', marginBottom: 16,
              border: '1px solid rgba(245,166,35,0.2)',
            }}>
              <div style={{
                fontFamily: 'var(--font-mono)', fontSize: '0.7rem',
                color: 'rgba(245,166,35,0.7)', letterSpacing: '0.1em',
                textTransform: 'uppercase', marginBottom: 6,
              }}>Step {step + 1}/{totalSteps}</div>
              <div style={{ fontSize: '0.95rem', lineHeight: 1.65, color: '#f0ede6' }}>
                {activeQuest.steps[step]}
              </div>
            </div>
          )}

          {totalSteps === 0 && (
            <div style={{
              background: 'rgba(255,255,255,0.04)', borderRadius: 12,
              padding: '18px 20px', marginBottom: 16, color: 'rgba(240,237,230,0.5)',
              fontSize: '0.9rem',
            }}>
              Select a quest below to begin your mission.
            </div>
          )}

          <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
            <span className="adhd-quest-tag">{activeQuest.tag}</span>
            <span className="adhd-quest-tag">+{activeQuest.xp} XP on complete</span>
          </div>

          <div className="adhd-progress-row">
            <div className="adhd-progress-track">
              <div className="adhd-progress-fill" style={{ width: `${progress}%` }} />
            </div>
            <div className="adhd-progress-label">{progress}% done</div>
          </div>

          {totalSteps > 0 && (
            <button
              onClick={advance}
              style={{
                marginTop: 20,
                background: isComplete ? '#4ade80' : 'var(--adhd-primary)',
                color: '#0f0f14',
                fontFamily: 'var(--font-display)', fontWeight: 800,
                fontSize: '0.95rem', padding: '13px 28px', borderRadius: 999,
                border: 'none', cursor: 'pointer',
                boxShadow: `0 0 20px ${isComplete ? 'rgba(74,222,128,0.35)' : 'rgba(245,166,35,0.3)'}`,
                transition: 'all 0.15s',
              }}
              onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.04)'}
              onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
            >
              {isComplete ? '🏆 Complete Quest!' : '→ Next Step'}
            </button>
          )}
        </div>

        {/* Quest grid */}
        <div style={{
          fontFamily: 'var(--font-display)', fontWeight: 700,
          fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase',
          color: 'rgba(240,237,230,0.4)', marginBottom: 14,
        }}>ALL QUESTS</div>

        <div className="adhd-quest-grid">
          {quests.map(q => (
            <div
              key={q.id}
              className={`adhd-quest-card ${activeQuest.id === q.id ? 'active' : ''}`}
              onClick={() => selectQuest(q)}
            >
              <div className="adhd-quest-num">{q.num}</div>
              <div className="adhd-quest-title">{q.title}</div>
              <span className="adhd-quest-tag">{q.tag}</span>
              <div style={{
                marginTop: 10, fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem', color: 'rgba(240,237,230,0.35)',
              }}>+{q.xp} XP</div>
            </div>
          ))}
        </div>

        {/* XP bar */}
        <div style={{
          marginTop: 28, background: '#1a1a22',
          border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: 16, padding: '18px 22px',
          display: 'flex', alignItems: 'center', gap: 20,
        }}>
          <div>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'rgba(245,166,35,0.6)', marginBottom: 3, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
              Level 3 — Explorer
            </div>
            <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.2rem', color: 'var(--adhd-primary)' }}>
              {xp} / 200 XP
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <div className="adhd-progress-track" style={{ height: 14 }}>
              <div className="adhd-progress-fill" style={{ width: `${Math.min((xp / 200) * 100, 100)}%` }} />
            </div>
          </div>
          <div style={{ fontSize: '1.8rem' }}>🏅</div>
        </div>
      </div>
    </div>
  )
}