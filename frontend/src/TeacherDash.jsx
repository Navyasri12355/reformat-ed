import React, { useState, useRef } from 'react'
import { uploadDocument, transformBatch } from './utils/api.js'

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

// How many atoms to transform per profile for the hackathon demo
// (set lower to save API credits; 3 = fast demo)
const ATOMS_TO_TRANSFORM = 3

export default function TeacherDash({ onLogout, atoms, setAtoms, transformed, setTransformed }) {
  const [tab, setTab]               = useState('overview')
  const [queue, setQueue]           = useState(MOCK_QUEUE)
  const [dragOver, setDragOver]     = useState(false)

  // Upload + transform state
  const [uploading, setUploading]   = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [transforming, setTransforming] = useState(false)
  const [transformStep, setTransformStep] = useState('')
  const [uploadResult, setUploadResult]   = useState(null)   // raw upload response
  const [allDone, setAllDone]       = useState(false)

  const fileRef = useRef()

  // ── Real upload + transform flow ──────────────────────────────────────
  const handleFile = async (file) => {
    if (!file) return
    setUploadError(null)
    setAllDone(false)
    setUploadResult(null)

    // Step 1: Upload to Phase 1 /api/upload
    setUploading(true)
    let uploadData
    try {
      uploadData = await uploadDocument(file)
    } catch (err) {
      setUploadError(`Upload failed: ${err.message}`)
      setUploading(false)
      return
    }
    setUploading(false)
    setUploadResult(uploadData)
    setAtoms(uploadData.atoms)

    // Step 2: Transform for all three profiles via /api/transform/batch
    // We cap at ATOMS_TO_TRANSFORM atoms to keep demo fast
    const subset = uploadData.atoms.slice(0, ATOMS_TO_TRANSFORM)

    setTransforming(true)
    const newTransformed = { adhd: [], dyslexia: [], asd: [] }

    for (const profile of ['adhd', 'dyslexia', 'asd']) {
      setTransformStep(`Transforming for ${profile.toUpperCase()} profile…`)
      try {
        const result = await transformBatch(
          subset.map(a => ({ id: a.id, text: a.text })),
          profile
        )
        newTransformed[profile] = result.results
      } catch (err) {
        // Non-fatal: show error in the UI but continue with other profiles
        console.error(`Transform failed for ${profile}:`, err)
        newTransformed[profile] = subset.map(a => ({
          atom_id:        a.id,
          profile,
          original_text:  a.text,
          rewritten_text: `[Could not transform: ${err.message}]`,
          error:          true,
        }))
      }
    }

    setTransformed(newTransformed)
    setTransforming(false)
    setTransformStep('')
    setAllDone(true)
  }

  const onFileInput = (e) => {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  const onDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  const approveItem = (id) =>
    setQueue(q => q.map(i => i.id === id ? { ...i, status: 'approved' } : i))

  const isProcessing = uploading || transforming

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
                  { v: atoms.length || '—', l: 'Atoms Loaded', c: 'var(--accent-blue)'  },
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

              {/* Phase 2: show transform status */}
              {allDone && (
                <div className="card" style={{ borderLeft: '4px solid var(--accent-green)' }}>
                  <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, marginBottom: 8 }}>
                    ✅ Content Ready
                  </div>
                  <p style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>
                    {uploadResult?.atom_count} atoms extracted from <strong>{uploadResult?.filename}</strong>.
                    Personalised versions generated for ADHD, Dyslexia and ASD profiles.
                    Students can now log in and see their content.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* ── UPLOAD ── */}
          {tab === 'upload' && (
            <div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 800, fontSize: '1.5rem', marginBottom: 6 }}>
                Upload Curriculum
              </h2>
              <p style={{ color: 'var(--muted)', fontSize: '0.9rem', marginBottom: 28 }}>
                Upload a PDF, DOCX, or plain text file. The system will extract curriculum atoms
                and immediately generate personalised versions for each cognitive profile.
              </p>

              {uploadError && (
                <div style={{
                  background: '#fff0f0', border: '2px solid var(--accent-rose)',
                  borderRadius: 10, padding: '14px 18px', marginBottom: 20,
                  fontSize: '0.88rem', color: '#b91c1c',
                }}>
                  ⚠️ {uploadError}
                  <button
                    onClick={() => setUploadError(null)}
                    style={{ marginLeft: 12, background: 'none', border: 'none', cursor: 'pointer', color: '#b91c1c', fontWeight: 700 }}
                  >✕</button>
                </div>
              )}

              {!allDone ? (
                <div
                  className={`dropzone ${dragOver ? 'drag-over' : ''}`}
                  onClick={() => !isProcessing && fileRef.current.click()}
                  onDragOver={e => { e.preventDefault(); setDragOver(true) }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={onDrop}
                  style={{ cursor: isProcessing ? 'wait' : 'pointer' }}
                >
                  <input
                    ref={fileRef}
                    type="file"
                    style={{ display: 'none' }}
                    onChange={onFileInput}
                    accept=".pdf,.docx,.txt"
                  />
                  {isProcessing ? (
                    <>
                      <div style={{ fontSize: '2.2rem', marginBottom: 12 }}>⏳</div>
                      <div className="dropzone-label">
                        {uploading ? 'Uploading and parsing file…' : transformStep || 'Generating personalised content…'}
                      </div>
                      <div className="dropzone-sub">
                        {uploading
                          ? 'Extracting curriculum atoms with PyMuPDF…'
                          : 'Calling GPT-4o with cognitive-profile prompts…'
                        }
                      </div>

                      {/* Progress bar animation */}
                      <div style={{
                        marginTop: 24, width: '100%', maxWidth: 300,
                        background: 'var(--border)', borderRadius: 999, overflow: 'hidden', height: 6,
                      }}>
                        <div style={{
                          height: '100%', background: 'var(--accent-blue)',
                          borderRadius: 999, width: '60%',
                          animation: 'shimmer 1.4s ease-in-out infinite',
                        }} />
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="dropzone-icon">📄</div>
                      <div className="dropzone-label">Drop your file here or click to browse</div>
                      <div className="dropzone-sub">PDF, DOCX, or TXT — max 10 MB</div>
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
                    <strong>{uploadResult?.atom_count}</strong> curriculum atoms extracted from{' '}
                    <strong>{uploadResult?.filename}</strong>.<br />
                    AI-personalised content generated for ADHD, Dyslexia, and ASD profiles.
                  </p>

                  {/* Preview of atoms */}
                  {atoms.length > 0 && (
                    <div style={{ textAlign: 'left', marginBottom: 20 }}>
                      <div style={{ fontWeight: 700, fontSize: '0.82rem', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--muted)' }}>
                        Extracted Atoms Preview
                      </div>
                      {atoms.slice(0, 3).map((a, i) => (
                        <div key={a.id} style={{
                          background: 'var(--paper)', border: '1px solid var(--border)',
                          borderRadius: 8, padding: '10px 14px', marginBottom: 8,
                          fontSize: '0.85rem', lineHeight: 1.6,
                        }}>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: 'var(--muted)', marginRight: 8 }}>
                            {a.id}
                          </span>
                          {a.text.slice(0, 120)}{a.text.length > 120 ? '…' : ''}
                        </div>
                      ))}
                      {atoms.length > 3 && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>
                          +{atoms.length - 3} more atoms
                        </div>
                      )}
                    </div>
                  )}

                  <button className="btn btn-outline btn-sm" onClick={() => { setAllDone(false); setUploadResult(null) }}>
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