'use client';

import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/SkillsSection.module.css';

export default function SkillsSection({ matchedSkills = [], missingSkills = [] }) {
  const { t } = useLanguage();
  return (
    <div className={styles.container} id="skills-section">
      {/* Matched Skills */}
      <div className={styles.column}>
        <div className={styles.columnHeader}>
          <svg className={`${styles.columnIcon} ${styles.matchedHeader}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <span className={`${styles.columnTitle} ${styles.matchedHeader}`}>{t('skills.matched')}</span>
          <span className={`${styles.count} ${styles.matchedCount}`}>{matchedSkills.length}</span>
        </div>
        <div className={styles.tags}>
          {matchedSkills.length > 0 ? (
            matchedSkills.map((skill, index) => (
              <span
                key={`matched-${index}`}
                className={`${styles.tag} ${styles.matchedTag}`}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <svg className={styles.tagIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {skill}
              </span>
            ))
          ) : (
            <span className={styles.emptyText}>{t('skills.empty.matched')}</span>
          )}
        </div>
      </div>

      {/* Missing Skills */}
      <div className={styles.column}>
        <div className={styles.columnHeader}>
          <svg className={`${styles.columnIcon} ${styles.missingHeader}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
          <span className={`${styles.columnTitle} ${styles.missingHeader}`}>{t('skills.missing')}</span>
          <span className={`${styles.count} ${styles.missingCount}`}>{missingSkills.length}</span>
        </div>
        <div className={styles.tags}>
          {missingSkills.length > 0 ? (
            missingSkills.map((skill, index) => (
              <span
                key={`missing-${index}`}
                className={`${styles.tag} ${styles.missingTag}`}
                style={{ animationDelay: `${index * 0.05}s` }}
              >
                <svg className={styles.tagIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
                {skill}
              </span>
            ))
          ) : (
            <span className={styles.emptyText}>{t('skills.empty.missing')}</span>
          )}
        </div>
      </div>
    </div>
  );
}
