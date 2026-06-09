'use client';

import { useState } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/ImprovementPlan.module.css';

/**
 * ImprovementPlan — Phase 4 Improvement Action Plan UI
 *
 * Displays action cards with:
 * - Priority badge (HIGH / MEDIUM / LOW)
 * - Action type badge (skill_gap / cv_rewrite)
 * - Status indicator
 * - Linked skill chip
 * - Expandable details with suggestion + guardrail
 */
export default function ImprovementPlan({ actions }) {
  const { t } = useLanguage();
  const [expandedCards, setExpandedCards] = useState(new Set());

  if (!actions || actions.length === 0) {
    return (
      <div className={styles.emptyState}>
        {t('phase4.improvement.empty')}
      </div>
    );
  }

  const toggleCard = (id) => {
    setExpandedCards((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const priorityClass = (priority) => {
    const p = (priority ?? '').toLowerCase();
    if (p === 'high') return styles.priorityHigh;
    if (p === 'medium') return styles.priorityMedium;
    return styles.priorityLow;
  };

  return (
    <div className={styles.planContainer}>
      {actions.map((action, index) => {
        const cardId = action.id ?? `action-${index}`;
        const isOpen = expandedCards.has(cardId);
        const status = action.status ?? 'pending';

        return (
          <div
            key={cardId}
            className={styles.actionCard}
            style={{ animationDelay: `${index * 0.06}s` }}
          >
            {/* Card header — clickable to expand */}
            <div
              className={styles.actionCardHeader}
              onClick={() => toggleCard(cardId)}
              role="button"
              tabIndex={0}
              aria-expanded={isOpen}
              id={`action-card-${cardId}`}
            >
              <div className={styles.actionCardLeft}>
                <span className={`${styles.priorityBadge} ${priorityClass(action.priority)}`}>
                  {(action.priority ?? 'low').toUpperCase()}
                </span>
                {action.type && (
                  <span className={styles.typeBadge}>
                    {t(`phase4.improvement.type.${action.type}`) || action.type}
                  </span>
                )}
                <span className={styles.actionTitle}>{action.title}</span>
              </div>
              <span className={`${styles.statusBadge} ${status === 'done' ? styles.statusDone : styles.statusPending}`}>
                {t(`phase4.improvement.status.${status}`)}
              </span>
              <svg
                className={`${styles.chevron} ${isOpen ? styles.chevronExpanded : ''}`}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>

            {/* Expanded details */}
            {isOpen && (
              <div className={styles.actionDetails}>
                {/* Linked skill */}
                {action.related_skill && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>{t('phase4.improvement.linkedSkill')}</span>
                    <div>
                      <span className={styles.linkedSkillChip}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="8" x2="12" y2="12" />
                          <line x1="12" y1="16" x2="12.01" y2="16" />
                        </svg>
                        {action.related_skill}
                      </span>
                    </div>
                  </div>
                )}

                {/* Reason / suggestion */}
                {action.suggestion && (
                  <div className={styles.detailRow}>
                    <span className={styles.detailLabel}>{t('phase4.improvement.safeSuggestion')}</span>
                    <p className={styles.detailValue}>{action.suggestion}</p>
                  </div>
                )}

                {/* Guardrail */}
                {action.guardrail && (
                  <div className={styles.guardrailNotice}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    </svg>
                    {action.guardrail}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
