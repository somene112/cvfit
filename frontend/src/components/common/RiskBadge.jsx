'use client';

import { getRiskLevel } from '@/utils/riskHelpers';
import styles from '@/styles/PageShell.module.css';

/**
 * RiskBadge
 * Displays a coloured risk level badge based on backend risk_gap score (0–5).
 *   0–1 → 🟢 Low Risk
 *   2–3 → 🟡 Medium Risk
 *   4–5 → 🔴 High Risk
 *
 * @param {{ score: number|null|undefined, showScore?: boolean }} props
 */
export default function RiskBadge({ score, showScore = false }) {
  const { label, emoji, level } = getRiskLevel(score);

  return (
    <span
      className={`${styles.riskBadge} ${styles[`riskBadge--${level}`]}`}
      aria-label={`Risk level: ${label}`}
    >
      <span aria-hidden="true">{emoji}</span>
      <span>{label}</span>
      {showScore && score !== null && score !== undefined && (
        <span className={styles.riskScore}>({score}/5)</span>
      )}
    </span>
  );
}
