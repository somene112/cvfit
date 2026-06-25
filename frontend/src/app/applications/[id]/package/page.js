'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ErrorBanner, { AnalysisRequiredBanner } from '@/components/common/ErrorBanner';
import EmptyStatePage from '@/components/common/EmptyStatePage';
import RiskBadge from '@/components/common/RiskBadge';
import Disclaimer from '@/components/common/Disclaimer';
import { generatePackage, getPackage } from '@/services/packageApi';
import { extractApiError, isAnalysisRequiredError } from '@/utils/errorHelpers';
import { deduplicateStrings } from '@/utils/riskHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import styles from '@/styles/Package.module.css';

export default function PackagePage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();

  const [pkg, setPkg] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState(null);
  const [analysisRequired, setAnalysisRequired] = useState(false);

  const loadPackage = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setAnalysisRequired(false);
    try {
      const data = await getPackage(id);
      setPkg(data);
    } catch (err) {
      if (err?.response?.status === 404) {
        // No package yet — that's okay
        setPkg(null);
      } else if (isAnalysisRequiredError(err)) {
        setAnalysisRequired(true);
      } else {
        const { message } = extractApiError(err, 'Không thể tải bộ hồ sơ.');
        setError(message);
      }
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (isAuthChecking) return;
    loadPackage();
  }, [isAuthChecking, loadPackage]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setAnalysisRequired(false);
    try {
      await generatePackage(id);
      trackEvent(ANALYTICS_EVENTS.PACKAGE_GENERATE_SUCCESS, { feature_name: 'package', has_analysis: true });
      await loadPackage();
    } catch (err) {
      if (isAnalysisRequiredError(err)) {
        setAnalysisRequired(true);
      } else {
        const { message } = extractApiError(err, 'Không thể tạo bộ hồ sơ. Vui lòng thử lại.');
        setError(message);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const payload = pkg?.payload_json ?? {};
  const bestCv = payload.best_cv_analysis ?? {};
  const skills = deduplicateStrings(Array.isArray(bestCv.matched_skills) ? bestCv.matched_skills : []);
  const gaps = deduplicateStrings(Array.isArray(bestCv.missing_skills) ? bestCv.missing_skills : []);
  const rubric = [];
  // Backend nests readiness fields under readiness_summary.
  const readinessSummary = payload.readiness_summary ?? {};
  const fitScore = readinessSummary.fit_score ?? null;
  const readinessLevel = readinessSummary.readiness_level ?? null;
  const packageSummary = readinessSummary.summary ?? null;
  const nextActions = Array.isArray(readinessSummary.next_actions) ? readinessSummary.next_actions : [];
  const hasReadiness = fitScore !== null || readinessLevel !== null;

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Hồ sơ ứng tuyển</Link>
        <span>›</span>
        <Link href={`/applications/${id}`} style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Chi tiết</Link>
        <span>›</span>
        <span>Bộ hồ sơ</span>
      </nav>

      <div className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Bộ hồ sơ ứng tuyển</h1>
          <p className={styles.pageSubtitle}>Bộ hồ sơ do AI tạo tóm tắt mức độ phù hợp của bạn với vị trí này.</p>
        </div>
        <button
          className={styles.generateBtn}
          onClick={handleGenerate}
          disabled={isGenerating}
          id="generate-package-btn"
        >
          {isGenerating ? (
            <><span className={styles.spinner} /> Đang tạo…</>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              {pkg ? 'Tạo lại' : 'Tạo bộ hồ sơ'}
            </>
          )}
        </button>
      </div>

      {analysisRequired && <AnalysisRequiredBanner appId={id} />}
      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading && <LoadingSpinner fullPage label="Đang tải bộ hồ sơ…" />}

      {!isLoading && !pkg && !analysisRequired && !error && (
        <EmptyStatePage
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            </svg>
          }
          title="Chưa có bộ hồ sơ"
          description="Nhấn 'Tạo bộ hồ sơ' để tạo bộ hồ sơ ứng tuyển từ AI. Cần đính kèm phân tích trước."
        />
      )}

      {!isLoading && pkg && (
        <>
          {/* Readiness summary */}
          {hasReadiness && (
            <div className={styles.readinessCard}>
              <h2 className={styles.readinessTitle}>
                📊 Đánh giá mức sẵn sàng
              </h2>
              <div className={styles.readinessGrid}>
                {fitScore != null && (
                  <div className={styles.readinessStat}>
                    <div className={styles.readinessStatValue}>{Math.round(fitScore <= 1 ? fitScore * 100 : fitScore)}%</div>
                    <div className={styles.readinessStatLabel}>Điểm phù hợp</div>
                  </div>
                )}
                {readinessLevel != null && (
                  <div className={styles.readinessStat}>
                    <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 700, color: 'var(--color-primary)', marginBottom: '0.25rem', lineHeight: 1.2 }}>
                      {readinessLevel}
                    </div>
                    <div className={styles.readinessStatLabel}>Mức sẵn sàng</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Matched skills */}
          {skills.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>✓ Kỹ năng đáp ứng</h2>
              <div className={styles.chips}>
                {skills.map((s) => (
                  <span key={s} className={styles.chip}>✓ {s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Skill gaps */}
          {gaps.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>⚠ Lỗ hổng kỹ năng</h2>
              <div className={styles.chips}>
                {gaps.map((g) => (
                  <span key={g} className={styles.chip} style={{ background: 'var(--color-warning-light)', color: '#92400E' }}>
                    ✗ {g}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Rubric */}
          {rubric.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>📋 Tiêu chí đánh giá</h2>
              <table className={styles.rubricTable}>
                <thead>
                  <tr>
                    <th>Tiêu chí</th>
                    <th>Điểm</th>
                    <th>Rủi ro</th>
                    <th>Ghi chú</th>
                  </tr>
                </thead>
                <tbody>
                  {rubric.map((item, i) => (
                    <tr key={item.id || i}>
                      <td>{item.criterion || item.name || `Item ${i + 1}`}</td>
                      <td>{item.score != null ? `${item.score}/10` : '—'}</td>
                      <td>
                        <RiskBadge score={item.risk_gap} showScore />
                      </td>
                      <td style={{ maxWidth: 260, color: 'var(--color-text-secondary)' }}>
                        {item.notes || item.feedback || '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Summary text */}
          {packageSummary && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>💬 Tóm tắt</h2>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
                {packageSummary}
              </p>
            </div>
          )}

          {/* Next actions */}
          {nextActions.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>📋 Hành động tiếp theo đề xuất</h2>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
                {nextActions.map((action, i) => (
                  <li key={i}>{typeof action === 'string' ? action : JSON.stringify(action)}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Disclaimer — always visible */}
          <div className={styles.disclaimer}>
            <Disclaimer text={payload.disclaimer} />
          </div>
        </>
      )}

      {/* Next steps */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', marginTop: '2rem', fontSize: '0.875rem' }}>
        <Link href={`/applications/${id}`} style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>← Quay lại hồ sơ</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/learning" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Mở lộ trình học tập</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/help" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Mở trợ giúp</Link>
      </div>
    </PageShell>
  );
}
