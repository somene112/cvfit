'use client';

import styles from '@/styles/PageShell.module.css';

/**
 * EmptyStatePage
 * Full-area empty state with icon, heading, description, and optional CTA.
 *
 * @param {{ icon?: React.ReactNode, title: string, description?: string, action?: React.ReactNode }} props
 */
export default function EmptyStatePage({ icon, title, description, action }) {
  return (
    <div className={styles.emptyState} role="status">
      {icon && <div className={styles.emptyStateIcon} aria-hidden="true">{icon}</div>}
      <h2 className={styles.emptyStateTitle}>{title}</h2>
      {description && <p className={styles.emptyStateDesc}>{description}</p>}
      {action && <div className={styles.emptyStateAction}>{action}</div>}
    </div>
  );
}
