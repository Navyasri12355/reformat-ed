/**
 * Subject illustrations — simple inline SVGs used as the visual anchor before a
 * segment (a picture, not just an emoji). Keyed by the backend's
 * `meta.illustration`. Decorative, so hidden from screen readers.
 */
const ART: Record<string, JSX.Element> = {
  leaf: (
    <>
      <path d="M40 12C22 16 14 34 16 52c18 2 34-8 38-26 1-5 0-10-2-14-4 2-8 1-12 0z" fill="#7bc47f" />
      <path d="M40 12C30 26 22 40 16 52" stroke="#3f8a4a" strokeWidth="2" fill="none" />
    </>
  ),
  flask: (
    <>
      <path d="M26 10h12v16l12 22a6 6 0 0 1-5 9H19a6 6 0 0 1-5-9l12-22z" fill="#cfe8ff" stroke="#3a7bd5" strokeWidth="2" />
      <path d="M20 40h24" stroke="#3a7bd5" strokeWidth="2" />
      <circle cx="27" cy="46" r="2.5" fill="#3a7bd5" />
      <circle cx="35" cy="50" r="2" fill="#3a7bd5" />
    </>
  ),
  atom: (
    <>
      <circle cx="32" cy="32" r="4" fill="#7c5cff" />
      <ellipse cx="32" cy="32" rx="22" ry="9" stroke="#7c5cff" strokeWidth="2" fill="none" />
      <ellipse cx="32" cy="32" rx="22" ry="9" stroke="#7c5cff" strokeWidth="2" fill="none" transform="rotate(60 32 32)" />
      <ellipse cx="32" cy="32" rx="22" ry="9" stroke="#7c5cff" strokeWidth="2" fill="none" transform="rotate(120 32 32)" />
    </>
  ),
  ruler: (
    <>
      <rect x="10" y="22" width="44" height="20" rx="3" fill="#ffe0a3" stroke="#d59a2e" strokeWidth="2" />
      <path d="M18 22v8M26 22v6M34 22v8M42 22v6M50 22v8" stroke="#d59a2e" strokeWidth="2" />
    </>
  ),
  scroll: (
    <>
      <rect x="16" y="14" width="32" height="36" rx="3" fill="#f3e6c4" stroke="#b89b56" strokeWidth="2" />
      <path d="M22 24h20M22 30h20M22 36h14" stroke="#b89b56" strokeWidth="2" />
    </>
  ),
  book: (
    <>
      <path d="M12 16c8-3 16-3 20 1 4-4 12-4 20-1v32c-8-3-16-3-20 1-4-4-12-4-20-1z" fill="#cfe8ff" stroke="#3a7bd5" strokeWidth="2" />
      <path d="M32 17v32" stroke="#3a7bd5" strokeWidth="2" />
    </>
  ),
  chip: (
    <>
      <rect x="18" y="18" width="28" height="28" rx="3" fill="#dfe7ff" stroke="#5b4bdb" strokeWidth="2" />
      <rect x="26" y="26" width="12" height="12" rx="2" fill="#5b4bdb" />
      <path d="M24 18v-6M32 18v-6M40 18v-6M24 52v-6M32 52v-6M40 52v-6M18 24h-6M18 32h-6M18 40h-6M52 24h-6M52 32h-6M52 40h-6" stroke="#5b4bdb" strokeWidth="2" />
    </>
  ),
  bulb: (
    <>
      <circle cx="32" cy="26" r="14" fill="#fff1b8" stroke="#e0a800" strokeWidth="2" />
      <path d="M26 42h12v6a3 3 0 0 1-3 3h-6a3 3 0 0 1-3-3z" fill="#cbd2dd" stroke="#8a94a6" strokeWidth="2" />
      <path d="M32 20v10M27 25l5 5 5-5" stroke="#e0a800" strokeWidth="2" fill="none" />
    </>
  ),
};

export function Illustration({ kind, size = 80 }: { kind?: string; size?: number }) {
  const art = ART[kind ?? "bulb"] ?? ART.bulb;
  return (
    <svg
      className="illustration"
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-hidden="true"
    >
      {art}
    </svg>
  );
}
