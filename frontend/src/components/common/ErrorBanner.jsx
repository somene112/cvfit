'use client';

import styles from '@/styles/PageShell.module.css';

/**
 * ErrorBanner
 * Displays a friendly error message with an optional hint.
 * Replaces raw HTTP error strings.
 *
 * @param {{ message: string, hint?: string|null, onDismiss?: () => void, analysisRequired?: boolean }} props
 */
export default function ErrorBanner({ message, hint, onDismiss, analysisRequired = false }) {
  if (!message) return null;

  return (
    <div
      className={`${styles.errorBanner} ${analysisRequired ? styles.errorBannerWarning : ''}`}
      role="alert"
      aria-live="polite"
    >
      <div className={styles.errorBannerIcon} aria-hidden="true">
        {analysisRequired ? (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        )}
      </div>
      <div className={styles.errorBannerContent}>
        <p className={styles.errorBannerMessage}>{message}</p>
        {hint && <p className={styles.errorBannerHint}>{hint}</p>}
      </div>
      {onDismiss && (
        <button
          className={styles.errorBannerDismiss}
          onClick={onDismiss}
          aria-label="Dismiss error"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      )}
    </div>
  );
}

/**
 * AnalysisRequiredBanner
 * Pre-configured ErrorBanner for the "attach analysis first" 422 scenario.
 */
export function AnalysisRequiredBanner({ appId }) {
  return (
    <ErrorBanner
      analysisRequired
      message="Attach analysis first"
      hint="Generate an analysis for this application and attach it before creating a package or cover letter."
    />
  );
}
