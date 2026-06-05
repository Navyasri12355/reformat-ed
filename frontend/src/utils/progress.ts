/** Percentage [0, 100] of items completed, clamped and integer-rounded. */
export function percent(current: number, total: number): number {
  if (total <= 0) return 0;
  const pct = (current / total) * 100;
  return Math.max(0, Math.min(100, Math.round(pct)));
}
