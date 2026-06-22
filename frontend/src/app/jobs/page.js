'use client';

import Link from 'next/link';
import { useState, useEffect, useMemo } from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import EmptyStatePage from '@/components/common/EmptyStatePage';
import { listTargetJobs } from '@/services/targetJobsApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import styles from '@/styles/TargetJobs.module.css';

const JOB_STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'saved', label: 'Saved' },
  { value: 'analyzing', label: 'Analyzing' },
  { value: 'ready_to_apply', label: 'Ready to Apply' },
  { value: 'interviewing', label: 'Interviewing' },
  { value: 'applied', label: 'Applied' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'offer', label: 'Offer' },
  { value: 'archived', label: 'Archived' },
];

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString();
}

function StatusBadge({ status }) {
  const cls = styles[`status--${status}`] || styles['status--saved'];
  return (
    <span className={`${styles.statusBadge} ${cls}`}>
      {status?.replace(/_/g, ' ') || 'saved'}
    </span>
  );
}

function SkeletonCard() {
  return (
    <div className={styles.skeletonCard}>
      <div className={`${styles.skeletonLine} ${styles['skeletonLine--wide']}`} />
      <div className={`${styles.skeletonLine} ${styles['skeletonLine--med']}`} />
      <div className={`${styles.skeletonLine} ${styles['skeletonLine--short']}`} style={{ marginTop: '1rem' }} />
    </div>
  );
}

export default function JobsPage() {
  const { isAuthChecking } = useRequireAuth();
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await listTargetJobs();
        if (!active) return;
        setJobs(Array.isArray(data?.items) ? data.items : []);
      } catch (err) {
        if (!active) return;
        const { message } = extractApiError(err, 'Could not load target jobs.');
        setError(message);
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking]);

  const filtered = useMemo(() => {
    return jobs.filter((j) => {
      const matchesSearch =
        !search ||
        j.job_title?.toLowerCase().includes(search.toLowerCase()) ||
        j.company?.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = !statusFilter || j.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [jobs, search, statusFilter]);

  const briefcaseIcon = (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
    </svg>
  );

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="960px">
      <div className={styles.topRow}>
        <div>
          <h1 className={styles.pageTitle}>Target Jobs</h1>
          <p className={styles.pageSubtitle}>
            Track jobs you&apos;re targeting. Each job unlocks readiness scoring, learning tasks, and interview practice.
          </p>
        </div>
        <Link href="/jobs/new" className={styles.newBtn} id="new-job-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Job
        </Link>
      </div>

      {/* Controls */}
      <div className={styles.controls}>
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Search by title or company…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          id="jobs-search"
        />
        <select
          className={styles.filterSelect}
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          id="jobs-status-filter"
        >
          {JOB_STATUSES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </select>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading && (
        <div className={styles.list}>
          {[1, 2, 3].map((k) => <SkeletonCard key={k} />)}
        </div>
      )}

      {!isLoading && !error && jobs.length === 0 && (
        <EmptyStatePage
          icon={briefcaseIcon}
          title="No target jobs yet"
          description="Add a job you're targeting to track your readiness, plan your learning, and prepare for interviews — all in one place."
          action={
            <Link href="/jobs/new" className={styles.newBtn}>
              Add your first target job
            </Link>
          }
        />
      )}

      {!isLoading && !error && jobs.length > 0 && filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
          No jobs match your current filters.{' '}
          <button
            style={{ color: 'var(--color-primary)', background: 'none', border: 'none', cursor: 'pointer', fontWeight: 600 }}
            onClick={() => { setSearch(''); setStatusFilter(''); }}
          >
            Clear filters
          </button>
        </div>
      )}

      {!isLoading && filtered.length > 0 && (
        <div className={styles.list}>
          {filtered.map((job, i) => (
            <Link
              key={job.id}
              href={`/jobs/${job.id}`}
              className={styles.card}
              id={`job-card-${job.id}`}
              style={{ animationDelay: `${i * 0.06}s` }}
            >
              <div className={styles.cardHeader}>
                <div>
                  <div className={styles.cardCompany}>{job.company || '—'}</div>
                  <div className={styles.cardRole}>{job.job_title || 'Untitled Role'}</div>
                </div>
                <StatusBadge status={job.status} />
              </div>
              <div className={styles.cardMeta}>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>Added</span>
                  <span className={styles.metaValue}>{formatDate(job.created_at)}</span>
                </div>
                {job.readiness_score != null && (
                  <div className={styles.metaItem}>
                    <span className={styles.metaLabel}>Readiness</span>
                    <span className={styles.scoreChip}>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                      </svg>
                      {job.readiness_score}%
                    </span>
                  </div>
                )}
                {job.target_role && (
                  <div className={styles.metaItem}>
                    <span className={styles.metaLabel}>Target Role</span>
                    <span className={styles.metaValue}>{job.target_role}</span>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </PageShell>
  );
}
