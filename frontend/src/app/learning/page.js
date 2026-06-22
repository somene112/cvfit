'use client';

import Link from 'next/link';
import { useState, useEffect, useMemo } from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import EmptyStatePage from '@/components/common/EmptyStatePage';
import { getLearningRoadmap, updateLearningTask } from '@/services/learningApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import styles from '@/styles/LearningRoadmap.module.css';
import appStyles from '@/styles/Applications.module.css';

const PRIORITY_ORDER = { high: 0, medium: 1, low: 2 };

const TASK_TYPE_ICONS = {
  article: '📖',
  project: '🛠',
  practice: '🎯',
  interview_prep: '🎤',
  profile_evidence: '📁',
};

const CATEGORY_COLORS = [
  'var(--color-primary)',
  '#7C3AED',
  '#059669',
  '#D97706',
  '#DC2626',
  '#0891B2',
];

function PriorityBadge({ priority }) {
  const cls =
    priority === 'high' ? styles.priorityHigh :
    priority === 'medium' ? styles.priorityMedium :
    styles.priorityLow;
  return <span className={`${styles.priorityBadge} ${cls}`}>{priority}</span>;
}

function StatusChip({ status, onChange, taskId, disabled }) {
  const colors = {
    todo: { bg: 'var(--color-border)', text: 'var(--color-text-secondary)' },
    in_progress: { bg: 'var(--color-warning-light)', text: '#B45309' },
    done: { bg: 'var(--color-success-light)', text: '#065F46' },
  };
  const c = colors[status] || colors.todo;
  return (
    <select
      value={status}
      onChange={(e) => onChange(taskId, e.target.value)}
      disabled={disabled}
      style={{
        padding: '3px 8px',
        borderRadius: 'var(--radius-full)',
        border: 'none',
        background: c.bg,
        color: c.text,
        fontSize: '0.7rem',
        fontWeight: 700,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        cursor: 'pointer',
        fontFamily: 'var(--font-family)',
      }}
    >
      <option value="todo">Todo</option>
      <option value="in_progress">In Progress</option>
      <option value="done">Done</option>
    </select>
  );
}

function SkeletonTask() {
  return (
    <div className={styles.roadmapCard}>
      <div className={styles.timelineDot} style={{ background: 'var(--color-border)' }} />
      <div className={styles.cardContent}>
        <div className={appStyles.skeletonLine} style={{ width: '50%', height: 14, marginBottom: 8 }} />
        <div className={appStyles.skeletonLine} style={{ width: '80%', height: 11 }} />
        <div className={appStyles.skeletonLine} style={{ width: '35%', height: 11, marginTop: 8 }} />
      </div>
    </div>
  );
}

export default function LearningPage() {
  const { isAuthChecking } = useRequireAuth();
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('');

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await getLearningRoadmap();
        if (!active) return;
        setTasks(Array.isArray(data?.items) ? data.items : []);
      } catch (err) {
        if (!active) return;
        const { message } = extractApiError(err, 'Could not load your learning roadmap.');
        setError(message);
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking]);

  const categories = useMemo(() => {
    const cats = [...new Set(tasks.map((t) => t.category).filter(Boolean))];
    return cats;
  }, [tasks]);

  const filtered = useMemo(() => {
    const list = categoryFilter
      ? tasks.filter((t) => t.category === categoryFilter)
      : tasks;
    return [...list].sort((a, b) => (PRIORITY_ORDER[a.priority] ?? 99) - (PRIORITY_ORDER[b.priority] ?? 99));
  }, [tasks, categoryFilter]);

  const handleStatusChange = async (taskId, newStatus) => {
    setUpdatingId(taskId);
    try {
      const updated = await updateLearningTask(taskId, { status: newStatus });
      setTasks((prev) => prev.map((t) => (t.id === taskId ? { ...t, ...updated } : t)));
      if (newStatus === 'in_progress') {
        trackEvent(ANALYTICS_EVENTS.LEARNING_TASK_STARTED, { feature_name: 'learning', task_type: tasks.find((t) => t.id === taskId)?.type });
      } else if (newStatus === 'done') {
        trackEvent(ANALYTICS_EVENTS.LEARNING_TASK_COMPLETED, { feature_name: 'learning', task_type: tasks.find((t) => t.id === taskId)?.type });
      }
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to update task status.');
      setError(message);
    } finally {
      setUpdatingId(null);
    }
  };

  const dotClass = (priority) =>
    priority === 'high' ? styles.dotHigh : priority === 'medium' ? styles.dotMedium : styles.dotLow;

  const bookIcon = (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  );

  const stats = {
    total: tasks.length,
    done: tasks.filter((t) => t.status === 'done').length,
    inProgress: tasks.filter((t) => t.status === 'in_progress').length,
    high: tasks.filter((t) => t.priority === 'high').length,
  };

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="900px">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap', animation: 'fadeInUp 0.35s ease-out' }}>
        <div>
          <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.025em', marginBottom: '0.25rem' }}>
            Learning Roadmap
          </h1>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6, maxWidth: 560 }}>
            Your personalised upskilling path based on your CV analysis. Tackle high-priority tasks first to close skill gaps.
          </p>
        </div>
        <Link
          href="/interview/sessions/new"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1rem', background: 'var(--color-primary)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}
        >
          Practice Interview
        </Link>
      </div>

      {/* Stats strip */}
      {!isLoading && tasks.length > 0 && (
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.5rem', animation: 'fadeIn 0.4s ease-out' }}>
          {[
            { label: 'Total Tasks', value: stats.total, color: 'var(--color-primary)' },
            { label: 'Done', value: stats.done, color: 'var(--color-success)' },
            { label: 'In Progress', value: stats.inProgress, color: '#F59E0B' },
            { label: 'High Priority', value: stats.high, color: 'var(--color-danger)' },
          ].map((s) => (
            <div key={s.label} style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '0.625rem 1rem', minWidth: 100 }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: s.color, lineHeight: 1, letterSpacing: '-0.04em' }}>{s.value}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: 2, fontWeight: 600 }}>{s.label}</div>
            </div>
          ))}

          {/* Progress bar */}
          {stats.total > 0 && (
            <div style={{ flex: 1, minWidth: 200, background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '0.625rem 1rem', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.375rem', fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                <span>Overall Progress</span>
                <span>{Math.round((stats.done / stats.total) * 100)}%</span>
              </div>
              <div style={{ height: 8, background: 'var(--color-border)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${(stats.done / stats.total) * 100}%`, background: 'linear-gradient(90deg, var(--color-primary), var(--color-success))', borderRadius: 'var(--radius-full)', transition: 'width 0.8s ease-out' }} />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Category Filter */}
      {!isLoading && categories.length > 1 && (
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.25rem' }}>
          <button
            onClick={() => setCategoryFilter('')}
            style={{ padding: '0.3rem 0.75rem', borderRadius: 'var(--radius-full)', border: '1px solid', borderColor: !categoryFilter ? 'var(--color-primary)' : 'var(--color-border)', background: !categoryFilter ? 'var(--color-primary-light)' : 'var(--color-card)', color: !categoryFilter ? 'var(--color-primary)' : 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)', fontWeight: 600, cursor: 'pointer' }}
          >
            All Categories
          </button>
          {categories.map((cat, i) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat === categoryFilter ? '' : cat)}
              style={{ padding: '0.3rem 0.75rem', borderRadius: 'var(--radius-full)', border: '1px solid', borderColor: categoryFilter === cat ? CATEGORY_COLORS[i % CATEGORY_COLORS.length] : 'var(--color-border)', background: categoryFilter === cat ? `${CATEGORY_COLORS[i % CATEGORY_COLORS.length]}18` : 'var(--color-card)', color: categoryFilter === cat ? CATEGORY_COLORS[i % CATEGORY_COLORS.length] : 'var(--color-text-secondary)', fontSize: 'var(--font-size-xs)', fontWeight: 600, cursor: 'pointer' }}
            >
              {cat}
            </button>
          ))}
        </div>
      )}

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading && (
        <div className={styles.roadmapContainer}>
          {[1, 2, 3, 4].map((k) => <SkeletonTask key={k} />)}
        </div>
      )}

      {!isLoading && tasks.length === 0 && !error && (
        <EmptyStatePage
          icon={bookIcon}
          title="No learning tasks yet"
          description="Run a CV vs JD analysis to get a personalised roadmap of skills to learn and evidence to build."
          action={
            <Link href="/dashboard" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1.25rem', background: 'linear-gradient(135deg, var(--color-primary), #4F46E5)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}>
              Run CV Analysis →
            </Link>
          }
        />
      )}

      {!isLoading && filtered.length > 0 && (
        <div className={styles.roadmapContainer}>
          {filtered.map((task, i) => (
            <div key={task.id} className={styles.roadmapCard} style={{ animationDelay: `${i * 0.05}s` }}>
              {/* Timeline dot */}
              <div className={`${styles.timelineDot} ${dotClass(task.priority)}`}>
                <span style={{ fontSize: '0.8rem' }}>{TASK_TYPE_ICONS[task.type] || '📌'}</span>
              </div>

              <div className={styles.cardContent}>
                <div className={styles.cardHeader}>
                  <Link href={`/learning/${task.id}`} className={styles.skillName} style={{ textDecoration: 'none', color: 'inherit' }}>
                    {task.skill || task.title || 'Learning Task'}
                  </Link>
                  <PriorityBadge priority={task.priority} />
                  {task.category && (
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', background: 'var(--color-border)', padding: '2px 8px', borderRadius: 'var(--radius-full)' }}>
                      {task.category}
                    </span>
                  )}
                  <StatusChip
                    status={task.status}
                    onChange={handleStatusChange}
                    taskId={task.id}
                    disabled={updatingId === task.id}
                  />
                </div>

                {task.why && (
                  <div className={styles.whySection}>{task.why}</div>
                )}

                {task.topics?.length > 0 && (
                  <div className={styles.detailBlock}>
                    <div className={styles.detailLabel}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="9 11 12 14 22 4" />
                        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                      </svg>
                      Topics
                    </div>
                    <div className={styles.topicChips}>
                      {task.topics.map((topic) => (
                        <span key={topic} className={styles.topicChip}>{topic}</span>
                      ))}
                    </div>
                  </div>
                )}

                {task.mini_project && (
                  <div className={styles.miniProjectBox}>
                    <strong>Mini Project:</strong> {task.mini_project}
                  </div>
                )}

                {task.cv_evidence && (
                  <div className={styles.cvEvidenceBox}>
                    <strong>Add to Evidence:</strong> {task.cv_evidence}
                  </div>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.25rem' }}>
                  <Link
                    href={`/learning/${task.id}`}
                    style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-primary)', textDecoration: 'none' }}
                  >
                    View Details →
                  </Link>
                  <span style={{ color: 'var(--color-text-muted)' }}>·</span>
                  <Link
                    href="/profile/evidence"
                    style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textDecoration: 'none' }}
                  >
                    Add Evidence
                  </Link>
                  <span style={{ color: 'var(--color-text-muted)' }}>·</span>
                  <Link
                    href="/interview/sessions/new"
                    style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: 'var(--color-text-secondary)', textDecoration: 'none' }}
                  >
                    Practice Interview
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Footer links — preserved from Phase 5 */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: 'var(--font-size-sm)', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
        <Link href="/dashboard" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>← CV Analysis</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Applications</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/profile/evidence" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Evidence Vault</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/help" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Help</Link>
      </div>
    </PageShell>
  );
}
