'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import Header from '@/components/dashboard/Header';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { getJobHistory } from '@/services/jobApi';
import styles from '@/styles/History.module.css';

function formatDate(value) {
  if (!value) {
    return 'N/A';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return 'N/A';
  }
  return date.toLocaleString();
}

function formatScore(value) {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  return `${value}`;
}

function formatReport(value) {
  return value ? 'Ready' : 'Not ready';
}

export default function HistoryPage() {
  const { isAuthChecking } = useRequireAuth();
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthChecking) {
      return;
    }

    let active = true;
    setIsLoading(true);
    setError('');

    (async () => {
      try {
        const data = await getJobHistory();
        if (!active) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
      } catch {
        if (!active) return;
        setError('Could not load history. Please try again.');
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      active = false;
    };
  }, [isAuthChecking]);

  if (isAuthChecking) {
    return (
      <div className={styles.page}>
        <main className={styles.main}>
          <div className={styles.statusCard}>Checking session...</div>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Header />
      <main className={styles.main}>
        <div className={styles.topRow}>
          <div>
            <h1 className={styles.title}>Analysis History</h1>
            <p className={styles.subtitle}>Review your saved CV fit analysis jobs.</p>
          </div>
          <Link href="/dashboard" className={styles.dashboardLink}>
            New Analysis
          </Link>
        </div>

        {isLoading && <div className={styles.statusCard}>Loading history...</div>}

        {!isLoading && error && (
          <div className={styles.errorCard} role="alert">
            {error}
          </div>
        )}

        {!isLoading && !error && items.length === 0 && (
          <div className={styles.emptyCard}>No analysis jobs found yet.</div>
        )}

        {!isLoading && !error && items.length > 0 && (() => {
          // Group by target_role (or "Unknown Role")
          const grouped = items.reduce((acc, item) => {
            const role = item.target_role || 'Unknown Role';
            if (!acc[role]) acc[role] = [];
            acc[role].push(item);
            return acc;
          }, {});

          return (
            <div className={styles.groupedList}>
              {Object.entries(grouped).map(([role, roleItems]) => (
                <section key={role} className={styles.roleGroup}>
                  <h2 className={styles.roleTitle}>{role}</h2>
                  <div className={styles.list}>
                    {roleItems.map((item, index) => {
                      const prevItem = index < roleItems.length - 1 ? roleItems[index + 1] : null;
                      const canCompare = item.status === 'succeeded' && prevItem?.status === 'succeeded';
                      
                      return (
                        <article key={item.job_id} className={styles.historyItem}>
                          <div className={styles.itemHeader}>
                            <div>
                              <div className={styles.jobId}>Job {item.job_id}</div>
                            </div>
                            <span className={styles.statusBadge}>{item.status || 'unknown'}</span>
                          </div>

                          <div className={styles.metaGrid}>
                            <div className={styles.metaItem}>
                              <span className={styles.metaLabel}>Progress</span>
                              <span className={styles.metaValue}>{item.progress ?? 0}%</span>
                            </div>
                            <div className={styles.metaItem}>
                              <span className={styles.metaLabel}>Fit score</span>
                              <span className={styles.metaValue}>{formatScore(item.overall_fit_score)}</span>
                            </div>
                            <div className={styles.metaItem}>
                              <span className={styles.metaLabel}>Report</span>
                              <span className={styles.metaValue}>{formatReport(item.has_report)}</span>
                            </div>
                            <div className={styles.metaItem}>
                              <span className={styles.metaLabel}>Created</span>
                              <span className={styles.metaValue}>{formatDate(item.created_at)}</span>
                            </div>
                          </div>
                          
                          <div className={styles.actionRow}>
                            {item.status === 'succeeded' && (
                              <Link 
                                href={`/dashboard?job_id=${item.job_id}`}
                                className={styles.viewResultBtn}
                              >
                                View Result
                              </Link>
                            )}
                            {canCompare && (
                              <Link 
                                href={`/dashboard?job_id=${item.job_id}&compare_with=${prevItem.job_id}`}
                                className={styles.compareBtn}
                              >
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="16" height="16">
                                  <line x1="18" y1="20" x2="18" y2="10" />
                                  <line x1="12" y1="20" x2="12" y2="4" />
                                  <line x1="6" y1="20" x2="6" y2="14" />
                                </svg>
                                Compare with Previous
                              </Link>
                            )}
                          </div>
                        </article>
                      );
                    })}
                  </div>
                </section>
              ))}
            </div>
          );
        })()}
      </main>
    </div>
  );
}
