'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ErrorBanner from '@/components/common/ErrorBanner';
import EmptyStatePage from '@/components/common/EmptyStatePage';
import RiskBadge from '@/components/common/RiskBadge';
import Disclaimer from '@/components/common/Disclaimer';
import { getInterviewQuestions, submitAnswer, getAnswers } from '@/services/interviewApi';
import { extractApiError } from '@/utils/errorHelpers';
import styles from '@/styles/Interview.module.css';

/* ─────────────────────────────────────────
   Rubric row component
───────────────────────────────────────── */
function RubricRow({ label, value }) {
  if (value == null) return null;
  const pct = Math.round((value / 5) * 100);
  return (
    <div className={styles.rubricRow}>
      <span className={styles.rubricLabel}>{label}</span>
      <div className={styles.rubricBarWrap}>
        <div className={styles.rubricBar} style={{ width: `${pct}%` }} />
      </div>
      <span className={styles.rubricScore}>{value}/5</span>
    </div>
  );
}

/* ─────────────────────────────────────────
   Feedback section helper
───────────────────────────────────────── */
function FeedbackSection({ title, items }) {
  if (!items || (Array.isArray(items) && items.length === 0)) return null;
  const list = Array.isArray(items) ? items : [items];
  return (
    <div className={styles.feedbackSection}>
      <p className={styles.feedbackSectionTitle}>{title}</p>
      {list.map((item, i) => (
        <div key={i} className={styles.suggestionItem}>
          <span className={styles.suggestionBullet}>▸</span>
          <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
        </div>
      ))}
    </div>
  );
}

/* ─────────────────────────────────────────
   Single question card
───────────────────────────────────────── */
function QuestionItem({ question, index, appId, pastAnswer }) {
  const [answerText, setAnswerText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState(null);   // { rubric, feedback }
  const [error, setError] = useState(null);
  const [showHistory, setShowHistory] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answerText.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const data = await submitAnswer(appId, {
        question_id: question.id || question.question_id || String(index),
        question: question.text || question.question || '',
        answer_text: answerText.trim(),
      });
      setResult(data);
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to submit answer. Please try again.');
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const rubric = result?.rubric || {};
  const feedback = result?.feedback || {};
  const overall = rubric.overall ?? null;
  const riskGap = rubric.risk_gap ?? null;

  return (
    <article
      className={styles.questionCard}
      style={{ animationDelay: `${index * 0.08}s` }}
      id={`question-${index + 1}`}
    >
      {/* Question header */}
      <div className={styles.questionHeader}>
        <span className={styles.questionNumber}>{index + 1}</span>
        <p className={styles.questionText}>{question.text || question.question || '—'}</p>
        {question.category && (
          <span className={styles.questionCategory}>{question.category}</span>
        )}
      </div>

      {/* Past answer badge */}
      {pastAnswer && !result && (
        <button
          className={styles.historyToggle}
          onClick={() => setShowHistory((v) => !v)}
          id={`history-toggle-${index + 1}`}
        >
          {showHistory ? '▲ Hide previous answer' : '▼ Show previous answer'}
        </button>
      )}
      {showHistory && pastAnswer && (
        <div className={styles.historyPanel}>
          <p className={styles.historyLabel}>Your previous answer</p>
          <p className={styles.historyText}>{pastAnswer.answer_text}</p>
        </div>
      )}

      {/* Answer form or feedback */}
      {!result ? (
        <form onSubmit={handleSubmit} className={styles.answerForm}>
          <textarea
            className={styles.answerTextarea}
            value={answerText}
            onChange={(e) => setAnswerText(e.target.value)}
            placeholder="Type your answer here…"
            disabled={isSubmitting}
            id={`answer-textarea-${index + 1}`}
            aria-label={`Answer for question ${index + 1}`}
          />
          {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
          <div className={styles.answerFooter}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
              {answerText.length} characters
            </span>
            <button
              type="submit"
              className={styles.submitBtn}
              disabled={isSubmitting || !answerText.trim()}
              id={`submit-answer-btn-${index + 1}`}
            >
              {isSubmitting ? (
                <><span className={styles.submitSpinner} /> Submitting…</>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                    strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
                    <line x1="22" y1="2" x2="11" y2="13" />
                    <polygon points="22 2 15 22 11 13 2 9 22 2" />
                  </svg>
                  Submit Answer
                </>
              )}
            </button>
          </div>
        </form>
      ) : (
        <div className={styles.feedbackPanel}>
          {/* ── Header ── */}
          <p className={styles.feedbackTitle}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            AI Feedback
          </p>

          {/* ── Overall score + risk_gap ── */}
          <div className={styles.feedbackScore}>
            {overall != null && (
              <>
                <span className={styles.scoreValue}>{overall}</span>
                <div>
                  <div className={styles.scoreMeta}>overall / 5</div>
                  {riskGap != null && <RiskBadge score={riskGap} showScore />}
                </div>
              </>
            )}
            {riskGap != null && overall == null && (
              <RiskBadge score={riskGap} showScore />
            )}
          </div>

          {/* ── Rubric breakdown ── */}
          {Object.keys(rubric).some((k) => k !== 'overall' && k !== 'risk_gap' && rubric[k] != null) && (
            <div className={styles.rubricGrid}>
              <p className={styles.feedbackSuggestionsTitle}>Rubric Breakdown</p>
              <RubricRow label="Relevance"    value={rubric.relevance} />
              <RubricRow label="Specificity"  value={rubric.specificity} />
              <RubricRow label="Evidence"     value={rubric.evidence} />
              <RubricRow label="Structure"    value={rubric.structure} />
              <RubricRow label="Risk / Gap"   value={rubric.risk_gap} />
            </div>
          )}

          {/* ── Feedback sections ── */}
          <FeedbackSection title="💪 Strengths"            items={feedback.strengths} />
          <FeedbackSection title="📎 Missing Evidence"     items={feedback.missing_evidence} />
          <FeedbackSection title="🔧 Suggested Improvements" items={feedback.suggested_improvements} />
          <FeedbackSection title="📋 Sample Outline"       items={feedback.sample_outline} />
          <FeedbackSection title="⚠️ Risk Notes"           items={feedback.risk_notes} />

          {/* ── Disclaimer — always visible ── */}
          {feedback.disclaimer && (
            <div className={styles.inlineFeedbackDisclaimer}>
              <Disclaimer text={feedback.disclaimer} title="AI Disclaimer" />
            </div>
          )}

          {/* ── Retry ── */}
          <button
            className={styles.retryBtn}
            onClick={() => { setResult(null); setAnswerText(''); }}
            id={`retry-answer-btn-${index + 1}`}
          >
            ↩ Try again
          </button>
        </div>
      )}
    </article>
  );
}

/* ─────────────────────────────────────────
   Page
───────────────────────────────────────── */
export default function InterviewPage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();

  const [questions, setQuestions]   = useState([]);
  const [answers, setAnswers]       = useState([]);   // answer history
  const [isLoading, setIsLoading]   = useState(true);
  const [error, setError]           = useState(null);
  const [disclaimer, setDisclaimer] = useState(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Load questions and history in parallel
      const [qData, aData] = await Promise.allSettled([
        getInterviewQuestions(id),
        getAnswers(id),
      ]);

      if (qData.status === 'fulfilled') {
        setQuestions(Array.isArray(qData.value?.questions) ? qData.value.questions : []);
        setDisclaimer(qData.value?.disclaimer || null);
      } else {
        const { message } = extractApiError(qData.reason, 'Could not load interview questions.');
        setError(message);
      }

      if (aData.status === 'fulfilled') {
        setAnswers(Array.isArray(aData.value?.items) ? aData.value.items : []);
      }
      // silently ignore answer history errors — not critical
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (isAuthChecking) return;
    loadData();
  }, [isAuthChecking, loadData]);

  /** Map question_id → latest answer object */
  const answerMap = answers.reduce((acc, a) => {
    const key = a.question_id || a.id;
    if (key) acc[key] = a;
    return acc;
  }, {});

  const micIcon = (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" style={{
        display: 'flex', alignItems: 'center', gap: '0.5rem',
        fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '1.5rem',
      }}>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>
          Applications
        </Link>
        <span>›</span>
        <Link href={`/applications/${id}`} style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>
          Application
        </Link>
        <span>›</span>
        <span>Interview Practice</span>
      </nav>

      <div className={styles.header}>
        <h1 className={styles.pageTitle}>Interview Practice</h1>
        <p className={styles.pageSubtitle}>
          Answer each question and receive AI-powered feedback and risk assessments.
        </p>
        {answers.length > 0 && (
          <span className={styles.historyBadge}>
            {answers.length} answer{answers.length > 1 ? 's' : ''} in history
          </span>
        )}
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {isLoading && <LoadingSpinner fullPage label="Loading questions…" />}

      {!isLoading && !error && questions.length === 0 && (
        <EmptyStatePage
          icon={micIcon}
          title="No questions available"
          description="Interview questions will appear here once your application analysis is ready and processed."
        />
      )}

      {!isLoading && questions.length > 0 && (
        <>
          <div className={styles.questionsList}>
            {questions.map((q, i) => {
              const qKey = q.id || q.question_id || String(i);
              return (
                <QuestionItem
                  key={qKey}
                  question={q}
                  index={i}
                  appId={id}
                  pastAnswer={answerMap[qKey] || null}
                />
              );
            })}
          </div>

          {/* Global disclaimer — always visible */}
          <div className={styles.disclaimer}>
            <Disclaimer text={disclaimer} />
          </div>
        </>
      )}
    </PageShell>
  );
}
