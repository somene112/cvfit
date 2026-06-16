'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import { createApplication } from '@/services/applicationsApi';
import { extractApiError } from '@/utils/errorHelpers';
import styles from '@/styles/ApplicationDetail.module.css';

const MAX_JD_CHARS = 8000;

export default function NewApplicationPage() {
  const { isAuthChecking } = useRequireAuth();
  const router = useRouter();

  const [form, setForm] = useState({
    company_name: '',
    job_title: '',
    jd_text: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!form.company_name.trim() || !form.job_title.trim()) {
      setError('Company name and role title are required.');
      return;
    }
    if (!form.jd_text.trim()) {
      setError('Job description is required.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const app = await createApplication({
        company_name: form.company_name.trim(),
        job_title: form.job_title.trim(),
        jd_text: form.jd_text.trim(),
      });
      router.push(`/applications/${app.id}`);
    } catch (err) {
      const { message, hint } = extractApiError(err, 'Failed to create application. Please try again.');
      setError(hint ? `${message} — ${hint}` : message);
      setIsSubmitting(false);
    }
  }

  const canSubmit = form.company_name.trim() && form.job_title.trim() && form.jd_text.trim() && !isSubmitting;

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="640px">
      {/* Breadcrumb */}
      <nav className={styles.breadcrumb} aria-label="Breadcrumb">
        <Link href="/applications">Applications</Link>
        <span className={styles.breadcrumbSep}>›</span>
        <span>New Application</span>
      </nav>

      <h1 className={styles.heroCompany} style={{ marginBottom: '0.5rem' }}>
        New Application
      </h1>
      <p className={styles.heroRole} style={{ marginBottom: '2rem' }}>
        Track a job you&apos;re applying for and generate AI-powered materials.
      </p>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      <div style={{ background: 'var(--color-primary-light)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '0.875rem 1rem', marginBottom: '1.75rem', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
        💡 After creating the application, go to the <strong>Overview</strong> tab to attach a CV fit analysis. This unlocks interview questions, a personalised cover letter, and a readiness package.
      </div>

      <form
        onSubmit={handleSubmit}
        style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}
        id="new-application-form"
      >
        <div>
          <label htmlFor="company_name" className={styles.infoItem}>
            <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.375rem' }}>
              Company Name <span style={{ color: 'var(--color-danger)' }}>*</span>
            </span>
          </label>
          <input
            id="company_name"
            name="company_name"
            type="text"
            required
            value={form.company_name}
            onChange={handleChange}
            disabled={isSubmitting}
            placeholder="e.g. Google, Shopify, Stripe"
            style={{ width: '100%', padding: '0.75rem 1rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: '1rem', background: 'var(--color-bg)', color: 'var(--color-text)', outline: 'none', transition: 'border-color 150ms' }}
            onFocus={(e) => { e.target.style.borderColor = 'var(--color-primary)'; }}
            onBlur={(e) => { e.target.style.borderColor = 'var(--color-border)'; }}
          />
        </div>

        <div>
          <label htmlFor="job_title">
            <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.375rem' }}>
              Role Title <span style={{ color: 'var(--color-danger)' }}>*</span>
            </span>
          </label>
          <input
            id="job_title"
            name="job_title"
            type="text"
            required
            value={form.job_title}
            onChange={handleChange}
            disabled={isSubmitting}
            placeholder="e.g. Senior Frontend Engineer"
            style={{ width: '100%', padding: '0.75rem 1rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: '1rem', background: 'var(--color-bg)', color: 'var(--color-text)', outline: 'none', transition: 'border-color 150ms' }}
            onFocus={(e) => { e.target.style.borderColor = 'var(--color-primary)'; }}
            onBlur={(e) => { e.target.style.borderColor = 'var(--color-border)'; }}
          />
        </div>

        <div>
          <label htmlFor="jd_text">
            <span style={{ display: 'block', fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.375rem' }}>
              Job Description <span style={{ color: 'var(--color-danger)' }}>*</span>
            </span>
          </label>
          <textarea
            id="jd_text"
            name="jd_text"
            value={form.jd_text}
            onChange={handleChange}
            disabled={isSubmitting}
            maxLength={MAX_JD_CHARS}
            placeholder="Paste the job description here…"
            style={{ width: '100%', minHeight: '200px', padding: '0.75rem 1rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: '0.9375rem', fontFamily: 'var(--font-family)', lineHeight: '1.6', background: 'var(--color-bg)', color: 'var(--color-text)', outline: 'none', resize: 'vertical', transition: 'border-color 150ms' }}
            onFocus={(e) => { e.target.style.borderColor = 'var(--color-primary)'; }}
            onBlur={(e) => { e.target.style.borderColor = 'var(--color-border)'; }}
          />
          <div style={{ textAlign: 'right', fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: '0.25rem' }}>
            {form.jd_text.length}/{MAX_JD_CHARS}
          </div>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', paddingTop: '0.5rem' }}>
          <Link href="/applications" className={styles.btnSecondary}>
            Cancel
          </Link>
          <button
            type="submit"
            className={styles.btnPrimary}
            disabled={!canSubmit}
            id="submit-application-btn"
          >
            {isSubmitting ? (
              <>
                <span style={{ width: 16, height: 16, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
                Creating…
              </>
            ) : 'Create Application'}
          </button>
        </div>
      </form>
    </PageShell>
  );
}
