import React, { useState } from 'react'

const QUESTS = [
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

export default function ADHDDash({ studentName, onLogout }) {
  const [activeQuest, setActiveQuest] = useState(QUESTS[0])
  const [step, setStep] = useState(activeQuest.current)
  const [xp, setXp] = useState(120)
  const [streak, setStreak] = useState(4)

  const totalSteps = activeQuest.steps.length
  const progress = totalSteps ? Math.round((step / totalSteps) * 100) : 0

  const advance = () => {
    if (step < totalSteps - 1) {
      setStep(s => s + 1)
      setXp(x => x + 10)
    } else {
      setXp(x => x + activeQuest.xp)
      setStreak(s => s + 1)
    }
  }

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
        {/* Hero — active quest */}
        <div className="adhd-hero">
          <div className="adhd-mission-label">🎯 Active Mission</div>
          <div className="adhd-mission-title">
            {activeQuest.title.split(' ').map((w, i) =>
              i === 0 ? <span key={i}>{w} </span> : <React.Fragment key={i}>{w} </React.Fragment>
            )}
          </div>

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

          <button
            onClick={advance}
            style={{
              marginTop: 20,
              background: 'var(--adhd-primary)', color: '#0f0f14',
              fontFamily: 'var(--font-display)', fontWeight: 800,
              fontSize: '0.95rem', padding: '13px 28px', borderRadius: 999,
              border: 'none', cursor: 'pointer',
              boxShadow: '0 0 20px rgba(245,166,35,0.3)',
              transition: 'all 0.15s',
            }}
            onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.04)'}
            onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
          >
            {step < totalSteps - 1 ? '→ Next Step' : '🏆 Complete Quest!'}
          </button>
        </div>

        {/* Quest grid */}
        <div style={{
          fontFamily: 'var(--font-display)', fontWeight: 700,
          fontSize: '0.8rem', letterSpacing: '0.08em', textTransform: 'uppercase',
          color: 'rgba(240,237,230,0.4)', marginBottom: 14,
        }}>ALL QUESTS</div>

        <div className="adhd-quest-grid">
          {QUESTS.map(q => (
            <div
              key={q.id}
              className={`adhd-quest-card ${activeQuest.id === q.id ? 'active' : ''}`}
              onClick={() => { setActiveQuest(q); setStep(q.current) }}
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
          marginTop: 28,
          background: '#1a1a22',
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