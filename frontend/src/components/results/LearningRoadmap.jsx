'use client';

import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/LearningRoadmap.module.css';

/**
 * LearningRoadmap — Phase 4 Learning Path
 *
 * Vertical timeline cards with topic chips and mini project ideas.
 * Data shape: result.learning_roadmap.items[]
 */
export default function LearningRoadmap({ learningRoadmap }) {
  const { t } = useLanguage();

  const items = learningRoadmap?.items ?? [];

  if (items.length === 0) {
    return (
      <div className={styles.emptyState}>
        {t('phase4.roadmap.empty')}
      </div>
    );
  }

  const priorityDotClass = (priority) => {
    const p = (priority ?? '').toLowerCase();
    if (p === 'high') return styles.dotHigh;
    if (p === 'medium') return styles.dotMedium;
    return styles.dotLow;
  };

  const priorityBadgeClass = (priority) => {
    const p = (priority ?? '').toLowerCase();
    if (p === 'high') return styles.priorityHigh;
    if (p === 'medium') return styles.priorityMedium;
    return styles.priorityLow;
  };

  return (
    <div className={styles.roadmapContainer}>
      {items.map((item, index) => (
        <div
          key={`roadmap-${index}`}
          className={styles.roadmapCard}
          style={{ animationDelay: `${index * 0.08}s` }}
        >
          {/* Timeline dot */}
          <div className={`${styles.timelineDot} ${priorityDotClass(item.priority)}`}>
            {index + 1}
          </div>

          {/* Card content */}
          <div className={styles.cardContent}>
            <div className={styles.cardHeader}>
              <span className={styles.skillName}>{item.skill}</span>
              <span className={`${styles.priorityBadge} ${priorityBadgeClass(item.priority)}`}>
                {(item.priority ?? 'low').toUpperCase()}
              </span>
            </div>

            {item.why && (
              <p className={styles.whySection}>{item.why}</p>
            )}

            {/* Topics */}
            {Array.isArray(item.topics) && item.topics.length > 0 && (
              <div className={styles.detailBlock}>
                <span className={styles.detailLabel}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                  </svg>
                  {t('phase4.roadmap.topics')}
                </span>
                <div className={styles.topicChips}>
                  {item.topics.map((topic, tIndex) => (
                    <span key={`topic-${index}-${tIndex}`} className={styles.topicChip}>
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Mini project */}
            {item.mini_project && (
              <div className={styles.detailBlock}>
                <span className={styles.detailLabel}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="12 2 2 7 12 12 22 7 12 2" />
                    <polyline points="2 17 12 22 22 17" />
                    <polyline points="2 12 12 17 22 12" />
                  </svg>
                  {t('phase4.roadmap.miniProject')}
                </span>
                <div className={styles.miniProjectBox}>
                  {item.mini_project}
                </div>
              </div>
            )}

            {/* CV evidence to add */}
            {item.cv_evidence_to_add && (
              <div className={styles.detailBlock}>
                <span className={styles.detailLabel}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="12" y1="18" x2="12" y2="12" />
                    <line x1="9" y1="15" x2="15" y2="15" />
                  </svg>
                  {t('phase4.roadmap.cvEvidence')}
                </span>
                <div className={styles.cvEvidenceBox}>
                  {item.cv_evidence_to_add}
                </div>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
