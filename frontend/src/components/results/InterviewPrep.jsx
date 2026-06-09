'use client';

import { useState, useMemo } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/InterviewPrep.module.css';

const TYPE_ORDER = ['technical', 'behavioral', 'situational', 'general'];

/**
 * InterviewPrep — Phase 4 Interview Prep Pack
 *
 * Accordion sections grouped by question type.
 * Data shape: result.interview_prep.questions[]
 */
export default function InterviewPrep({ interviewPrep }) {
  const { t } = useLanguage();
  const [expandedQuestions, setExpandedQuestions] = useState(new Set());

  const questions = interviewPrep?.questions ?? [];

  const grouped = useMemo(() => {
    const groups = new Map();
    for (const q of questions) {
      const type = (q.type ?? 'general').toLowerCase();
      if (!groups.has(type)) groups.set(type, []);
      groups.get(type).push(q);
    }
    // Sort by defined order
    const sorted = new Map();
    for (const type of TYPE_ORDER) {
      if (groups.has(type)) sorted.set(type, groups.get(type));
    }
    // Add any remaining types
    for (const [type, items] of groups) {
      if (!sorted.has(type)) sorted.set(type, items);
    }
    return sorted;
  }, [questions]);

  if (questions.length === 0) {
    return (
      <div className={styles.emptyState}>
        {t('phase4.interviewPrep.empty')}
      </div>
    );
  }

  const toggleQuestion = (id) => {
    setExpandedQuestions((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const typeIconClass = (type) => {
    const map = {
      behavioral: styles.typeIconBehavioral,
      technical: styles.typeIconTechnical,
      situational: styles.typeIconSituational,
      general: styles.typeIconGeneral,
    };
    return map[type] || styles.typeIconGeneral;
  };

  const typeBadgeClass = (type) => {
    const map = {
      behavioral: styles.typeBehavioral,
      technical: styles.typeTechnical,
      situational: styles.typeSituational,
      general: styles.typeGeneral,
    };
    return map[type] || styles.typeGeneral;
  };

  let globalIndex = 0;

  return (
    <div className={styles.prepContainer}>
      {Array.from(grouped.entries()).map(([type, items], gIndex) => (
        <div
          key={type}
          className={styles.typeGroup}
          style={{ animationDelay: `${gIndex * 0.08}s` }}
        >
          <div className={styles.typeGroupHeader}>
            <div className={`${styles.typeIcon} ${typeIconClass(type)}`} />
            <span className={styles.typeLabel}>
              {t(`phase4.interviewPrep.type.${type}`) || type}
            </span>
            <span className={styles.typeCount}>
              {items.length} {t('phase4.interviewPrep.questions')}
            </span>
          </div>

          {items.map((q, qIndex) => {
            globalIndex++;
            const qId = `q-${type}-${qIndex}`;
            const isOpen = expandedQuestions.has(qId);

            return (
              <div key={qId} className={styles.questionCard}>
                <div
                  className={styles.questionHeader}
                  onClick={() => toggleQuestion(qId)}
                  role="button"
                  tabIndex={0}
                  aria-expanded={isOpen}
                >
                  <span className={styles.questionNumber}>{globalIndex}</span>
                  <span className={styles.questionText}>{q.question}</span>
                  <svg
                    className={`${styles.questionChevron} ${isOpen ? styles.questionChevronExpanded : ''}`}
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

                {isOpen && (
                  <div className={styles.questionDetails}>
                    {q.why_this_question && (
                      <div className={styles.detailBlock}>
                        <span className={styles.detailLabel}>
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <circle cx="12" cy="12" r="10" />
                            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                            <line x1="12" y1="17" x2="12.01" y2="17" />
                          </svg>
                          {t('phase4.interviewPrep.whyThisQuestion')}
                        </span>
                        <p className={styles.detailValue}>{q.why_this_question}</p>
                      </div>
                    )}

                    {q.suggested_answer_outline && (
                      <div className={styles.detailBlock}>
                        <span className={styles.detailLabel}>
                          {t('phase4.interviewPrep.suggestedOutline')}
                        </span>
                        <div className={styles.outlineBlock}>
                          {q.suggested_answer_outline}
                        </div>
                      </div>
                    )}

                    {q.related_jd_requirement && (
                      <div className={styles.detailBlock}>
                        <span className={styles.detailLabel}>
                          {t('phase4.interviewPrep.relatedJd')}
                        </span>
                        <div className={styles.relatedBlock}>
                          {q.related_jd_requirement}
                        </div>
                      </div>
                    )}

                    {q.related_cv_evidence && (
                      <div className={styles.detailBlock}>
                        <span className={styles.detailLabel}>
                          {t('phase4.interviewPrep.relatedCv')}
                        </span>
                        <div className={styles.relatedBlock}>
                          {q.related_cv_evidence}
                        </div>
                      </div>
                    )}

                    {q.risk_if_user_cannot_answer && (
                      <div className={styles.detailBlock}>
                        <span className={styles.detailLabel}>
                          {t('phase4.interviewPrep.risk')}
                        </span>
                        <div className={styles.riskBlock}>
                          {q.risk_if_user_cannot_answer}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}
