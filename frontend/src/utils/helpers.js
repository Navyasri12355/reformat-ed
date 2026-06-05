/**
 * NeuraCore — Utility Functions
 * Helpers for profiles, transformations, and UI logic
 */

/**
 * Calculate cognitive profile from quiz responses
 * @param {number} adhdScore
 * @param {number} dyslexiaScore
 * @param {number} asdScore
 * @returns {string} - dominant profile: 'adhd' | 'dyslexia' | 'asd'
 */
export function calculateProfile(adhdScore, dyslexiaScore, asdScore) {
  const profiles = {
    adhd: adhdScore,
    dyslexia: dyslexiaScore,
    asd: asdScore,
  }
  return Object.keys(profiles).reduce((a, b) =>
    profiles[a] > profiles[b] ? a : b
  )
}

/**
 * Get CSS class for profile styling
 */
export function getProfileClass(profile) {
  const map = {
    adhd: 'profile-adhd',
    dyslexia: 'profile-dyslexia',
    asd: 'profile-asd',
  }
  return map[profile] || 'profile-default'
}

/**
 * Get display name for profile
 */
export function getProfileLabel(profile) {
  const map = {
    adhd: 'ADHD-Friendly',
    dyslexia: 'Dyslexia-Friendly',
    asd: 'Autism-Spectrum-Friendly',
  }
  return map[profile] || 'Default'
}
