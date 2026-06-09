'use client';

import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/SafeRewrite.module.css';

/**
 * SafeRewrite — Phase 4 Safe Rewrite Suggestions
 *
 * Filters improvement_actions where type === "cv_rewrite"
 * and displays them with a prominent safety warning banner.
 */
export default function SafeRewrite({ actions, evidence }) {
  const { t } = useLanguage();

  // Filter to only cv_rewrite type actions
  const rewriteActions = (actions ?? []).filter(
    (a) => a.type === 'cv_rewrite'
  );

  if (rewriteActions.length === 0) {
    return (
      <div className={styles.emptyState}>
        {t('phase4.safeRewrite.empty')}
      </div>
    );
  }

  // Build evidence lookup for linking
  const evidenceMap = {};
  if (Array.isArray(evidence)) {
    for (const ev of evidence) {
      if (ev.id) evidenceMap[ev.id] = ev;
    }
  }

  return (
    <div className={styles.rewriteContainer}>
      {/* Prominent warning banner */}
      <div className={styles.warningBanner} id="safe-rewrite-warning">
        <svg className={styles.warningIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
        <div className={styles.warningContent}>
          <span className={styles.warningTitle}>{t('phase4.safeRewrite.warning')}</span>
          <span className={styles.warningDetail}>{t('phase4.safeRewrite.warningDetail')}</span>
        </div>
      </div>

      {/* Rewrite cards */}
      {rewriteActions.map((action, index) => {
        // Find linked evidence
        const linkedEvidence = (action.related_evidence_ids ?? [])
          .map((id) => evidenceMap[id])
          .filter(Boolean);
        const currentEvidenceText = linkedEvidence
          .map((ev) => ev.text)
          .filter(Boolean)
          .join(' • ') || null;

        return (
          <div
            key={action.id ?? `rewrite-${index}`}
            className={styles.rewriteCard}
            style={{ animationDelay: `${index * 0.06}s` }}
          >
            <div className={styles.rewriteHeader}>
              <span className={styles.rewriteTitle}>{action.title}</span>
            </div>

            {/* Current evidence */}
            {currentEvidenceText && (
              <div className={styles.currentEvidence}>
                <span className={styles.evidenceLabel}>
                  {t('phase4.safeRewrite.currentEvidence')}
                </span>
                <div className={styles.evidenceText}>
                  {currentEvidenceText}
                </div>
              </div>
            )}

            {/* Suggested rewrite */}
            {action.suggestion && (
              <div className={styles.suggestedRewrite}>
                <span className={styles.evidenceLabel}>
                  {t('phase4.safeRewrite.suggestedRewrite')}
                </span>
                <div className={styles.suggestedText}>
                  {action.suggestion}
                </div>
              </div>
            )}

            {/* Guardrail */}
            {action.guardrail && (
              <div className={styles.guardrail}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>
                {action.guardrail}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
