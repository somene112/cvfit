'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import EmptyStatePage from '@/components/common/EmptyStatePage';
import { listSessions } from '@/services/interviewSessionsApi';
import { extractApiError } from '@/utils/errorHelpers';
import styles from '@/styles/InterviewSessions.module.css';

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString();
}

function DifficultyBadge({ difficulty }) {
  const cls =
    difficulty === 'easy' ? styles['diff--easy'] :
    difficulty === 'hard' ? styles['diff--hard'] :
    styles['diff--medium'];
  return <span className={`${styles.difficultyBadge} ${cls}`}>{difficulty || 'medium'}</span>;
}

function SkeletonCard() {
  return (
    <div className={styles.skeletonCard}>
      <div className={`${styles.skeletonLine} ${styles['skeletonLine--wide']}`} />
      <div className={`${styles.skeletonLine} ${styles['skeletonLine--med']}`} />
      <div className={`${styles.skeletonLine} ${styles['skeletonLine--short']}`} style={{ marginTop: '0.75rem' }} />
    </div>
  );
}

export default function InterviewSessionsPage() {
  const { isAuthChecking } = useRequireAuth();
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await listSessions();
        if (!active) return;
        setSessions(Array.isArray(data?.items) ? data.items : []);
      } catch (err) {
        if (!active) return;
        const { message } = extractApiError(err, 'Could not load interview sessions.');
        setError(message);
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking]);

  const micIcon = (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="860px">
      <div className={styles.topRow}>
        <div>
          <h1 className={styles.pageTitle}>Interview Practice</h1>
          <p className={styles.pageSubtitle}>
            Practice AI-generated interview questions and get structured rubric feedback on every answer.
          </p>
        </div>
        <Link href="/interview/sessions/new" className={styles.newBtn} id="new-session-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Session
        </Link>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading && (
        <div className={styles.list}>
          {[1, 2, 3].map((k) => <SkeletonCard key={k} />)}
        </div>
      )}

      {!isLoading && !error && sessions.length === 0 && (
        <EmptyStatePage
          icon={micIcon}
          title="No sessions yet"
          description="Start a practice session to get AI-generated questions tailored to a question type and difficulty level. Each session saves your answers and scores."
          action={
            <Link href="/interview/sessions/new" className={styles.newBtn}>
              Start your first session
            </Link>
          }
        />
      )}

      {!isLoading && sessions.length > 0 && (
        <div className={styles.list}>
          {sessions.map((session, i) => (
            <Link
              key={session.id}
              href={`/interview/sessions/${session.id}`}
              className={styles.card}
              id={`session-card-${session.id}`}
              style={{ animationDelay: `${i * 0.06}s` }}
            >
              <div className={styles.cardHeader}>
                <div className={styles.cardTitle}>
                  {session.question_type
                    ? session.question_type.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
                    : 'Interview Session'} Session
                </div>
                <DifficultyBadge difficulty={session.difficulty} />
              </div>
              <div className={styles.cardMeta}>
                <span>{formatDate(session.created_at)}</span>
                {session.questions_count != null && (
                  <span>{session.questions_count} question{session.questions_count !== 1 ? 's' : ''}</span>
                )}
                {session.avg_score != null && (
                  <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>
                    Avg. {session.avg_score}/10
                  </span>
                )}
                {session.completed_at && (
                  <span style={{ color: 'var(--color-success)', fontWeight: 600 }}>✓ Completed</span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </PageShell>
  );
}
