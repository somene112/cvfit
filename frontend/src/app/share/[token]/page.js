'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { getPublicShare } from '@/services/shareApi';
import styles from '@/styles/Share.module.css';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';

/**
 * Public Shareable Readiness page at /share/[token]
 *
 * This page is unauthenticated — it shows only safe, curated information.
 * NEVER exposes: tokens, IDs, raw CV text, raw JD text, private data.
 */
export default function PublicSharePage() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await getPublicShare(token);
      setData(result);
      trackEvent(ANALYTICS_EVENTS.SHARE_LINK_OPENED, {
        feature_name: 'share',
        status: 'success',
      });
    } catch (err) {
      const status = err?.response?.status;
      if (status === 404) {
        setError('not_found');
      } else if (status === 410) {
        setError('expired');
      } else if (status === 403) {
        setError('revoked');
      } else {
        setError('error');
      }
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (isLoading) {
    return (
      <div className={styles.publicPage}>
        <div className={styles.publicContainer}>
          <div style={{ textAlign: 'center', paddingTop: '4rem' }}>
            <div style={{ width: 48, height: 48, border: '3px solid #BFDBFE', borderTopColor: 'var(--color-primary)', borderRadius: '50%', animation: 'spin 0.7s linear infinite', margin: '0 auto 1rem' }} />
            <p style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>Loading readiness profile…</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    const errorInfo = {
      not_found: { icon: '🔍', title: 'Share Link Not Found', desc: 'This readiness profile link doesn\'t exist or has never been shared.' },
      expired: { icon: '⏰', title: 'Link Has Expired', desc: 'This share link has expired. Ask the owner to generate a new one.' },
      revoked: { icon: '🔒', title: 'Access Revoked', desc: 'The owner has revoked access to this profile.' },
      error: { icon: '⚠️', title: 'Something Went Wrong', desc: 'We couldn\'t load this profile right now. Please try again later.' },
    };
    const info = errorInfo[error] || errorInfo.error;

    return (
      <div className={styles.publicPage}>
        <div className={styles.publicContainer}>
          <div className={styles.expiredCard}>
            <div className={styles.expiredIcon}>{info.icon}</div>
            <div className={styles.expiredTitle}>{info.title}</div>
            <p className={styles.expiredDesc}>{info.desc}</p>
            <Link
              href="/"
              style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1.25rem', background: 'var(--color-primary)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}
            >
              Go to AI CV Fit
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className={styles.publicPage}>
      <div className={styles.publicContainer}>

        {/* Brand Header */}
        <div className={styles.publicHeader}>
          <Link href="/" className={styles.publicBrand}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            AI CV Fit
          </Link>

          {data.candidate_name && (
            <div className={styles.publicName}>{data.candidate_name}</div>
          )}
          {data.target_role && (
            <div className={styles.publicRole}>{data.target_role}</div>
          )}
          {data.company && (
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
              Applying to {data.company}
            </div>
          )}
        </div>

        {/* Score Card */}
        {data.readiness_score != null && (
          <div className={styles.scoreCard}>
            <div className={styles.scoreValue}>{data.readiness_score}%</div>
            <div className={styles.scoreLabel}>Job Readiness Score</div>
            <div style={{ marginTop: '1rem', height: 10, background: '#E0E7FF', borderRadius: 'var(--radius-full)', overflow: 'hidden', maxWidth: 300, margin: '1rem auto 0' }}>
              <div style={{ height: '100%', width: `${data.readiness_score}%`, background: 'linear-gradient(90deg, var(--color-primary), #8B5CF6)', borderRadius: 'var(--radius-full)', transition: 'width 1.2s ease-out' }} />
            </div>
            {data.score_summary && (
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginTop: '0.875rem', lineHeight: 1.6, maxWidth: 440, margin: '0.875rem auto 0' }}>
                {data.score_summary}
              </p>
            )}
          </div>
        )}

        {/* Score Breakdown */}
        {data.score_breakdown && Object.keys(data.score_breakdown).length > 0 && (
          <div className={styles.publicSection} style={{ animationDelay: '0.1s' }}>
            <div className={styles.sectionTitle}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
              </svg>
              Score Breakdown
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: '0.75rem' }}>
              {Object.entries(data.score_breakdown).map(([key, val]) => (
                <div key={key} style={{ padding: '0.75rem', background: 'var(--color-bg)', borderRadius: 'var(--radius-md)' }}>
                  <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)', marginBottom: '0.375rem' }}>
                    {key.replace(/_/g, ' ')}
                  </div>
                  <div style={{ fontSize: 'var(--font-size-xl)', fontWeight: 800, color: 'var(--color-primary)', letterSpacing: '-0.03em' }}>
                    {val}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Selected Evidence */}
        {data.evidence?.length > 0 && (
          <div className={styles.publicSection} style={{ animationDelay: '0.15s' }}>
            <div className={styles.sectionTitle}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              Highlights &amp; Evidence
            </div>
            <div className={styles.evidenceList}>
              {data.evidence.map((item, i) => (
                <div key={i} className={styles.evidenceItem}>
                  <div className={styles.evidenceTitle}>{item.title}</div>
                  {item.description && (
                    <div className={styles.evidenceDesc}>{item.description}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Package Summary */}
        {data.package_summary && (
          <div className={styles.publicSection} style={{ animationDelay: '0.2s' }}>
            <div className={styles.sectionTitle}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              </svg>
              Package Summary
            </div>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
              {data.package_summary}
            </p>
          </div>
        )}

        {/* Footer */}
        <div className={styles.publicFooter}>
          <p>
            Powered by{' '}
            <Link href="/">AI CV Fit</Link>
            {' '}· This is a candidate-shared readiness profile. Private data, raw CV, and raw JD are not included.
          </p>
        </div>
      </div>
    </div>
  );
}
