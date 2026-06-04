/**
 * NeuraCore — API service layer
 * ==============================
 * Centralises all backend calls so components stay clean.
 * Set VITE_API_BASE in your .env (defaults to localhost:8000).
 */

const BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

// ── Upload ────────────────────────────────────────────────────────────────

/**
 * Upload a curriculum file and receive an array of curriculum atoms.
 *
 * @param {File} file
 * @returns {Promise<{ filename: string, atom_count: number, atoms: Array<{id: string, text: string, word_count: number}> }>}
 */
export async function uploadDocument(file) {
  const form = new FormData()
  form.append('file', file)

  const res = await fetch(`${BASE}/api/upload`, {
    method: 'POST',
    body:   form,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Upload failed (${res.status})`)
  }

  return res.json()
}

// ── Transform (single atom) ───────────────────────────────────────────────

/**
 * Rewrite a single curriculum atom for a cognitive profile.
 *
 * @param {string} atomId
 * @param {string} text
 * @param {'adhd'|'dyslexia'|'asd'} profile
 * @returns {Promise<{ atom_id: string, profile: string, original_text: string, rewritten_text: string }>}
 */
export async function transformAtom(atomId, text, profile) {
  const res = await fetch(`${BASE}/api/transform`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ atom_id: atomId, text, profile }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Transform failed (${res.status})`)
  }

  return res.json()
}

// ── Transform (batch) ─────────────────────────────────────────────────────

/**
 * Rewrite a list of atoms for a single cognitive profile.
 *
 * @param {Array<{id: string, text: string}>} atoms
 * @param {'adhd'|'dyslexia'|'asd'} profile
 * @returns {Promise<{ results: Array, count: number }>}
 */
export async function transformBatch(atoms, profile) {
  const res = await fetch(`${BASE}/api/transform/batch`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ atoms, profile }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Batch transform failed (${res.status})`)
  }

  return res.json()
}
