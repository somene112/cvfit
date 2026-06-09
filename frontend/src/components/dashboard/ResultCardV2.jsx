'use client';

import { useMemo } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { getResultData, getFitLevel } from '@/utils/resultHelpers';
import ScoreCircle from './ScoreCircle';
import DownloadReport from './DownloadReport';
import EmptyState from './EmptyState';
import EvidenceSection from '@/components/results/EvidenceSection';
import ImprovementPlan from '@/components/results/ImprovementPlan';
import SafeRewrite from '@/components/results/SafeRewrite';
import InterviewPrep from '@/components/results/InterviewPrep';
import LearningRoadmap from '@/components/results/LearningRoadmap';
import styles from '@/styles/ResultCardV2.module.css';

/**
 * ResultCardV2 — Renders the v2 Result Dashboard.
 *
 * Receives the full API response and renders 8 ordered sections:
 * 1. Score Summary   2. Score Breakdown   3. Matched Skills
 * 4. Evidence        5. Missing Skills    6. Improvement Actions
 * 7. Report Download 8. Limitations
 *
 * Sections hide gracefully when their data is absent (v1 compat).
 */
export default function ResultCardV2({ result, jobId, accessToken, onNewAnalysis }) {
  const { t } = useLanguage();
  const { result: data } = useMemo(() => getResultData(result), [result]);

  if (!data) {
    return <EmptyState onRetry={onNewAnalysis} />;
  }

  /* ── Normalize v2 fields with safe fallbacks ── */
  const overall = data.overall ?? {};
  const fitScore = overall.fit_score ?? data.fit_score ?? data.scores?.fit_score ?? 0;
  const fitLevel = overall.fit_level ?? getFitLevel(fitScore);
  const summary = overall.summary ?? '';
  const confidence = overall.confidence ?? null;

  const scoreBreakdown = data.score_breakdown ?? [];
  const matchedSkills = data.matched_skills ?? [];
  const evidence = data.evidence ?? [];
  const missingSkills = data.missing_skills ?? [];
  const improvementActions = data.improvement_actions ?? [];
  const limitations = data.limitations ?? [];
  const interviewPrep = data.interview_prep ?? null;
  const learningRoadmap = data.learning_roadmap ?? null;

  const hasBreakdown = scoreBreakdown.length > 0;
  const hasMatched = matchedSkills.length > 0;
  const hasEvidence = evidence.length > 0;
  const hasMissing = missingSkills.length > 0;
  const hasImprovement = improvementActions.length > 0;
  const hasLimitations = limitations.length > 0;
  const hasInterviewPrep = interviewPrep?.questions?.length > 0;
  const hasLearningRoadmap = learningRoadmap?.items?.length > 0;
  const hasRewriteActions = improvementActions.some((a) => a.type === 'cv_rewrite');

  /* ── Fit level style mapping ── */
  const fitLevelClass = {
    excellent: styles.fitExcellent,
    good: styles.fitGood,
    partial: styles.fitPartial,
    weak: styles.fitWeak,
  }[fitLevel] ?? styles.fitPartial;

  /* ── Priority badge class ── */
  const priorityClass = (priority) => {
    const p = (priority ?? '').toLowerCase();
    if (p === 'high') return styles.priorityHigh;
    if (p === 'medium') return styles.priorityMedium;
    return styles.priorityLow;
  };

  return (
    <div className={styles.dashboardV2} id="result-dashboard-v2">

      {/* ═══════════════════════════════════════════════
          1. Score Summary
          ═══════════════════════════════════════════════ */}
      <section className={`${styles.sectionCard} ${styles.scoreSummary}`} id="v2-score-summary">
        <div className={styles.scoreSummaryInner}>
          <ScoreCircle score={fitScore} />

          <span className={`${styles.fitLevelBadge} ${fitLevelClass}`}>
            <FitLevelIcon level={fitLevel} />
            {t(`resultV2.fitLevel.${fitLevel}`)}
          </span>

          {summary && (
            <p className={styles.summaryText}>{summary}</p>
          )}

          {confidence != null && (
            <div className={styles.confidenceRow}>
              <span>{t('resultV2.scoreSummary.confidence')}</span>
              <div className={styles.confidenceBar}>
                <div
                  className={styles.confidenceFill}
                  style={{ width: `${Math.round(confidence * 100)}%` }}
                />
              </div>
              <span>{Math.round(confidence * 100)}%</span>
            </div>
          )}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════
          2. Score Breakdown
          ═══════════════════════════════════════════════ */}
      {hasBreakdown && (
        <section className={styles.sectionCard} id="v2-score-breakdown">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconPrimary}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('resultV2.scoreBreakdown.title')}</h2>
              <p className={styles.sectionSubtitle}>{t('resultV2.scoreBreakdown.subtitle')}</p>
            </div>
          </div>

          <div className={styles.breakdownGrid}>
            {scoreBreakdown.map((item) => (
              <div key={item.key} className={styles.metricCard}>
                <div className={styles.metricLabel}>{item.label}</div>
                <div className={styles.metricScoreRow}>
                  <span className={styles.metricScore}>
                    {Math.round(item.score)}
                    <span className={styles.metricUnit}>%</span>
                  </span>
                  {item.weight != null && (
                    <span className={styles.metricWeight}>
                      {t('resultV2.scoreBreakdown.weight')} {Math.round(item.weight * 100)}%
                    </span>
                  )}
                </div>
                <div className={styles.metricProgressTrack}>
                  <div
                    className={styles.metricProgressFill}
                    style={{ width: `${Math.min(100, Math.max(0, item.score))}%` }}
                  />
                </div>
                {item.explanation && (
                  <div className={styles.metricExplanation}>{item.explanation}</div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          3. Matched Skills
          ═══════════════════════════════════════════════ */}
      {hasMatched && (
        <section className={styles.sectionCard} id="v2-matched-skills">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconSuccess}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('resultV2.matchedSkills.title')}</h2>
              <p className={styles.sectionSubtitle}>
                {matchedSkills.length} {t('resultV2.matchedSkills.found')}
              </p>
            </div>
          </div>

          <div className={styles.skillsGrid}>
            {matchedSkills.map((item, index) => (
              <div
                key={`matched-v2-${index}`}
                className={styles.matchedSkillChip}
                style={{ animationDelay: `${index * 0.04}s` }}
              >
                <svg className={styles.chipIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                <span>{item.skill}</span>
                {item.confidence != null && (
                  <span className={styles.chipBadge}>
                    {Math.round(item.confidence * 100)}%
                  </span>
                )}
                {item.cv_evidence_ids?.length > 0 && (
                  <span className={styles.chipEvidenceBadge}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                    {item.cv_evidence_ids.length}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          4. Evidence Section (Phase 4 — Grouped/Truncated)
          ═══════════════════════════════════════════════ */}
      {hasEvidence && (
        <section className={styles.sectionCard} id="v2-evidence">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconPrimary}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('phase4.evidence.title')}</h2>
              <p className={styles.sectionSubtitle}>
                {t('phase4.evidence.subtitle')}
              </p>
            </div>
          </div>

          <EvidenceSection evidence={evidence} />
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          5. Missing Skills
          ═══════════════════════════════════════════════ */}
      {hasMissing && (
        <section className={styles.sectionCard} id="v2-missing-skills">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconWarning}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('resultV2.missingSkills.title')}</h2>
              <p className={styles.sectionSubtitle}>
                {missingSkills.length} {t('resultV2.missingSkills.found')}
              </p>
            </div>
          </div>

          <div className={styles.missingList}>
            {missingSkills.map((item, index) => (
              <div
                key={`missing-v2-${index}`}
                className={styles.missingCard}
                style={{ animationDelay: `${index * 0.06}s` }}
              >
                <div className={styles.missingSkillName}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="15" y1="9" x2="9" y2="15" />
                    <line x1="9" y1="9" x2="15" y2="15" />
                  </svg>
                  {item.skill}
                </div>
                <p className={styles.missingReason}>
                  {item.reason || t('resultV2.missingSkills.noEvidence')}
                </p>
                {item.suggestion && (
                  <div className={styles.missingSuggestion}>
                    {item.suggestion}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          6. Improvement Action Plan (Phase 4 — Expandable)
          ═══════════════════════════════════════════════ */}
      {hasImprovement && (
        <section className={styles.sectionCard} id="v2-improvement-actions">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconPrimary}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('phase4.improvement.title')}</h2>
              <p className={styles.sectionSubtitle}>{t('phase4.improvement.subtitle')}</p>
            </div>
          </div>

          <ImprovementPlan actions={improvementActions} />
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          6b. Safe Rewrite Suggestions (Phase 4)
          ═══════════════════════════════════════════════ */}
      {hasRewriteActions && (
        <section className={styles.sectionCard} id="v2-safe-rewrite">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconWarning}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('phase4.safeRewrite.title')}</h2>
              <p className={styles.sectionSubtitle}>{t('phase4.safeRewrite.subtitle')}</p>
            </div>
          </div>

          <SafeRewrite actions={improvementActions} evidence={evidence} />
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          6c. Interview Prep Pack (Phase 4)
          ═══════════════════════════════════════════════ */}
      {hasInterviewPrep && (
        <section className={styles.sectionCard} id="v2-interview-prep">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconPrimary}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('phase4.interviewPrep.title')}</h2>
              <p className={styles.sectionSubtitle}>{t('phase4.interviewPrep.subtitle')}</p>
            </div>
          </div>

          <InterviewPrep interviewPrep={interviewPrep} />
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          6d. Learning Roadmap (Phase 4)
          ═══════════════════════════════════════════════ */}
      {hasLearningRoadmap && (
        <section className={styles.sectionCard} id="v2-learning-roadmap">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconSuccess}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 2 7 12 12 22 7 12 2" />
                <polyline points="2 17 12 22 22 17" />
                <polyline points="2 12 12 17 22 12" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('phase4.roadmap.title')}</h2>
              <p className={styles.sectionSubtitle}>{t('phase4.roadmap.subtitle')}</p>
            </div>
          </div>

          <LearningRoadmap learningRoadmap={learningRoadmap} />
        </section>
      )}

      {/* ═══════════════════════════════════════════════
          7. Report Download + New Analysis
          ═══════════════════════════════════════════════ */}
      <div className={styles.actionsRow} id="v2-actions">
        <DownloadReport jobId={jobId} accessToken={accessToken} />
        <button
          className={styles.newAnalysisButton}
          onClick={onNewAnalysis}
          id="v2-new-analysis-button"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          {t('result.btn.new')}
        </button>
      </div>

      {/* ═══════════════════════════════════════════════
          8. Limitations / Disclaimer
          ═══════════════════════════════════════════════ */}
      {hasLimitations && (
        <section className={styles.limitationsCard} id="v2-limitations">
          <div className={styles.sectionHeader}>
            <div className={`${styles.sectionIconBox} ${styles.iconNeutral}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
            </div>
            <div>
              <h2 className={styles.sectionTitle}>{t('resultV2.limitations.title')}</h2>
            </div>
          </div>

          <div className={styles.limitationsList}>
            {limitations.map((msg, index) => (
              <div key={`lim-${index}`} className={styles.limitationItem}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <span>{msg}</span>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

/* ── Fit-level icon sub-component ── */
function FitLevelIcon({ level }) {
  if (level === 'excellent' || level === 'good') {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="20 6 9 17 4 12" />
      </svg>
    );
  }
  if (level === 'partial') {
    return (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <line x1="5" y1="12" x2="19" y2="12" />
      </svg>
    );
  }
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}
