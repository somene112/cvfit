'use client';

import styles from '@/styles/PageShell.module.css';

/**
 * Disclaimer
 * Always-visible disclaimer block. Never collapsed, never hidden.
 * Renders backend disclaimer text or a default message.
 *
 * @param {{ text?: string, title?: string }} props
 */
export default function Disclaimer({ text, title = 'Important Disclaimer' }) {
  const content =
    text ||
    'This content is AI-generated and is provided for informational purposes only. ' +
      'It should not be relied upon as professional advice. ' +
      'Always verify information independently before making career decisions.';

  return (
    <aside className={styles.disclaimer} role="note" aria-label="Disclaimer">
      <div className={styles.disclaimerIcon} aria-hidden="true">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <div className={styles.disclaimerBody}>
        <p className={styles.disclaimerTitle}>{title}</p>
        <p className={styles.disclaimerText}>{content}</p>
      </div>
    </aside>
  );
}
