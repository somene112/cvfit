'use client';

import styles from '@/styles/PageShell.module.css';

/**
 * LoadingSpinner
 * Reusable spinner for page-level and inline loading states.
 *
 * @param {{ size?: 'sm' | 'md' | 'lg', label?: string, fullPage?: boolean }} props
 */
export default function LoadingSpinner({
  size = 'md',
  label = 'Loading…',
  fullPage = false,
}) {
  const spinner = (
    <div
      className={`${styles.spinner} ${styles[`spinner--${size}`]}`}
      role="status"
      aria-label={label}
    >
      <div className={styles.spinnerRing} />
      {label && <span className={styles.spinnerLabel}>{label}</span>}
    </div>
  );

  if (fullPage) {
    return <div className={styles.spinnerPage}>{spinner}</div>;
  }

  return spinner;
}
