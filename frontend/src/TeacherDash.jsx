import React, { useState, useRef } from 'react'

const MOCK_STUDENTS = [
  { id: 1, name: 'Aisha Patel',    profile: 'ADHD',     progress: 72, lastActive: '2 hrs ago',  status: 'active' },
  { id: 2, name: 'Marcus Green',   profile: 'Dyslexia', progress: 45, lastActive: '1 day ago',  status: 'review' },
  { id: 3, name: 'Priya Sharma',   profile: 'ASD',      progress: 88, lastActive: '30 min ago', status: 'active' },
  { id: 4, name: 'Leo Tan',        profile: 'ADHD',     progress: 30, lastActive: '3 days ago', status: 'flagged' },
  { id: 5, name: 'Sara Okoro',     profile: 'Dyslexia', progress: 60, lastActive: '5 hrs ago',  status: 'active' },
]

const MOCK_QUEUE = [
  { id: 1, atom: 'Photosynthesis — Stage 1', profile: 'ADHD',     status: 'pending' },
  { id: 2, atom: 'Cell Division Overview',   profile: 'Dyslexia', status: 'pending' },
  { id: 3, atom: 'Newton\'s Laws — Intro',   profile: 'ASD',      status: 'approved' },
]

const PROFILE_COLORS = { ADHD: 'amber', Dyslexia: 'blue', ASD: 'green' }
const STATUS_COLORS  = { active: 'green', review: 'amber', flagged: 'rose', pending: 'amber', approved: 'green' }

export default function TeacherDash({ onLogout }) {
  const [tab, setTab]         = useState('overview')
  const [queue, setQueue]     = useState(MOCK_QUEUE)
  const [dragOver, setDragOver] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadDone, setUploadDone] = useState(false)
  const fileRef = useRef()

  const handleFile = () => {
    setUploading(true)
    setTimeout(() => { setUploading(false); setUploadDone(true) }, 2200)
  }

  const approveItem = (id) =>
    setQueue(q => q.map(i => i.id === id ? { ...i, status: 'approved' } : i))

  const TABS = [
    { id: 'overview', icon: '📊', label: 'Overview' },
    { id: 'upload',   icon: '⬆️',  label: 'Upload' },
    { id: 'students', icon: '👩‍🎓', label: 'Students' },
    { id: 'queue',    icon: '✅',   label: 'Review Queue' },
  ]

  return (
    <div style={{ background: 'var(--paper)', minHeight: '100vh' }}>
      {/* Nav */}
      <nav className="topnav">
        <span className="topnav-logo">Neuro<span>Learn</span></span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>Ms. Ranjani Iyer</span>
          <div style={{
            width: 36, height: 36, borderRadius: '50%',
            background: 'var(--accent-blue)', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontFamily: 'var(--font-display)', fontWeight: 700,
          }}>R</div>
          <button onClick={onLogout} className="btn btn-outline btn-sm">Log out</button>
        </div>
      </nav>

      <div className="layout page-enter">
        {/* Sidebar */}
        <aside className="sidebar">
          {TABS.map(t => (
            <div key={t.id}
              className={`sidebar-item ${tab === t.id ? 'active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              <span className="sidebar-icon">{t.icon}</span> {t.label}
            </div>
          ))}
          <hr className="divider" style={{ marginTop: 'auto' }} />
          <div className="sidebar-item" style={{ color: 'var(--accent-rose)' }}>
            <span className="sidebar-icon">⚙️</span> Settings
          </div>
        </aside>

        {/* Main */}
        <main className="main-content">

          {/* ── OVERVIEW ── */}
          {tab === 'overview' && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.5rem', marginBottom: 6 }}>
                Good morning, Ms. Iyer 👋
              </h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: 28 }}>
                Here's how your class is doing today.
              </p>

              <div className="stats-row">
                {[
                  { v: '5',  l: 'Active Students',   c: 'var(--accent-green)' },
                  { v: '12', l: 'Atoms Delivered',    c: 'var(--accent-blue)'  },
                  { v: '2',  l: 'Pending Reviews',    c: 'var(--accent-amber)' },
                  { v: '1',  l: 'Flagged Students',   c: 'var(--accent-rose)'  },
                ].map(s => (
                  <div key={s.l} className="stat-card">
                    <div className="stat-value" style={{ color: s.c }}>{s.v}</div>
                    <div className="stat-label">{s.l}</div>
                  </div>
                ))}
              </div>

              <div className="card" style={{ marginBottom: 20 }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1rem', marginBottom: 16 }}>
                  Profile Distribution
                </h3>
                {[
                  { label: 'ADHD', pct: 40, color: 'var(--accent-amber)' },
                  { label: 'Dyslexia', pct: 40, color: 'var(--accent-blue)' },
                  { label: 'ASD', pct: 20, color: 'var(--accent-green)' },
                ].map(b => (
                  <div key={b.label} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem', marginBottom: 5 }}>
                      <span style={{ fontWeight: 600 }}>{b.label}</span>
                      <span style={{ color: 'var(--muted)' }}>{b.pct}%</span>
                    </div>
                    <div className="progress-track">
                      <div className="progress-fill" style={{ width: `${b.pct}%`, background: b.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── UPLOAD ── */}
          {tab === 'upload' && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.5rem', marginBottom: 6 }}>
                Upload Curriculum
              </h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: 28 }}>
                Upload a PDF, DOCX, or plain text file. The system will extract curriculum atoms and prepare personalised versions for each profile.
              </p>

              {!uploadDone ? (
                <div
                  className={`dropzone ${dragOver ? 'drag-over' : ''}`}
                  onClick={() => fileRef.current.click()}
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={e => { e.preventDefault(); setDragOver(false); handleFile() }}
                >
                  <input ref={fileRef} type="file" style={{ display: 'none' }} onChange={handleFile} accept=".pdf,.docx,.txt" />
                  {uploading ? (
                    <>
                      <div style={{ fontSize: '2.2rem', marginBottom: 12 }}>⏳</div>
                      <div className="dropzone-label">Processing your file…</div>
                      <div className="dropzone-sub">Extracting curriculum atoms</div>
                    </>
                  ) : (
                    <>
                      <div className="dropzone-icon">📄</div>
                      <div className="dropzone-label">Drop your file here or click to browse</div>
                      <div className="dropzone-sub">PDF, DOCX, or TXT — max 20 MB</div>
                    </>
                  )}
                </div>
              ) : (
                <div className="card" style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: 10 }}>✅</div>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.2rem', marginBottom: 8 }}>
                    File processed successfully
                  </div>
                  <p style={{ color: 'var(--muted)', marginBottom: 20 }}>
                    14 curriculum atoms extracted. AI transformation queued for 5 student profiles.
                  </p>
                  <button className="btn btn-outline btn-sm" onClick={() => setUploadDone(false)}>
                    Upload another file
                  </button>
                </div>
              )}

              <div className="card" style={{ marginTop: 24 }}>
                <h3 style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 14 }}>
                  Recent Uploads
                </h3>
                {['biology_ch4_photosynthesis.pdf', 'newton_laws_intro.docx', 'cell_division_notes.txt'].map((f, i) => (
                  <div key={f} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '12px 0',
                    borderBottom: i < 2 ? '1px solid var(--border)' : 'none',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span style={{ fontSize: '1.2rem' }}>📄</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{f}</div>
                        <div style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                          {[12, 8, 6][i]} atoms · {['2 days ago', '5 days ago', '1 week ago'][i]}
                        </div>
                      </div>
                    </div>
                    <span className={`badge badge-${['green', 'green', 'amber'][i]}`}>
                      {['Delivered', 'Delivered', 'Pending'][i]}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── STUDENTS ── */}
          {tab === 'students' && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.5rem', marginBottom: 6 }}>
                Students
              </h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: 24 }}>
                Track each student's profile, progress, and engagement.
              </p>
              <div className="card">
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Profile</th>
                        <th>Progress</th>
                        <th>Last Active</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {MOCK_STUDENTS.map(s => (
                        <tr key={s.id}>
                          <td>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                              <div style={{
                                width: 32, height: 32, borderRadius: '50%',
                                background: 'var(--paper-2)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.85rem',
                              }}>{s.name[0]}</div>
                              <span style={{ fontWeight: 500 }}>{s.name}</span>
                            </div>
                          </td>
                          <td>
                            <span className={`badge badge-${PROFILE_COLORS[s.profile]}`}>{s.profile}</span>
                          </td>
                          <td style={{ minWidth: 140 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                              <div className="progress-track" style={{ width: 80 }}>
                                <div className="progress-fill" style={{
                                  width: `${s.progress}%`,
                                  background: s.progress > 70 ? 'var(--accent-green)' : s.progress > 40 ? 'var(--accent-amber)' : 'var(--accent-rose)',
                                }} />
                              </div>
                              <span style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>{s.progress}%</span>
                            </div>
                          </td>
                          <td style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>{s.lastActive}</td>
                          <td>
                            <span className={`badge badge-${STATUS_COLORS[s.status]}`}>
                              {s.status.charAt(0).toUpperCase() + s.status.slice(1)}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ── REVIEW QUEUE ── */}
          {tab === 'queue' && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.5rem', marginBottom: 6 }}>
                AI Review Queue
              </h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: 24 }}>
                Every AI-generated atom waits here for your approval before reaching a student.
              </p>
              <div className="card">
                {queue.map((item, i) => (
                  <div key={item.id} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '16px 0',
                    borderBottom: i < queue.length - 1 ? '1px solid var(--border)' : 'none',
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.92rem', marginBottom: 4 }}>{item.atom}</div>
                      <span className={`badge badge-${PROFILE_COLORS[item.profile]}`}>{item.profile}</span>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <span className={`badge badge-${STATUS_COLORS[item.status]}`}>
                        {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                      </span>
                      {item.status === 'pending' && (
                        <button className="btn btn-green btn-sm" onClick={() => approveItem(item.id)}>
                          Approve ✓
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  )
}