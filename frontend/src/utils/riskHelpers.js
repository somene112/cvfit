/**
 * Risk Level Helpers
 *
 * Maps backend risk_gap scores (0–5) to display labels, emojis, and CSS classes.
 *   0–1  → Low Risk   🟢
 *   2–3  → Medium Risk 🟡
 *   4–5  → High Risk  🔴
 */

/**
 * @param {number|null|undefined} score - risk_gap value from backend rubric (0–5)
 * @returns {{ label: string, emoji: string, level: 'low' | 'medium' | 'high' }}
 */
export function getRiskLevel(score) {
  const n = Number(score);
  if (Number.isNaN(n)) return { label: 'Unknown', emoji: '⚪', level: 'unknown' };
  if (n <= 1) return { label: 'Low Risk', emoji: '🟢', level: 'low' };
  if (n <= 3) return { label: 'Medium Risk', emoji: '🟡', level: 'medium' };
  return { label: 'High Risk', emoji: '🔴', level: 'high' };
}

/**
 * Deduplicates an array of strings (case-insensitive).
 * Preserves the first occurrence's original casing.
 * @param {string[]} items
 * @returns {string[]}
 */
export function deduplicateStrings(items) {
  if (!Array.isArray(items)) return [];
  const seen = new Set();
  return items.filter((item) => {
    const key = String(item).toLowerCase().trim();
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * Deduplicates an array of objects by a given key.
 * @template T
 * @param {T[]} items
 * @param {keyof T} key
 * @returns {T[]}
 */
export function deduplicateByKey(items, key) {
  if (!Array.isArray(items)) return [];
  const seen = new Set();
  return items.filter((item) => {
    const val = String(item?.[key] ?? '').toLowerCase().trim();
    if (seen.has(val)) return false;
    seen.add(val);
    return true;
  });
}
