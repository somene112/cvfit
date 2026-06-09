/**
 * Result Schema v2 Helpers
 * Utilities for detecting schema version, normalizing result data,
 * and mapping fit levels.
 *
 * Source of truth: docs/result_schema_v2.md
 */

/**
 * Detect whether the API response contains a v2 result.
 * Checks for schema_version === "2.0" or the presence of result.overall.
 * @param {Object} apiResponse - Full API response from getJobResult
 * @returns {boolean}
 */
export function isResultV2(apiResponse) {
  if (!apiResponse) return false;
  const inner = apiResponse.result ?? apiResponse;
  return (
    inner?.schema_version === '2.0' ||
    inner?.overall != null
  );
}

/**
 * Normalize both v1 and v2 API response shapes into a consistent accessor.
 * @param {Object} apiResponse - Full API response from getJobResult
 * @returns {{ raw: Object, result: Object, isV2: boolean }}
 */
export function getResultData(apiResponse) {
  if (!apiResponse) {
    return { raw: null, result: null, isV2: false };
  }
  const inner = apiResponse.result ?? apiResponse;
  const v2 = isResultV2(apiResponse);
  return { raw: apiResponse, result: inner, isV2: v2 };
}

/**
 * Fit-level thresholds per result_schema_v2.md:
 *   excellent: >= 85
 *   good:      70–84
 *   partial:   50–69
 *   weak:      < 50
 *
 * @param {number} score - 0–100
 * @returns {'excellent'|'good'|'partial'|'weak'}
 */
export function getFitLevel(score) {
  const s = Math.max(0, Math.min(100, Number(score) || 0));
  if (s >= 85) return 'excellent';
  if (s >= 70) return 'good';
  if (s >= 50) return 'partial';
  return 'weak';
}

/**
 * Return a user-facing fit-level label.
 * @param {'excellent'|'good'|'partial'|'weak'} level
 * @returns {string}
 */
export function getFitLevelLabel(level) {
  const map = {
    excellent: 'Excellent',
    good: 'Good',
    partial: 'Partial',
    weak: 'Weak',
  };
  return map[level] ?? 'Unknown';
}

/**
 * Safely access nested value with fallback.
 * @param {Object} obj
 * @param {string} path - dot-separated
 * @param {*} fallback
 * @returns {*}
 */
export function safeGet(obj, path, fallback = undefined) {
  return path.split('.').reduce((acc, key) => acc?.[key], obj) ?? fallback;
}

/* ═══════════════════════════════════════════
   Evidence UX Helpers (Phase 4)
   ═══════════════════════════════════════════ */

/**
 * Remove duplicate evidence entries by (normalized_skill + text) pair.
 * @param {Array} evidence
 * @returns {Array}
 */
export function deduplicateEvidence(evidence) {
  if (!Array.isArray(evidence)) return [];
  const seen = new Set();
  return evidence.filter((ev) => {
    const key = `${(ev.normalized_skill || ev.kind || '').toLowerCase()}::${(ev.text || '').trim().toLowerCase()}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

/**
 * Group evidence items by skill/category for cleaner rendering.
 * @param {Array} evidence
 * @returns {Map<string, Array>} Map of groupLabel → evidence items
 */
export function groupEvidenceBySkill(evidence) {
  if (!Array.isArray(evidence)) return new Map();
  const groups = new Map();
  for (const ev of evidence) {
    const groupKey = ev.normalized_skill || ev.kind || 'Other';
    if (!groups.has(groupKey)) {
      groups.set(groupKey, []);
    }
    groups.get(groupKey).push(ev);
  }
  return groups;
}

/**
 * Truncate text to a maximum character length with ellipsis.
 * @param {string} text
 * @param {number} maxLen
 * @returns {string}
 */
export function truncateText(text, maxLen = 120) {
  if (!text || text.length <= maxLen) return text || '';
  return text.slice(0, maxLen).trimEnd() + '…';
}
