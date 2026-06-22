'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { getSession, submitSessionAnswer } from '@/services/interviewSessionsApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import styles from '@/styles/InterviewSessions.module.css';

const RUBRIC_KEYS = ['relevance', 'evidence', 'clarity', 'structure', 'confidence', 'risk'];

const RUBRIC_LABELS = {
  relevance: 'Relevance',
  evidence: 'Evidence',
  clarity: 'Clarity',
  structure: 'Structure',
  confidence: 'Confidence',
  risk: 'Risk',
};

const RUBRIC_DESCS = {
  relevance: 'How directly the answer addresses the question',
  evidence: 'Concrete examples and proof points used',
  clarity: 'Clear, easy to understand communication',
  structure: 'Logical flow and organisation (e.g. STAR)',
  confidence: 'Tone, assertiveness, and conviction',
  risk: 'Potential red flags or concerns raised',
};

function RubricBar({ score, max = 10 }) {
  const pct = Math.min(100, Math.round((score / max) * 100));
  return (
    <div className={styles.rubricBar}>
      <div className={styles.rubricBarFill} style={{ width: `${pct}%` }} />
    </div>
  );
}

export default function SessionDetailPage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();

  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [activeQ, setActiveQ] = useState(0);
  const [answerDraft, setAnswerDraft] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [feedback, setFeedback] = useState(null); // current question feedback
  const [answersMap, setAnswersMap] = useState({}); // { questionId -> { text, feedback } }

  const loadSession = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSession(id);
      setSession(data);
      // Pre-populate answers map if session has existing answers
      if (data.answers?.length) {
        const map = {};
        data.answers.forEach((a) => {
          map[a.question_id] = { text: a.answer_text, feedback: a.feedback };
        });
        setAnswersMap(map);
      }
    } catch (err) {
      const { message } = extractApiError(err, 'Could not load session.');
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (isAuthChecking) return;
    loadSession();
  }, [isAuthChecking, loadSession]);

  // Sync draft when switching questions
  useEffect(() => {
    if (!session?.questions?.length) return;
    const q = session.questions[activeQ];
    setAnswerDraft(answersMap[q?.id]?.text || '');
    setFeedback(answersMap[q?.id]?.feedback || null);
    setSubmitError(null);
  }, [activeQ, session, answersMap]);

  const handleSubmitAnswer = async () => {
    if (!answerDraft.trim() || !session?.questions?.length) return;
    const q = session.questions[activeQ];
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      const result = await submitSessionAnswer(id, {
        question_id: q.id,
        answer_text: answerDraft.trim(),
      });
      setAnswersMap((prev) => ({
        ...prev,
        [q.id]: { text: answerDraft.trim(), feedback: result },
      }));
      setFeedback(result);
      trackEvent(ANALYTICS_EVENTS.INTERVIEW_ANSWER_SUBMITTED, {
        feature_name: 'interview_sessions',
        question_type: session.question_type,
        difficulty: session.difficulty,
      });
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to submit answer. Please try again.');
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRetry = () => {
    setFeedback(null);
    setAnswerDraft('');
  };

  const handleExport = () => {
    if (!session) return;
    const lines = [];
    lines.push(`Interview Session Export`);
    lines.push(`Type: ${session.question_type} | Difficulty: ${session.difficulty}`);
    lines.push(`Date: ${new Date().toLocaleDateString()}`);
    lines.push('');
    (session.questions || []).forEach((q, i) => {
      lines.push(`Q${i + 1}: ${q.text}`);
      const ans = answersMap[q.id];
      if (ans?.text) {
        lines.push(`Answer: ${ans.text}`);
        if (ans.feedback?.overall_score != null) {
          lines.push(`Score: ${ans.feedback.overall_score}/10`);
        }
      } else {
        lines.push('Answer: (not answered)');
      }
      lines.push('');
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `interview-session-${id}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const questions = session?.questions || [];
  const currentQ = questions[activeQ];
  const currentAns = currentQ ? answersMap[currentQ.id] : null;

  // Score trend: collect avg scores from answered questions
  const scoreTrend = questions
    .map((q) => answersMap[q.id]?.feedback?.overall_score ?? null)
    .filter((s) => s !== null);
  const maxTrend = Math.max(...scoreTrend, 10);

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="1080px">
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/interview/sessions">Interview Practice</Link>
        <span className={styles.breadcrumbSep}>›</span>
        <span>{session ? `${session.question_type?.replace(/_/g, ' ')} — ${session.difficulty}` : 'Loading…'}</span>
      </nav>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {isLoading && <LoadingSpinner fullPage label="Loading session…" />}

      {!isLoading && session && (
        <>
          {/* Top bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '0.75rem', animation: 'fadeInDown 0.3s ease-out' }}>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
              <span style={{ padding: '3px 10px', borderRadius: 'var(--radius-full)', background: 'var(--color-primary-light)', color: 'var(--color-primary)', fontSize: 'var(--font-size-xs)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                {session.question_type?.replace(/_/g, ' ')}
              </span>
              <span style={{ padding: '3px 10px', borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', ...(session.difficulty === 'easy' ? { background: '#D1FAE5', color: '#065F46' } : session.difficulty === 'hard' ? { background: '#FEE2E2', color: '#991B1B' } : { background: '#FEF3C7', color: '#B45309' }) }}>
                {session.difficulty}
              </span>
              <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
                {questions.length} question{questions.length !== 1 ? 's' : ''}
                {' · '}{Object.keys(answersMap).length} answered
              </span>
            </div>
            <button className={styles.exportBtn} onClick={handleExport} id="export-session-btn">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              Export Summary
            </button>
          </div>

          <div className={styles.sessionLayout}>
            {/* Question Nav */}
            <aside className={styles.questionNav} aria-label="Question list">
              <div className={styles.navTitle}>Questions</div>
              <div className={styles.questionList}>
                {questions.map((q, i) => {
                  const answered = !!answersMap[q.id];
                  const isActive = i === activeQ;
                  return (
                    <button
                      key={q.id}
                      type="button"
                      className={`${styles.questionNavItem} ${isActive ? styles['questionNavItem--active'] : ''}`}
                      onClick={() => setActiveQ(i)}
                      id={`qnav-${i}`}
                    >
                      <span className={`${styles.qNavNum} ${isActive ? styles['qNavNum--active'] : answered ? styles['qNavNum--answered'] : ''}`}>
                        {answered && !isActive ? '✓' : i + 1}
                      </span>
                      <span className={styles.qNavText}>{q.text}</span>
                    </button>
                  );
                })}
              </div>
            </aside>

            {/* Main Area */}
            <div className={styles.practiceArea}>
              {/* Question Card */}
              {currentQ && (
                <div className={styles.questionCard}>
                  <div className={styles.questionMeta}>
                    <span className={styles.qTypeBadge}>Q{activeQ + 1} of {questions.length}</span>
                    {currentQ.type && <span className={styles.qTypeBadge} style={{ background: '#EDE9FE', color: '#5B21B6' }}>{currentQ.type.replace(/_/g, ' ')}</span>}
                  </div>
                  <p className={styles.questionText}>{currentQ.text}</p>

                  {!feedback ? (
                    <>
                      <textarea
                        className={styles.answerTextarea}
                        value={answerDraft}
                        onChange={(e) => setAnswerDraft(e.target.value)}
                        placeholder="Type your answer here… Use the STAR method for behavioral questions (Situation, Task, Action, Result)."
                        disabled={isSubmitting}
                        id={`answer-input-${activeQ}`}
                      />
                      {submitError && (
                        <div style={{ color: 'var(--color-danger)', fontSize: 'var(--font-size-sm)', marginTop: '0.5rem' }}>
                          {submitError}
                        </div>
                      )}
                      <div className={styles.answerActions}>
                        {activeQ > 0 && (
                          <button type="button" className={styles.btnSecondary} onClick={() => setActiveQ((p) => p - 1)}>
                            ← Previous
                          </button>
                        )}
                        <button
                          type="button"
                          className={styles.btnPrimary}
                          onClick={handleSubmitAnswer}
                          disabled={!answerDraft.trim() || isSubmitting}
                          id={`submit-answer-${activeQ}`}
                        >
                          {isSubmitting ? (
                            <>
                              <span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
                              Evaluating…
                            </>
                          ) : 'Submit Answer'}
                        </button>
                        {activeQ < questions.length - 1 && (
                          <button type="button" className={styles.btnSecondary} onClick={() => setActiveQ((p) => p + 1)}>
                            Skip →
                          </button>
                        )}
                      </div>
                    </>
                  ) : (
                    <div className={styles.answerActions}>
                      <button type="button" className={styles.btnOutline} onClick={handleRetry} id={`retry-answer-${activeQ}`}>
                        ↺ Retry Answer
                      </button>
                      {activeQ < questions.length - 1 && (
                        <button type="button" className={styles.btnPrimary} onClick={() => setActiveQ((p) => p + 1)}>
                          Next Question →
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Feedback Panel */}
              {feedback && (
                <div className={styles.feedbackCard}>
                  <div className={styles.feedbackTitle}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                    </svg>
                    AI Feedback
                    {feedback.overall_score != null && (
                      <span style={{ marginLeft: 'auto', fontSize: 'var(--font-size-xl)', fontWeight: 800, color: 'var(--color-primary)', letterSpacing: '-0.04em' }}>
                        {feedback.overall_score}<span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 400, color: '#7C3AED', marginLeft: 1 }}>/10</span>
                      </span>
                    )}
                  </div>

                  {feedback.feedback_text && (
                    <p className={styles.feedbackText}>{feedback.feedback_text}</p>
                  )}

                  {/* Rubric Grid */}
                  <div className={styles.rubricGrid}>
                    {RUBRIC_KEYS.map((key) => {
                      const score = feedback[key] ?? feedback.rubric?.[key];
                      if (score == null) return null;
                      return (
                        <div key={key} className={styles.rubricItem} title={RUBRIC_DESCS[key]}>
                          <div className={styles.rubricLabel}>{RUBRIC_LABELS[key]}</div>
                          <div className={styles.rubricScore}>{score}<span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', fontWeight: 400 }}>/10</span></div>
                          <RubricBar score={score} />
                        </div>
                      );
                    })}
                  </div>

                  {feedback.suggestions?.length > 0 && (
                    <div style={{ marginTop: '0.5rem' }}>
                      <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#6D28D9', marginBottom: '0.5rem' }}>
                        Suggestions
                      </div>
                      <ul style={{ listStyle: 'disc', paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                        {feedback.suggestions.map((s, i) => (
                          <li key={i} style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5 }}>{s}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Score Trend */}
              {scoreTrend.length > 1 && (
                <div className={styles.trendSection}>
                  <div className={styles.trendTitle}>📈 Score Trend</div>
                  <div className={styles.trendBars}>
                    {scoreTrend.map((score, i) => (
                      <div
                        key={i}
                        className={`${styles.trendBar} ${i === scoreTrend.length - 1 ? styles['trendBar--current'] : ''}`}
                        style={{ height: `${Math.max(10, (score / maxTrend) * 100)}%` }}
                        title={`Q${i + 1}: ${score}/10`}
                      />
                    ))}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.375rem', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                    <span>Q1</span>
                    <span>Q{scoreTrend.length}</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </PageShell>
  );
}
