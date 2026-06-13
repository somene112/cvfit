'use client';

import Header from '@/components/dashboard/Header';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import styles from '@/styles/PageShell.module.css';

/**
 * PageShell
 * Standard authenticated page layout. Wraps Header + main content area.
 * Handles auth-checking loading state at page level.
 *
 * @param {{ isAuthChecking?: boolean, children: React.ReactNode, maxWidth?: string }} props
 */
export default function PageShell({ isAuthChecking, children, maxWidth = '960px' }) {
  if (isAuthChecking) {
    return (
      <div className={styles.page}>
        <LoadingSpinner fullPage label="Checking session…" />
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Header />
      <main className={styles.main} style={{ maxWidth }}>
        {children}
      </main>
    </div>
  );
}
