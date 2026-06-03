import React, { useState } from 'react'
import TeacherLogin  from './TeacherLogin.jsx'
import StudentLogin  from './StudentLogin.jsx'
import TeacherDash   from './TeacherDash.jsx'
import Quiz          from './Quiz.jsx'
import ADHDDash      from './ADHDDash.jsx'
import DyslexiaDash  from './DyslexiaDash.jsx'
import ASDDash       from './ASDDash.jsx'

/*
  Global router — no external library needed for a hackathon.
  screen values:
    'home' | 'teacher-login' | 'teacher-dash'
    'student-login' | 'quiz' | 'adhd' | 'dyslexia' | 'asd'
*/
export default function App() {
  const [screen, setScreen] = useState('home')
  const [studentName, setStudentName] = useState('')
  const [profile, setProfile] = useState(null) // { type: 'adhd'|'dyslexia'|'asd' }

  const go = (s) => setScreen(s)

  if (screen === 'teacher-login')
    return <TeacherLogin onLogin={() => go('teacher-dash')} onBack={() => go('home')} />
  if (screen === 'teacher-dash')
    return <TeacherDash onLogout={() => go('home')} />
  if (screen === 'student-login')
    return <StudentLogin
      onLogin={(name) => { setStudentName(name); go('quiz') }}
      onSkipDiagnosed={(name, type) => { setStudentName(name); setProfile({ type }); go(type) }}
      onBack={() => go('home')}
    />
  if (screen === 'quiz')
    return <Quiz
      studentName={studentName}
      onComplete={(type) => { setProfile({ type }); go(type) }}
    />
  if (screen === 'adhd')     return <ADHDDash     studentName={studentName} onLogout={() => go('home')} />
  if (screen === 'dyslexia') return <DyslexiaDash studentName={studentName} onLogout={() => go('home')} />
  if (screen === 'asd')      return <ASDDash      studentName={studentName} onLogout={() => go('home')} />

  // ── Home / Role Select ──
  return (
    <div className="login-screen page-enter" style={{ flexDirection: 'column', gap: 0 }}>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <div style={{
          fontFamily: 'var(--font-display)', fontWeight: 800,
          fontSize: '2.6rem', letterSpacing: '-0.04em', marginBottom: 10,
        }}>
          Neuro<span style={{ color: 'var(--accent-green)' }}>Learn</span>
        </div>
        <p style={{ color: 'var(--muted)', fontSize: '1rem', maxWidth: 340, margin: '0 auto' }}>
          Personalised learning rebuilt from the ground up — for every kind of mind.
        </p>
      </div>
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', justifyContent: 'center' }}>
        <RoleCard
          emoji="📚"
          title="I'm a Teacher"
          sub="Upload content, review AI outputs, manage your class"
          color="var(--accent-blue)"
          onClick={() => go('teacher-login')}
        />
        <RoleCard
          emoji="🎒"
          title="I'm a Student"
          sub="Get your personalised curriculum in the format that works for you"
          color="var(--accent-green)"
          onClick={() => go('student-login')}
        />
      </div>
    </div>
  )
}

function RoleCard({ emoji, title, sub, color, onClick }) {
  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--white)',
        border: '1.5px solid var(--border)',
        borderRadius: 'var(--r-xl)',
        padding: '36px 40px',
        width: 260,
        cursor: 'pointer',
        transition: 'transform 0.18s, box-shadow 0.18s, border-color 0.18s',
        textAlign: 'center',
      }}
      onMouseEnter={e => {
        e.currentTarget.style.transform = 'translateY(-5px)'
        e.currentTarget.style.boxShadow = '0 16px 40px rgba(0,0,0,0.1)'
        e.currentTarget.style.borderColor = color
      }}
      onMouseLeave={e => {
        e.currentTarget.style.transform = ''
        e.currentTarget.style.boxShadow = ''
        e.currentTarget.style.borderColor = 'var(--border)'
      }}
    >
      <div style={{ fontSize: '2.4rem', marginBottom: 14 }}>{emoji}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.15rem', marginBottom: 8 }}>{title}</div>
      <p style={{ fontSize: '0.85rem', color: 'var(--muted)', lineHeight: 1.6 }}>{sub}</p>
    </div>
  )
}