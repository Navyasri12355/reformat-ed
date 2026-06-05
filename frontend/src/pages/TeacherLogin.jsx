import React, { useState } from 'react'

export default function TeacherLogin({ onLogin, onBack }) {
  const [email, setEmail] = useState('')
  const [pass, setPass]   = useState('')
  const [err, setErr]     = useState('')

  const handle = (e) => {
    e.preventDefault()
    if (!email || !pass) { setErr('Please fill in both fields.'); return }
    // Demo: any credentials work
    onLogin()
  }

  return (
    <div className="login-screen page-enter">
      <div className="login-box">
        <button onClick={onBack} style={{
          background: 'none', border: 'none', cursor: 'pointer',
          color: 'var(--muted)', fontSize: '0.85rem', marginBottom: 24,
          display: 'flex', alignItems: 'center', gap: 6,
        }}>← Back</button>

        <div style={{
          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
          width: 48, height: 48, borderRadius: 14,
          background: '#e8f0fc', fontSize: '1.5rem', marginBottom: 20,
        }}>📚</div>

        <h1 className="login-title">Teacher Login</h1>
        <p className="login-sub">Access your educator dashboard, upload materials, and review student content.</p>

        {err && (
          <div style={{
            background: '#fdedf0', border: '1.5px solid #f7bfca',
            borderRadius: 'var(--r-sm)', padding: '10px 14px',
            fontSize: '0.85rem', color: '#b8274a', marginBottom: 18,
          }}>{err}</div>
        )}

        <form onSubmit={handle}>
          <div className="form-field">
            <label className="form-label">Email Address</label>
            <input className="input" type="email" placeholder="you@school.edu"
              value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div className="form-field">
            <label className="form-label">Password</label>
            <input className="input" type="password" placeholder="••••••••"
              value={pass} onChange={e => setPass(e.target.value)} />
          </div>
          <button type="submit" className="btn btn-blue" style={{ width: '100%', justifyContent: 'center', marginTop: 8 }}>
            Sign In to Dashboard →
          </button>
        </form>

        <p style={{ fontSize: '0.78rem', color: 'var(--muted)', textAlign: 'center', marginTop: 20 }}>
          Demo mode — any credentials work
        </p>
      </div>
    </div>
  )
}
