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
        const { message } = extractApiError(err, 'Could not load package.');
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
      await loadPackage();
    } catch (err) {
      if (isAnalysisRequiredError(err)) {
        setAnalysisRequired(true);
      } else {
        const { message } = extractApiError(err, 'Failed to generate package. Please try again.');
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
  const readiness = payload.readiness_summary ?? null;

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Applications</Link>
        <span>›</span>
        <Link href={`/applications/${id}`} style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Application</Link>
        <span>›</span>
        <span>Package</span>
      </nav>

      <div className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Application Package</h1>
          <p className={styles.pageSubtitle}>AI-generated package summarising your fit for this role.</p>
        </div>
        <button
          className={styles.generateBtn}
          onClick={handleGenerate}
          disabled={isGenerating}
          id="generate-package-btn"
        >
          {isGenerating ? (
            <><span className={styles.spinner} /> Generating…</>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              {pkg ? 'Regenerate' : 'Generate Package'}
            </>
          )}
        </button>
      </div>

      {analysisRequired && <AnalysisRequiredBanner appId={id} />}
      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading && <LoadingSpinner fullPage label="Loading package…" />}

      {!isLoading && !pkg && !analysisRequired && !error && (
        <EmptyStatePage
          icon={
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
            </svg>
          }
          title="No package yet"
          description="Click 'Generate Package' to create an AI-powered application package for this role. An analysis must be attached first."
        />
      )}

      {!isLoading && pkg && (
        <>
          {/* Readiness summary */}
          {readiness && (
            <div className={styles.readinessCard}>
              <h2 className={styles.readinessTitle}>
                📊 Readiness Summary
              </h2>
              <div className={styles.readinessGrid}>
                {readiness.overall_score != null && (
                  <div className={styles.readinessStat}>
                    <div className={styles.readinessStatValue}>{readiness.overall_score}%</div>
                    <div className={styles.readinessStatLabel}>Overall Fit</div>
                  </div>
                )}
                {readiness.skill_match != null && (
                  <div className={styles.readinessStat}>
                    <div className={styles.readinessStatValue}>{readiness.skill_match}%</div>
                    <div className={styles.readinessStatLabel}>Skill Match</div>
                  </div>
                )}
                {readiness.experience_match != null && (
                  <div className={styles.readinessStat}>
                    <div className={styles.readinessStatValue}>{readiness.experience_match}%</div>
                    <div className={styles.readinessStatLabel}>Experience</div>
                  </div>
                )}
                {readiness.risk_level != null && (
                  <div className={styles.readinessStat}>
                    <div style={{ marginBottom: '0.375rem' }}>
                      <RiskBadge score={readiness.risk_level} />
                    </div>
                    <div className={styles.readinessStatLabel}>Risk Level</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Matched skills */}
          {skills.length > 0 && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>✓ Matched Skills</h2>
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
              <h2 className={styles.sectionTitle}>⚠ Skill Gaps</h2>
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
              <h2 className={styles.sectionTitle}>📋 Evaluation Rubric</h2>
              <table className={styles.rubricTable}>
                <thead>
                  <tr>
                    <th>Criterion</th>
                    <th>Score</th>
                    <th>Risk</th>
                    <th>Notes</th>
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
          {readiness?.summary && (
            <div className={styles.section}>
              <h2 className={styles.sectionTitle}>💬 Summary</h2>
              <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.8 }}>
                {readiness.summary}
              </p>
            </div>
          )}

          {/* Disclaimer — always visible */}
          <div className={styles.disclaimer}>
            <Disclaimer text={payload.disclaimer} />
          </div>
        </>
      )}
    </PageShell>
  );
}
