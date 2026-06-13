'use client';

import { useState, useEffect, useCallback } from 'react';
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

export default function CoverLetterPage() {
  const { isAuthChecking } = useRequireAuth();
  const { id } = useParams();

  const [letter, setLetter] = useState(null);
  const [editedText, setEditedText] = useState('');
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
      setEditedText(data?.text || '');
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
      const data = await generateCoverLetter(id);
      setLetter(data);
      setEditedText(data?.text || '');
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

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      const data = await updateCoverLetter(id, editedText);
      setLetter(data);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to save cover letter.');
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const isDirty = letter && editedText !== (letter.text || '');

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
              <span className={styles.editorLabel}>Edit your cover letter below</span>
              <span className={styles.charCount}>{editedText.length} characters</span>
            </div>
            <textarea
              className={styles.textarea}
              value={editedText}
              onChange={(e) => { setEditedText(e.target.value); setSaved(false); }}
              disabled={isSaving}
              id="cover-letter-editor"
              aria-label="Cover letter text"
            />
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

          {/* Disclaimer — always visible */}
          <div className={styles.disclaimer}>
            <Disclaimer text={letter.disclaimer} />
          </div>
        </>
      )}
    </PageShell>
  );
}
