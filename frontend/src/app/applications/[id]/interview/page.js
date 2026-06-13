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
import { getInterviewQuestions, submitAnswer } from '@/services/interviewApi';
import { extractApiError } from '@/utils/errorHelpers';
import styles from '@/styles/Interview.module.css';

/**
 * Single question card with answer form and feedback panel.
 */
function QuestionItem({ question, index, appId }) {
  const [answerText, setAnswerText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!answerText.trim()) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const result = await submitAnswer(appId, {
        question_id: question.id || question.question_id || String(index),
        question: question.text || question.question || '',
        answer_text: answerText.trim(),
      });
      setFeedback(result);
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to submit answer. Please try again.');
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const suggestions = Array.isArray(feedback?.suggestions)
    ? feedback.suggestions
    : feedback?.improvement_tips || [];

  return (
    <article
      className={styles.questionCard}
      style={{ animationDelay: `${index * 0.08}s` }}
      id={`question-${index + 1}`}
    >
      <div className={styles.questionHeader}>
        <span className={styles.questionNumber}>{index + 1}</span>
        <p className={styles.questionText}>{question.text || question.question || '—'}</p>
        {question.category && (
          <span className={styles.questionCategory}>{question.category}</span>
        )}
      </div>

      {!feedback ? (
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
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
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
          <p className={styles.feedbackTitle}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
            AI Feedback
          </p>

          {/* Score and risk */}
          <div className={styles.feedbackScore}>
            {feedback.score != null && (
              <>
                <span className={styles.scoreValue}>{feedback.score}</span>
                <div>
                  <div className={styles.scoreMeta}>out of 10</div>
                  {feedback.risk_gap != null && (
                    <RiskBadge score={feedback.risk_gap} showScore />
                  )}
                </div>
              </>
            )}
            {feedback.risk_gap != null && feedback.score == null && (
              <RiskBadge score={feedback.risk_gap} showScore />
            )}
          </div>

          {/* Feedback text */}
          {(feedback.feedback || feedback.comment) && (
            <p className={styles.feedbackText}>
              {feedback.feedback || feedback.comment}
            </p>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className={styles.feedbackSuggestions}>
              <p className={styles.feedbackSuggestionsTitle}>Suggestions for improvement</p>
              {suggestions.map((s, i) => (
                <div key={i} className={styles.suggestionItem}>
                  <span className={styles.suggestionBullet}>▸</span>
                  <span>{typeof s === 'string' ? s : s.text || JSON.stringify(s)}</span>
                </div>
              ))}
            </div>
          )}

          {/* Retry */}
          <button
            style={{ marginTop: '1rem', fontSize: 'var(--font-size-xs)', color: 'var(--color-primary)', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            onClick={() => { setFeedback(null); setAnswerText(''); }}
          >
            ↩ Try again
          </button>
        </div>
      )}
    </article>
  );
}

export default function InterviewPage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();

  const [questions, setQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [disclaimer, setDisclaimer] = useState(null);

  const loadQuestions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getInterviewQuestions(id);
      setQuestions(Array.isArray(data?.questions) ? data.questions : []);
      setDisclaimer(data?.disclaimer || null);
    } catch (err) {
      const { message } = extractApiError(err, 'Could not load interview questions.');
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (isAuthChecking) return;
    loadQuestions();
  }, [isAuthChecking, loadQuestions]);

  const micIcon = (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
      <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Applications</Link>
        <span>›</span>
        <Link href={`/applications/${id}`} style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Application</Link>
        <span>›</span>
        <span>Interview Practice</span>
      </nav>

      <div className={styles.header}>
        <h1 className={styles.pageTitle}>Interview Practice</h1>
        <p className={styles.pageSubtitle}>
          Answer each question and receive AI-powered feedback and risk assessments.
        </p>
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
            {questions.map((q, i) => (
              <QuestionItem
                key={q.id || q.question_id || i}
                question={q}
                index={i}
                appId={id}
              />
            ))}
          </div>

          {/* Disclaimer — always visible */}
          <div className={styles.disclaimer}>
            <Disclaimer text={disclaimer} />
          </div>
        </>
      )}
    </PageShell>
  );
}
