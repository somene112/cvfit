'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { getLearningTask, updateLearningTask } from '@/services/learningApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import styles from '@/styles/LearningRoadmap.module.css';

const TASK_TYPE_ICONS = {
  article: '📖',
  project: '🛠',
  practice: '🎯',
  interview_prep: '🎤',
  profile_evidence: '📁',
};

const STATUS_LABELS = {
  todo: { label: 'Todo', bg: 'var(--color-border)', text: 'var(--color-text-secondary)' },
  in_progress: { label: 'In Progress', bg: 'var(--color-warning-light)', text: '#B45309' },
  done: { label: 'Done', bg: 'var(--color-success-light)', text: '#065F46' },
};

function PriorityBadge({ priority }) {
  const cls =
    priority === 'high' ? styles.priorityHigh :
    priority === 'medium' ? styles.priorityMedium :
    styles.priorityLow;
  return <span className={`${styles.priorityBadge} ${cls}`}>{priority}</span>;
}

export default function LearningTaskPage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();

  const [task, setTask] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await getLearningTask(id);
        if (!active) return;
        setTask(data);
      } catch (err) {
        if (!active) return;
        const { message } = extractApiError(err, 'Could not load this learning task.');
        setError(message);
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking, id]);

  const handleStatusChange = async (newStatus) => {
    if (!task || newStatus === task.status) return;
    setIsUpdating(true);
    try {
      const updated = await updateLearningTask(id, { status: newStatus });
      setTask((prev) => ({ ...prev, ...updated }));
      if (newStatus === 'in_progress') {
        trackEvent(ANALYTICS_EVENTS.LEARNING_TASK_STARTED, {
          feature_name: 'learning',
          task_type: task.type,
        });
      } else if (newStatus === 'done') {
        trackEvent(ANALYTICS_EVENTS.LEARNING_TASK_COMPLETED, {
          feature_name: 'learning',
          task_type: task.type,
        });
      }
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to update status.');
      setError(message);
    } finally {
      setIsUpdating(false);
    }
  };

  const dotClass = (priority) =>
    priority === 'high' ? styles.dotHigh : priority === 'medium' ? styles.dotMedium : styles.dotLow;

  const statusInfo = STATUS_LABELS[task?.status] || STATUS_LABELS.todo;

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="760px">
      {/* Breadcrumb */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: '1.5rem', animation: 'fadeInDown 0.3s ease-out' }} aria-label="Breadcrumb">
        <Link href="/learning" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Learning Roadmap</Link>
        <span>›</span>
        <span>{task ? (task.skill || task.title || 'Task') : 'Loading…'}</span>
      </nav>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {isLoading && <LoadingSpinner fullPage label="Loading task…" />}

      {!isLoading && task && (
        <>
          {/* Hero */}
          <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '2rem', marginBottom: '1.5rem', animation: 'fadeInUp 0.35s ease-out', position: 'relative', overflow: 'hidden' }}>
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 4, background: 'linear-gradient(90deg, var(--color-primary), #8B5CF6)' }} />

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem', flexWrap: 'wrap' }}>
              <div className={`${styles.timelineDot} ${dotClass(task.priority)}`} style={{ width: 52, height: 52, fontSize: '1.5rem', flexShrink: 0 }}>
                {TASK_TYPE_ICONS[task.type] || '📌'}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h1 style={{ fontSize: 'var(--font-size-xl)', fontWeight: 700, color: 'var(--color-text)', marginBottom: '0.375rem', letterSpacing: '-0.02em' }}>
                  {task.skill || task.title || 'Learning Task'}
                </h1>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
                  <PriorityBadge priority={task.priority} />
                  {task.category && (
                    <span style={{ fontSize: 'var(--font-size-xs)', background: 'var(--color-border)', color: 'var(--color-text-secondary)', padding: '2px 8px', borderRadius: 'var(--radius-full)', fontWeight: 600 }}>
                      {task.category}
                    </span>
                  )}
                  {task.type && (
                    <span style={{ fontSize: 'var(--font-size-xs)', background: 'var(--color-primary-50)', color: 'var(--color-primary)', padding: '2px 8px', borderRadius: 'var(--radius-full)', fontWeight: 600, textTransform: 'capitalize' }}>
                      {task.type.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>
              </div>

              {/* Status selector */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem', alignItems: 'flex-end' }}>
                <label style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Status
                </label>
                <select
                  value={task.status}
                  onChange={(e) => handleStatusChange(e.target.value)}
                  disabled={isUpdating}
                  id="task-status-select"
                  style={{ padding: '0.4rem 0.75rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', background: statusInfo.bg, color: statusInfo.text, fontSize: 'var(--font-size-sm)', fontWeight: 700, cursor: 'pointer', fontFamily: 'var(--font-family)' }}
                >
                  <option value="todo">Todo</option>
                  <option value="in_progress">In Progress</option>
                  <option value="done">Done</option>
                </select>
              </div>
            </div>
          </div>

          {/* Why */}
          {task.why && (
            <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.5rem', marginBottom: '1rem', animation: 'fadeInUp 0.4s ease-out both' }}>
              <div className={styles.detailLabel} style={{ marginBottom: '0.625rem' }}>Why this matters</div>
              <p className={styles.whySection}>{task.why}</p>
            </div>
          )}

          {/* Topics */}
          {task.topics?.length > 0 && (
            <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.5rem', marginBottom: '1rem', animation: 'fadeInUp 0.42s ease-out both' }}>
              <div className={styles.detailLabel} style={{ marginBottom: '0.75rem' }}>Topics to Study</div>
              <div className={styles.topicChips}>
                {task.topics.map((t) => <span key={t} className={styles.topicChip}>{t}</span>)}
              </div>
            </div>
          )}

          {/* Mini Project */}
          {task.mini_project && (
            <div className={styles.miniProjectBox} style={{ marginBottom: '1rem', animation: 'fadeInUp 0.44s ease-out both' }}>
              <strong>Hands-On Project:</strong> {task.mini_project}
            </div>
          )}

          {/* CV Evidence */}
          {task.cv_evidence && (
            <div className={styles.cvEvidenceBox} style={{ marginBottom: '1rem', animation: 'fadeInUp 0.46s ease-out both' }}>
              <strong>Add to CV Evidence:</strong> {task.cv_evidence}
            </div>
          )}

          {/* Resources */}
          {task.resources?.length > 0 && (
            <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.5rem', marginBottom: '1rem', animation: 'fadeInUp 0.48s ease-out both' }}>
              <div className={styles.detailLabel} style={{ marginBottom: '0.75rem' }}>Resources</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {task.resources.map((r, i) => (
                  <a key={i} href={r.url || r} target="_blank" rel="noopener noreferrer" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-primary)', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" /></svg>
                    {r.title || r.url || r}
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '0.5rem', animation: 'fadeInUp 0.5s ease-out both' }}>
            <Link
              href="/profile/evidence"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1.1rem', background: 'linear-gradient(135deg, #059669, #10B981)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}
              id="add-evidence-btn"
            >
              📁 Add Evidence To Profile
            </Link>
            <Link
              href="/interview/sessions/new"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1.1rem', background: 'linear-gradient(135deg, #7C3AED, #4F46E5)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}
              id="practice-interview-btn"
            >
              🎤 Practice Interview For Skill
            </Link>
            <Link
              href="/learning"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1.1rem', background: 'var(--color-card)', color: 'var(--color-text)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}
            >
              ← All Tasks
            </Link>
          </div>
        </>
      )}
    </PageShell>
  );
}
