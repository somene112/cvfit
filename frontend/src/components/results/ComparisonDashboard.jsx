'use client';

import { useMemo } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { getResultData } from '@/utils/resultHelpers';
import styles from '@/styles/ComparisonDashboard.module.css';

/**
 * ComparisonDashboard — Phase 4 Before/After Analysis
 *
 * Compares previous and current result:
 * - Score delta with arrow indicator
 * - Resolved gaps, still missing, newly matched
 * - Keyword stuffing warnings
 * - Remaining actions
 */
export default function ComparisonDashboard({ previousResult, currentResult }) {
  const { t } = useLanguage();

  const prev = useMemo(() => getResultData(previousResult), [previousResult]);
  const curr = useMemo(() => getResultData(currentResult), [currentResult]);

  if (!prev.result || !curr.result) {
    return (
      <div className={styles.unavailableState}>
        {t('phase4.comparison.unavailable')}
      </div>
    );
  }

  const prevData = prev.result;
  const currData = curr.result;

  // Scores
  const prevScore = prevData.overall?.fit_score ?? prevData.fit_score ?? 0;
  const currScore = currData.overall?.fit_score ?? currData.fit_score ?? 0;
  const delta = Math.round(currScore - prevScore);

  // Skills analysis
  const prevMissing = new Set((prevData.missing_skills ?? []).map((s) => s.skill?.toLowerCase()));
  const currMissing = new Set((currData.missing_skills ?? []).map((s) => s.skill?.toLowerCase()));
  const currMatched = new Set((currData.matched_skills ?? []).map((s) => s.skill?.toLowerCase()));
  const prevMatched = new Set((prevData.matched_skills ?? []).map((s) => s.skill?.toLowerCase()));

  const resolvedGaps = [...prevMissing].filter((s) => !currMissing.has(s));
  const stillMissing = [...currMissing].filter((s) => prevMissing.has(s));
  const newlyMatched = [...currMatched].filter((s) => !prevMatched.has(s));

  // Keyword stuffing detection
  const prevEvidenceCount = (prevData.evidence ?? []).length;
  const currEvidenceCount = (currData.evidence ?? []).length;
  const scoreJump = delta > 15;
  const evidenceGrowth = currEvidenceCount - prevEvidenceCount;
  const showStuffingWarning = scoreJump && evidenceGrowth < 3;

  // Remaining actions
  const remainingActions = (currData.improvement_actions ?? []).slice(0, 4);

  // Delta display
  const deltaClass = delta > 0 ? styles.deltaImproved
    : delta < 0 ? styles.deltaRegressed
    : styles.deltaNoChange;
  const deltaValueClass = delta > 0 ? styles.deltaValuePositive
    : delta < 0 ? styles.deltaValueNegative
    : styles.deltaValueNeutral;
  const deltaLabelKey = delta > 0 ? 'phase4.comparison.improved'
    : delta < 0 ? 'phase4.comparison.regressed'
    : 'phase4.comparison.noChange';

  return (
    <div className={styles.comparisonContainer} id="comparison-dashboard">

      {/* Score comparison cards */}
      <div className={styles.scoreComparison}>
        <div className={styles.scoreBox}>
          <span className={styles.scoreLabel}>{t('phase4.comparison.previous')}</span>
          <span className={styles.scoreValue}>
            {Math.round(prevScore)}<span className={styles.scoreUnit}>%</span>
          </span>
        </div>

        <div className={styles.deltaContainer}>
          <div className={`${styles.deltaArrow} ${deltaClass}`}>
            {delta > 0 ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            ) : delta < 0 ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <polyline points="19 12 12 19 5 12" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            )}
          </div>
          <span className={`${styles.deltaValue} ${deltaValueClass}`}>
            {delta > 0 ? '+' : ''}{delta}%
          </span>
          <span className={styles.deltaLabel}>{t(deltaLabelKey)}</span>
        </div>

        <div className={styles.scoreBox}>
          <span className={styles.scoreLabel}>{t('phase4.comparison.current')}</span>
          <span className={styles.scoreValue}>
            {Math.round(currScore)}<span className={styles.scoreUnit}>%</span>
          </span>
        </div>
      </div>

      {/* Keyword stuffing warning */}
      {showStuffingWarning && (
        <div className={styles.stuffingWarning}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div className={styles.stuffingContent}>
            <span className={styles.stuffingTitle}>{t('phase4.comparison.stuffingWarning')}</span>
            <span className={styles.stuffingDetail}>{t('phase4.comparison.stuffingDetail')}</span>
          </div>
        </div>
      )}

      {/* Resolved gaps */}
      <div className={styles.comparisonSection} style={{ animationDelay: '0.1s' }}>
        <div className={styles.sectionHeader}>
          <svg className={styles.sectionIcon} viewBox="0 0 24 24" fill="none" stroke="#10B981" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span className={styles.sectionTitle}>{t('phase4.comparison.resolvedGaps')}</span>
          <span className={styles.sectionCount}>{resolvedGaps.length}</span>
        </div>
        {resolvedGaps.length > 0 ? (
          <div className={styles.skillChipList}>
            {resolvedGaps.map((skill) => (
              <span key={`resolved-${skill}`} className={styles.skillChipResolved}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className={styles.emptySectionMessage}>No gaps resolved in this revision.</p>
        )}
      </div>

      {/* Newly matched */}
      {newlyMatched.length > 0 && (
        <div className={styles.comparisonSection} style={{ animationDelay: '0.15s' }}>
          <div className={styles.sectionHeader}>
            <svg className={styles.sectionIcon} viewBox="0 0 24 24" fill="none" stroke="#3B82F6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span className={styles.sectionTitle}>{t('phase4.comparison.newlyMatched')}</span>
            <span className={styles.sectionCount}>{newlyMatched.length}</span>
          </div>
          <div className={styles.skillChipList}>
            {newlyMatched.map((skill) => (
              <span key={`new-${skill}`} className={styles.skillChipNew}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Still missing */}
      <div className={styles.comparisonSection} style={{ animationDelay: '0.2s' }}>
        <div className={styles.sectionHeader}>
          <svg className={styles.sectionIcon} viewBox="0 0 24 24" fill="none" stroke="#F59E0B" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span className={styles.sectionTitle}>{t('phase4.comparison.stillMissing')}</span>
          <span className={styles.sectionCount}>{stillMissing.length}</span>
        </div>
        {stillMissing.length > 0 ? (
          <div className={styles.skillChipList}>
            {stillMissing.map((skill) => (
              <span key={`missing-${skill}`} className={styles.skillChipMissing}>
                {skill}
              </span>
            ))}
          </div>
        ) : (
          <p className={styles.emptySectionMessage}>All previous gaps have been resolved!</p>
        )}
      </div>

      {/* Remaining actions */}
      {remainingActions.length > 0 && (
        <div className={styles.comparisonSection} style={{ animationDelay: '0.25s' }}>
          <div className={styles.sectionHeader}>
            <svg className={styles.sectionIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20h9" />
              <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
            </svg>
            <span className={styles.sectionTitle}>{t('phase4.comparison.nextActions')}</span>
            <span className={styles.sectionCount}>{remainingActions.length}</span>
          </div>
          <div className={styles.skillChipList}>
            {remainingActions.map((action, i) => (
              <span key={`action-${i}`} className={styles.skillChipMissing}>
                {action.title}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
