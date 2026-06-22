'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import { createSession } from '@/services/interviewSessionsApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import styles from '@/styles/InterviewSessions.module.css';

const QUESTION_TYPES = [
  { value: 'technical', label: 'Technical', icon: '💻', desc: 'Code, systems, problem-solving' },
  { value: 'behavioral', label: 'Behavioral', icon: '🤝', desc: 'Teamwork, leadership, STAR stories' },
  { value: 'project', label: 'Project', icon: '📁', desc: 'Past work, achievements, impact' },
  { value: 'HR', label: 'HR / Culture', icon: '🌐', desc: 'Fit, salary, career goals' },
  { value: 'gap_check', label: 'Gap Check', icon: '🔍', desc: 'Skill gaps from your CV analysis' },
];

const DIFFICULTIES = [
  { value: 'easy', label: 'Easy', icon: '🟢', desc: 'Warm-up, foundational' },
  { value: 'medium', label: 'Medium', icon: '🟡', desc: 'Standard interview level' },
  { value: 'hard', label: 'Hard', icon: '🔴', desc: 'Senior / competitive' },
];

export default function NewSessionPage() {
  const { isAuthChecking } = useRequireAuth();
  const router = useRouter();

  const [questionType, setQuestionType] = useState('behavioral');
  const [difficulty, setDifficulty] = useState('medium');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleStart(e) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const session = await createSession({ question_type: questionType, difficulty });
      trackEvent(ANALYTICS_EVENTS.INTERVIEW_SESSION_CREATED, {
        feature_name: 'interview_sessions',
        question_type: questionType,
        difficulty,
      });
      router.push(`/interview/sessions/${session.id}`);
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to start session. Please try again.');
      setError(message);
      setIsSubmitting(false);
    }
  }

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="700px">
      {/* Breadcrumb */}
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/interview/sessions">Interview Practice</Link>
        <span className={styles.breadcrumbSep}>›</span>
        <span>New Session</span>
      </nav>

      <div className={styles.formCard}>
        <h1 className={styles.formTitle}>Start a Practice Session</h1>
        <p className={styles.formSubtitle}>
          Choose a question type and difficulty. The AI will generate targeted questions and provide rubric-based feedback on your answers.
        </p>

        {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

        <form onSubmit={handleStart} id="new-session-form">
          {/* Question Type */}
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel}>Question Type</label>
            <div className={styles.optionGrid}>
              {QUESTION_TYPES.map((qt) => (
                <button
                  key={qt.value}
                  type="button"
                  className={`${styles.optionCard} ${questionType === qt.value ? styles['optionCard--selected'] : ''}`}
                  onClick={() => setQuestionType(qt.value)}
                  id={`qtype-${qt.value}`}
                >
                  <div className={styles.optionIcon}>{qt.icon}</div>
                  <div className={styles.optionLabel}>{qt.label}</div>
                  <div className={styles.optionDesc}>{qt.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Difficulty */}
          <div className={styles.fieldGroup}>
            <label className={styles.fieldLabel}>Difficulty</label>
            <div className={styles.optionGrid} style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              {DIFFICULTIES.map((d) => (
                <button
                  key={d.value}
                  type="button"
                  className={`${styles.optionCard} ${difficulty === d.value ? styles['optionCard--selected'] : ''}`}
                  onClick={() => setDifficulty(d.value)}
                  id={`difficulty-${d.value}`}
                >
                  <div className={styles.optionIcon}>{d.icon}</div>
                  <div className={styles.optionLabel}>{d.label}</div>
                  <div className={styles.optionDesc}>{d.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div className={styles.formActions}>
            <Link href="/interview/sessions" className={styles.btnSecondary}>
              Cancel
            </Link>
            <button
              type="submit"
              className={styles.btnPrimary}
              disabled={isSubmitting}
              id="start-session-btn"
            >
              {isSubmitting ? (
                <>
                  <span style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
                  Starting…
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  Start Session
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </PageShell>
  );
}
