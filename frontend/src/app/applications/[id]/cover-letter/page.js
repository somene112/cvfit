'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ErrorBanner, { AnalysisRequiredBanner } from '@/components/common/ErrorBanner';
import Disclaimer from '@/components/common/Disclaimer';
import { generateCoverLetter, getCoverLetter, updateCoverLetter } from '@/services/coverLetterApi';
import { extractApiError, isAnalysisRequiredError } from '@/utils/errorHelpers';
import styles from '@/styles/CoverLetter.module.css';

function extractSections(letter) {
  const p = letter?.payload_json ?? {};
  return {
    opening: p.opening ?? '',
    why_role_company: p.why_role_company ?? '',
    contribution_fit: p.contribution_fit ?? '',
    closing: p.closing ?? '',
  };
}

export default function CoverLetterPage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();

  const [letter, setLetter] = useState(null);
  const [sections, setSections] = useState({ opening: '', why_role_company: '', contribution_fit: '', closing: '' });
  const [isLoading, setIsLoading] = useState(true);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState(null);
  const [analysisRequired, setAnalysisRequired] = useState(false);
  const [saved, setSaved] = useState(false);

  const loadLetter = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    setAnalysisRequired(false);
    try {
      const data = await getCoverLetter(id);
      setLetter(data);
      setSections(extractSections(data));
    } catch (err) {
      if (err?.response?.status === 404) {
        setLetter(null);
      } else if (isAnalysisRequiredError(err)) {
        setAnalysisRequired(true);
      } else {
        const { message } = extractApiError(err, 'Could not load cover letter.');
        setError(message);
      }
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (isAuthChecking) return;
    loadLetter();
  }, [isAuthChecking, loadLetter]);

  const handleGenerate = async () => {
    setIsGenerating(true);
    setError(null);
    setAnalysisRequired(false);
    try {
      await generateCoverLetter(id);
      await loadLetter();
      setSaved(false);
    } catch (err) {
      if (isAnalysisRequiredError(err)) {
        setAnalysisRequired(true);
      } else {
        const { message } = extractApiError(err, 'Failed to generate cover letter.');
        setError(message);
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const original = useMemo(() => extractSections(letter), [letter]);

  const isDirty = letter && JSON.stringify(sections) !== JSON.stringify(original);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      const patch = {};
      if (sections.opening !== original.opening) patch.opening = sections.opening;
      if (sections.why_role_company !== original.why_role_company) patch.why_role_company = sections.why_role_company;
      if (sections.contribution_fit !== original.contribution_fit) patch.contribution_fit = sections.contribution_fit;
      if (sections.closing !== original.closing) patch.closing = sections.closing;
      if (Object.keys(patch).length === 0) return;
      const data = await updateCoverLetter(id, patch);
      setLetter(data);
      setSections(extractSections(data));
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to save cover letter.');
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const payload = letter?.payload_json ?? {};
  const disclaimer = payload.disclaimer ?? null;
  const missingEvidence = Array.isArray(payload.missing_evidence) ? payload.missing_evidence : [];
  const reviewNotes = Array.isArray(payload.review_notes) ? payload.review_notes : [];

  const sectionFields = [
    { key: 'opening', label: 'Opening' },
    { key: 'why_role_company', label: 'Why This Role & Company' },
    { key: 'contribution_fit', label: 'Contribution & Fit' },
    { key: 'closing', label: 'Closing' },
  ];

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--color-text-muted)', marginBottom: '1.5rem' }}>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Applications</Link>
        <span>›</span>
        <Link href={`/applications/${id}`} style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Application</Link>
        <span>›</span>
        <span>Cover Letter</span>
      </nav>

      <div className={styles.header}>
        <div>
          <h1 className={styles.pageTitle}>Cover Letter</h1>
          <p className={styles.pageSubtitle}>AI-generated, fully editable cover letter for this application.</p>
        </div>
        <button
          className={styles.generateBtn}
          onClick={handleGenerate}
          disabled={isGenerating || isLoading}
          id="generate-cover-letter-btn"
        >
          {isGenerating ? (
            <><span className={styles.spinner} /> Generating…</>
          ) : (
            <>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              {letter ? 'Regenerate' : 'Generate Cover Letter'}
            </>
          )}
        </button>
      </div>

      {analysisRequired && <AnalysisRequiredBanner appId={id} />}
      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading && <LoadingSpinner fullPage label="Loading cover letter…" />}

      {!isLoading && !letter && !analysisRequired && !error && (
        <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--color-text-secondary)' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>✉️</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '0.5rem' }}>No cover letter yet</h2>
          <p style={{ fontSize: '0.9375rem', maxWidth: 380, margin: '0 auto' }}>
            Click &apos;Generate Cover Letter&apos; to create an AI-powered draft. An analysis must be attached to this application first.
          </p>
        </div>
      )}

      {!isLoading && letter && (
        <>
          <div className={styles.editorCard}>
            <div className={styles.editorToolbar}>
              <span className={styles.editorLabel}>Edit each section below</span>
            </div>

            {sectionFields.map(({ key, label }) => (
              <div key={key} style={{ marginBottom: '1.25rem' }}>
                <label
                  htmlFor={`cl-section-${key}`}
                  style={{ display: 'block', fontSize: '0.75rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.375rem' }}
                >
                  {label}
                </label>
                <textarea
                  id={`cl-section-${key}`}
                  className={styles.textarea}
                  value={sections[key]}
                  onChange={(e) => { setSections((prev) => ({ ...prev, [key]: e.target.value })); setSaved(false); }}
                  disabled={isSaving}
                  style={{ minHeight: '100px' }}
                  aria-label={label}
                />
              </div>
            ))}

            <div className={styles.editorFooter}>
              {saved && (
                <span className={styles.savedIndicator}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  Saved
                </span>
              )}
              <button
                className={styles.saveBtn}
                onClick={handleSave}
                disabled={isSaving || !isDirty}
                id="save-cover-letter-btn"
              >
                {isSaving ? (
                  <>
                    <span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
                    Saving…
                  </>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z" />
                      <polyline points="17 21 17 13 7 13 7 21" />
                      <polyline points="7 3 7 8 15 8" />
                    </svg>
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </div>

          {missingEvidence.length > 0 && (
            <div style={{ marginTop: '1.5rem', background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
              <p style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
                Missing Evidence
              </p>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
                {missingEvidence.map((item, i) => <li key={i}>{typeof item === 'string' ? item : JSON.stringify(item)}</li>)}
              </ul>
            </div>
          )}

          {reviewNotes.length > 0 && (
            <div style={{ marginTop: '1rem', background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '1.25rem' }}>
              <p style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>
                Review Notes
              </p>
              <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.7 }}>
                {reviewNotes.map((note, i) => <li key={i}>{typeof note === 'string' ? note : JSON.stringify(note)}</li>)}
              </ul>
            </div>
          )}

          {/* Disclaimer — always visible */}
          <div className={styles.disclaimer}>
            <Disclaimer text={disclaimer} />
          </div>
        </>
      )}
    </PageShell>
  );
}
