import type { ReactNode } from "react";

/** Split a word into rough syllable groups (a known dyslexia reading aid). */
export function syllabify(word: string): string[] {
  const m = word.match(
    /[^aeiouyAEIOUY]*[aeiouyAEIOUY]+(?:[^aeiouyAEIOUY]*$|[^aeiouyAEIOUY](?=[^aeiouyAEIOUY]))?/g,
  );
  return m && m.length ? m : [word];
}

/**
 * Render text with alternating-colour syllables and highlighted key words.
 * A word is a "key word" if it appears in `keywords` (from the backend's
 * structured meta), or — as a fallback — if it is long (>= `keyMinLen` letters).
 */
export function colourise(text: string, keywords: string[] = [], keyMinLen = 8): ReactNode[] {
  const keySet = new Set(keywords.flatMap((k) => k.toLowerCase().split(/\s+/)));
  return text.split(/(\s+)/).map((tok, ti) => {
    if (!tok.trim()) return <span key={ti}>{tok}</span>;
    const bare = tok.replace(/[^A-Za-z]/g, "");
    const isKey = keySet.has(bare.toLowerCase()) || bare.length >= keyMinLen;
    const parts = syllabify(tok).map((syl, si) => (
      <span key={si} className={si % 2 ? "syl-b" : "syl-a"}>
        {syl}
      </span>
    ));
    return (
      <span key={ti} className={isKey ? "kw" : undefined}>
        {parts}
      </span>
    );
  });
}
