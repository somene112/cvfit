'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { getApplication, attachAnalysis } from '@/services/applicationsApi';
import { extractApiError } from '@/utils/errorHelpers';
import styles from '@/styles/ApplicationDetail.module.css';

function formatDate(value) {
  if (!value) return '—';
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? '—' : d.toLocaleDateString();
}

function getInitial(name) {
  return (name || '?').charAt(0).toUpperCase();
}

export default function ApplicationDetailPage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();
  const router = useRouter();

  const [app, setApp] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Attach analysis state
  const [attachJobId, setAttachJobId] = useState('');
  const [isAttaching, setIsAttaching] = useState(false);
  const [attachError, setAttachError] = useState(null);
  const [attachSuccess, setAttachSuccess] = useState(false);

  const loadApp = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getApplication(id);
      setApp(data);
    } catch (err) {
      const { message } = extractApiError(err, 'Could not load application details.');
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (isAuthChecking) return;
    loadApp();
  }, [isAuthChecking, loadApp]);

  const handleAttach = async (e) => {
    e.preventDefault();
    if (!attachJobId.trim()) {
      setAttachError('Please enter a Job ID.');
      return;
    }
    setIsAttaching(true);
    setAttachError(null);
    setAttachSuccess(false);
    try {
      await attachAnalysis(id, attachJobId.trim());
      setAttachSuccess(true);
      setAttachJobId('');
      // Reload the application to reflect attached analysis
      await loadApp();
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to attach analysis.');
      setAttachError(message);
    } finally {
      setIsAttaching(false);
    }
  };

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      {/* Breadcrumb */}
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/applications">Applications</Link>
        <span className={styles.breadcrumbSep}>›</span>
        <span>{app ? `${app.company_name} — ${app.job_title}` : 'Loading…'}</span>
      </nav>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading && <LoadingSpinner fullPage label="Loading application…" />}

      {!isLoading && app && (
        <>
          {/* Hero */}
          <div className={styles.heroCard}>
            <div className={styles.heroTop}>
              <div className={styles.companyLogo} aria-hidden="true">
                {getInitial(app.company_name)}
              </div>
              <div className={styles.heroInfo}>
                <h1 className={styles.heroCompany}>{app.company_name || 'Unknown Company'}</h1>
                <p className={styles.heroRole}>{app.job_title || 'Untitled Role'}</p>
              </div>
              <div className={styles.heroActions}>
                <Link
                  href={`/applications/${id}/package`}
                  className={styles.btnPrimary}
                  id="go-to-package-btn"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                  </svg>
                  Package
                </Link>
                <Link
                  href={`/applications/${id}/cover-letter`}
                  className={styles.btnSecondary}
                  id="go-to-cover-letter-btn"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                    <polyline points="22,6 12,13 2,6" />
                  </svg>
                  Cover Letter
                </Link>
                <Link
                  href={`/applications/${id}/interview`}
                  className={styles.btnSecondary}
                  id="go-to-interview-btn"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                  </svg>
                  Interview
                </Link>
              </div>
            </div>

            <div className={styles.infoGrid}>
              <div className={styles.infoItem}>
                <label>Status</label>
                <span>{app.status || 'draft'}</span>
              </div>
              <div className={styles.infoItem}>
                <label>Created</label>
                <span>{formatDate(app.created_at)}</span>
              </div>
              <div className={styles.infoItem}>
                <label>Analysis</label>
                <span>{app.best_analysis_job_id ? '✓ Attached' : 'Not attached'}</span>
              </div>
            </div>
          </div>

          {/* Sub-navigation tabs */}
          <nav className={styles.tabs} aria-label="Application sections">
            <Link href={`/applications/${id}`} className={`${styles.tab} ${styles.active}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="16" />
                <line x1="8" y1="12" x2="16" y2="12" />
              </svg>
              Overview
            </Link>
            <Link href={`/applications/${id}/package`} className={styles.tab}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              </svg>
              Package
            </Link>
            <Link href={`/applications/${id}/cover-letter`} className={styles.tab}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
              Cover Letter
            </Link>
            <Link href={`/applications/${id}/interview`} className={styles.tab}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              Interview
            </Link>
          </nav>

          {/* Analysis attachment section */}
          <div className={styles.analysisCard}>
            <div className={styles.analysisHeader}>
              <h2 className={styles.analysisTitle}>
                🔗 Attached Analysis
              </h2>
              {app.best_analysis_job_id && (
                <span className={styles.attachedBadge}>
                  ✓ Analysis attached
                </span>
              )}
            </div>

            {app.best_analysis_job_id ? (
              <>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
                  Phân tích đã được đính kèm. Bạn có thể tạo package, cover letter và luyện tập phỏng vấn ngay bây giờ.
                  <span style={{ display: 'block', marginTop: '0.5rem', color: 'var(--color-text-muted)' }}>
                    Job ID: <code style={{ background: 'var(--color-bg)', padding: '2px 6px', borderRadius: 4, fontSize: '0.8125rem' }}>{app.best_analysis_job_id}</code>
                  </span>
                </p>

                {/* Feature Links */}
                <div className={styles.featureLinksSection}>
                  <div className={styles.featureLinksTitle}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                    </svg>
                    Các tính năng AI có sẵn
                  </div>
                  <div className={styles.featureLinksGrid}>
                    {/* Interview */}
                    <Link
                      href={`/applications/${id}/interview`}
                      className={`${styles.featureLinkCard} ${styles.interview}`}
                      id="feature-link-interview"
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                          width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                          background: 'linear-gradient(135deg, #F5F3FF, #EDE9FE)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#7C3AED'
                        }}>
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                          </svg>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: 3 }}>AI Interview</div>
                          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--color-text)' }}>Luyện phỏng vấn</div>
                        </div>
                      </div>
                      <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
                        Thực hành trả lời câu hỏi phỏng vấn AI tạo riêng cho vị trí này
                      </p>
                      <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: '#7C3AED', display: 'flex', alignItems: 'center', gap: 4 }}>
                        Bắt đầu luyện tập
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                      </span>
                    </Link>

                    {/* Cover Letter */}
                    <Link
                      href={`/applications/${id}/cover-letter`}
                      className={`${styles.featureLinkCard} ${styles.letter}`}
                      id="feature-link-cover-letter"
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                          width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                          background: 'linear-gradient(135deg, #ECFDF5, #D1FAE5)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#059669'
                        }}>
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                            <polyline points="22,6 12,13 2,6" />
                          </svg>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: 3 }}>AI Writing</div>
                          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--color-text)' }}>Tạo Cover Letter</div>
                        </div>
                      </div>
                      <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
                        Thư xin việc được cá nhân hoá theo kết quả phân tích CV & JD
                      </p>
                      <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: '#059669', display: 'flex', alignItems: 'center', gap: 4 }}>
                        Tạo ngay
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                      </span>
                    </Link>

                    {/* Package */}
                    <Link
                      href={`/applications/${id}/package`}
                      className={`${styles.featureLinkCard} ${styles.packageLink}`}
                      id="feature-link-package"
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                          width: 40, height: 40, borderRadius: 10, flexShrink: 0,
                          background: 'linear-gradient(135deg, #FFF7ED, #FFEDD5)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#D97706'
                        }}>
                          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
                            <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
                            <line x1="12" y1="22.08" x2="12" y2="12" />
                          </svg>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: 3 }}>Full Package</div>
                          <div style={{ fontSize: 'var(--font-size-sm)', fontWeight: 700, color: 'var(--color-text)' }}>Application Package</div>
                        </div>
                      </div>
                      <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
                        Bộ hồ sơ hoàn chỉnh gồm CV tối ưu, cover letter và câu hỏi phỏng vấn
                      </p>
                      <span style={{ fontSize: 'var(--font-size-xs)', fontWeight: 600, color: '#D97706', display: 'flex', alignItems: 'center', gap: 4 }}>
                        Xem package
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
                      </span>
                    </Link>
                  </div>
                </div>
              </>
            ) : (
              <>
                <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: '1rem', lineHeight: 1.6 }}>
                  Attach a CV fit analysis to unlock Package, Cover Letter, and Interview generation. Run an analysis from the Dashboard first, then paste the Job ID here.
                </p>
                {attachError && (
                  <ErrorBanner message={attachError} onDismiss={() => setAttachError(null)} />
                )}
                {attachSuccess && (
                  <div style={{ color: 'var(--color-success)', fontSize: 'var(--font-size-sm)', fontWeight: 600, marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
                    ✓ Analysis attached successfully.
                  </div>
                )}
                <form onSubmit={handleAttach} className={styles.attachForm}>
                  <input
                    type="text"
                    className={styles.attachInput}
                    value={attachJobId}
                    onChange={(e) => setAttachJobId(e.target.value)}
                    placeholder="Paste Job ID from Dashboard analysis…"
                    disabled={isAttaching}
                    id="attach-job-id-input"
                  />
                  <button
                    type="submit"
                    className={`${styles.btnPrimary} ${styles.btnSm}`}
                    disabled={isAttaching || !attachJobId.trim()}
                    id="attach-analysis-btn"
                  >
                    {isAttaching ? 'Attaching…' : 'Attach'}
                  </button>
                </form>
              </>
            )}
          </div>

          {/* Job description preview */}
          {app.jd_text && (
            <div className={styles.analysisCard} style={{ marginTop: '1.5rem' }}>
              <h2 className={styles.analysisTitle} style={{ marginBottom: '1rem' }}>📄 Job Description</h2>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.8, whiteSpace: 'pre-wrap', maxHeight: '300px', overflow: 'auto' }}>
                {app.jd_text}
              </p>
            </div>
          )}
        </>
      )}
    </PageShell>
  );
}
