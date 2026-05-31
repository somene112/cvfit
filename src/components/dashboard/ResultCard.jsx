'use client';

import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/ResultCard.module.css';
import ScoreCircle from './ScoreCircle';
import SkillsSection from './SkillsSection';
import DownloadReport from './DownloadReport';

export default function ResultCard({ result, jobId, accessToken, onNewAnalysis }) {
  const { t } = useLanguage();
  if (!result) return null;

  const score = result.overall_score ?? result.score ?? 0;
  const matchedSkills = result.matched_skills ?? result.matchedSkills ?? [];
  const missingSkills = result.missing_skills ?? result.missingSkills ?? [];
  const strengths = result.strengths ?? [];
  const weaknesses = result.weaknesses ?? [];
  const recommendations = result.recommendations ?? [];

  return (
    <div className={styles.card} id="result-card">
      <div className={styles.header}>
        <h2 className={styles.title}>{t('result.header.title')}</h2>
        <p className={styles.subtitle}>{t('result.header.subtitle')}</p>
      </div>

      <div className={styles.scoreSection}>
        <ScoreCircle score={score} />
      </div>

      <div className={styles.divider} />

      <SkillsSection matchedSkills={matchedSkills} missingSkills={missingSkills} />

      <div className={styles.divider} />

      {/* Strengths */}
      <div className={styles.infoSection}>
        <div className={styles.sectionHeader}>
          <svg className={`${styles.sectionIcon} ${styles.strengthIcon}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
          <h3 className={styles.sectionTitle}>{t('feedback.strengths')}</h3>
        </div>
        <div className={styles.infoList}>
          {strengths.length > 0 ? (
            strengths.map((item, index) => (
              <div
                key={`strength-${index}`}
                className={styles.infoItem}
                style={{ animationDelay: `${index * 0.08}s` }}
              >
                <svg className={`${styles.itemIcon} ${styles.strengthIcon}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {item}
              </div>
            ))
          ) : (
            <p className={styles.emptyText}>{t('feedback.empty.strengths')}</p>
          )}
        </div>
      </div>

      {/* Weaknesses */}
      <div className={styles.infoSection}>
        <div className={styles.sectionHeader}>
          <svg className={`${styles.sectionIcon} ${styles.weaknessIcon}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <h3 className={styles.sectionTitle}>{t('feedback.weaknesses')}</h3>
        </div>
        <div className={styles.infoList}>
          {weaknesses.length > 0 ? (
            weaknesses.map((item, index) => (
              <div
                key={`weakness-${index}`}
                className={styles.infoItem}
                style={{ animationDelay: `${index * 0.08}s` }}
              >
                <svg className={`${styles.itemIcon} ${styles.weaknessIcon}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {item}
              </div>
            ))
          ) : (
            <p className={styles.emptyText}>{t('feedback.empty.weaknesses')}</p>
          )}
        </div>
      </div>

      {/* Recommendations */}
      <div className={styles.infoSection}>
        <div className={styles.sectionHeader}>
          <svg className={`${styles.sectionIcon} ${styles.recommendIcon}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <h3 className={styles.sectionTitle}>{t('feedback.recommendations')}</h3>
        </div>
        <div className={styles.infoList}>
          {recommendations.length > 0 ? (
            recommendations.map((item, index) => (
              <div
                key={`recommendation-${index}`}
                className={styles.infoItem}
                style={{ animationDelay: `${index * 0.08}s` }}
              >
                <svg className={`${styles.itemIcon} ${styles.recommendIcon}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 18l6-6-6-6" />
                </svg>
                {item}
              </div>
            ))
          ) : (
            <p className={styles.emptyText}>{t('feedback.empty.recommendations')}</p>
          )}
        </div>
      </div>

      <div className={styles.actions}>
        <DownloadReport jobId={jobId} accessToken={accessToken} />
        <button
          className={styles.newAnalysisButton}
          onClick={onNewAnalysis}
          id="new-analysis-button"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
          {t('result.btn.new')}
        </button>
      </div>
    </div>
  );
}
