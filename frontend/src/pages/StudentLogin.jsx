import React, { useState } from 'react'

export default function StudentLogin({ onLogin, onSkipDiagnosed, onBack }) {
  const [name, setName]       = useState('')
  const [code, setCode]       = useState('')
  const [diagnosed, setDiagnosed] = useState(false)
  const [diagType, setDiagType]   = useState('')
  const [err, setErr]             = useState('')

  const handle = (e) => {
    e.preventDefault()
    if (!name.trim()) { setErr('Please enter your name.'); return }
    if (diagnosed && !diagType) { setErr('Please select your diagnosis.'); return }
    if (diagnosed) {
      onSkipDiagnosed(name.trim(), diagType)
    } else {
      onLogin(name.trim())
    }
  }

  return (
    <div className="login-screen page-enter">
      <div className="login-box" style={{ maxWidth: 480 }}>
        <button onClick={onBack} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--muted)', fontSize: '0.85rem', marginBottom: 24,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>← Back</button>

        <div style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 48, height: 48, borderRadius: 14,
          background: '#e6f9f1', fontSize: '1.5rem', marginBottom: 20,
        }}>🎒</div>

        <h1 className="login-title">Welcome!</h1>
        <p className="login-sub">Let's set up your personalised learning space.</p>

        {err && (
          <div style={{
            background: '#fdedf0', border: '1.5px solid #f7bfca',
            borderRadius: 'var(--r-sm)', padding: '10px 14px',
            fontSize: '0.85rem', color: '#b8274a', marginBottom: 18,
          }}>{err}</div>
        )}

        <form onSubmit={handle}>
          <div className="form-field">
            <label className="form-label">Your Name</label>
            <input className="input" placeholder="e.g. Aisha" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div className="form-field">
            <label className="form-label">Class Code (optional)</label>
            <input className="input" placeholder="e.g. BIO-2025" value={code} onChange={e => setCode(e.target.value)} />
          </div>

          <hr className="divider" />

          {/* Already diagnosed toggle */}
          <div style={{
            background: 'var(--paper)', borderRadius: 'var(--r-md)',
            padding: '16px 18px', marginBottom: 20,
          }}>
            <label style={{
              display: 'flex', alignItems: 'center', gap: 12, cursor: 'pointer',
              fontWeight: 600, fontSize: '0.9rem',
            }}>
              <input
                type="checkbox"
                checked={diagnosed}
                onChange={e => setDiagnosed(e.target.checked)}
                style={{ width: 18, height: 18, accentColor: 'var(--accent-green)' }}
              />
              I already have a diagnosis / know my learning profile
            </label>
            <p style={{ fontSize: '0.8rem', color: 'var(--muted)', marginTop: 7, marginLeft: 30 }}>
              Skip the quiz and go straight to your personalised dashboard.
            </p>

            {diagnosed && (
              <div style={{ marginTop: 16, marginLeft: 30, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {[
                  { id: 'adhd',     label: '⚡ ADHD',     color: 'var(--accent-amber)' },
                  { id: 'dyslexia', label: '🎧 Dyslexia', color: 'var(--accent-blue)'  },
                  { id: 'asd',      label: '🧩 ASD',      color: 'var(--accent-green)' },
                ].map(t => (
                  <button
                    key={t.id} type="button"
                    onClick={() => setDiagType(t.id)}
                    style={{
                      padding: '9px 18px', borderRadius: 999, fontSize: '0.88rem',
                      fontFamily: 'var(--font-display)', fontWeight: 600,
                      border: `2px solid ${diagType === t.id ? t.color : 'var(--border)'}`,
                      background: diagType === t.id ? t.color : 'var(--white)',
                      color: diagType === t.id ? (t.id === 'dyslexia' ? '#fff' : '#fff') : 'var(--ink)',
                      cursor: 'pointer', transition: 'all 0.15s',
                    }}
                  >{t.label}</button>
                ))}
              </div>
            )}
          </div>

          <button type="submit" className="btn btn-green" style={{ width: '100%', justifyContent: 'center' }}>
            Continue →
          </button>
        </form>
      </div>
    </div>
  )
}
