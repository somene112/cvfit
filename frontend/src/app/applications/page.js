'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import EmptyStatePage from '@/components/common/EmptyStatePage';
import { listApplications } from '@/services/applicationsApi';
import { extractApiError } from '@/utils/errorHelpers';
import styles from '@/styles/Applications.module.css';

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString();
}

function StatusBadge({ status }) {
  const cls =
    status === 'active'
      ? styles['statusBadge--active']
      : status === 'archived'
        ? styles['statusBadge--archived']
        : styles['statusBadge--draft'];
  return (
    <span className={`${styles.statusBadge} ${cls}`}>
      {status || 'draft'}
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

export default function ApplicationsPage() {
  const { isAuthChecking } = useRequireAuth();
  const [apps, setApps] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await listApplications();
        if (!active) return;
        setApps(Array.isArray(data?.items) ? data.items : []);
      } catch (err) {
        if (!active) return;
        const { message } = extractApiError(err, 'Could not load applications.');
        setError(message);
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking]);

  const folderIcon = (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      <div className={styles.topRow}>
        <div>
          <h1 className={styles.pageTitle}>Applications</h1>
          <p className={styles.pageSubtitle}>Track your job applications and AI-generated materials.</p>
        </div>
        <Link href="/applications/new" className={styles.newBtn} id="new-application-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Application
        </Link>
      </div>

      {error && (
        <ErrorBanner
          message={error}
          onDismiss={() => setError(null)}
        />
      )}

      {isLoading && (
        <div className={styles.list}>
          {[1, 2, 3].map((k) => <SkeletonCard key={k} />)}
        </div>
      )}

      {!isLoading && !error && apps.length === 0 && (
        <EmptyStatePage
          icon={folderIcon}
          title="No applications yet"
          description="Start tracking your job applications and generate AI-powered packages, cover letters, and interview prep."
          action={
            <Link href="/applications/new" className={styles.newBtn}>
              Create your first application
            </Link>
          }
        />
      )}

      {!isLoading && apps.length > 0 && (
        <div className={styles.list}>
          {apps.map((app, i) => (
            <Link
              key={app.id}
              href={`/applications/${app.id}`}
              className={styles.card}
              id={`application-card-${app.id}`}
              style={{ animationDelay: `${i * 0.06}s` }}
            >
              <div className={styles.cardHeader}>
                <div>
                  <div className={styles.cardCompany}>{app.company_name || '—'}</div>
                  <div className={styles.cardRole}>{app.role_title || 'Untitled Role'}</div>
                </div>
                <StatusBadge status={app.status} />
              </div>
              <div className={styles.cardMeta}>
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>Applied</span>
                  <span className={styles.metaValue}>{formatDate(app.created_at)}</span>
                </div>
                {app.overall_fit_score != null && (
                  <div className={styles.metaItem}>
                    <span className={styles.metaLabel}>Fit Score</span>
                    <span className={styles.scoreChip}>{app.overall_fit_score}%</span>
                  </div>
                )}
                <div className={styles.metaItem}>
                  <span className={styles.metaLabel}>Analysis</span>
                  <span className={styles.metaValue}>
                    {app.analysis_attached ? '✓ Attached' : 'Not attached'}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </PageShell>
  );
}
