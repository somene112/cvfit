'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import { askAssistant } from '@/services/helpApi';
import { listApplications } from '@/services/applicationsApi';
import { listTargetJobs } from '@/services/targetJobsApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';

const PROMPT_CHIPS = [
  { id: 'next', label: '🎯 What should I do next?' },
  { id: 'score', label: '📊 Why is my score low?' },
  { id: 'learn', label: '📚 What should I learn first?' },
  { id: 'prep', label: '🎤 How should I prepare for interview?' },
];

const ACTION_ICONS = {
  learning_task: '📚',
  interview_session: '🎤',
  comparison: '📊',
  package: '📦',
};

export default function HelpAssistantPage() {
  const { isAuthChecking } = useRequireAuth();

  const [prompt, setPrompt] = useState('');
  const [contextType, setContextType] = useState('');
  const [contextOptions, setContextOptions] = useState({ jobs: [], applications: [] });
  const [selectedContextId, setSelectedContextId] = useState('');

  const [isLoading, setIsLoading] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState(null);

  // Load context options (target jobs and applications)
  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    Promise.allSettled([listTargetJobs(), listApplications()]).then(([jobs, apps]) => {
      if (!active) return;
      setContextOptions({
        jobs: jobs.status === 'fulfilled' ? (jobs.value?.items || []) : [],
        applications: apps.status === 'fulfilled' ? (apps.value?.items || []) : [],
      });
    });
    return () => { active = false; };
  }, [isAuthChecking]);

  useEffect(() => {
    trackEvent(ANALYTICS_EVENTS.HELP_ASSISTANT_OPENED, { feature_name: 'help' });
  }, []);

  const handleChipClick = (chip) => {
    setPrompt(chip.label.replace(/^[^\w]+/, ''));
    trackEvent(ANALYTICS_EVENTS.HELP_ASSISTANT_PROMPT_CLICKED, {
      feature_name: 'help',
      prompt_chip: chip.id,
    });
  };

  const handleAsk = async (e) => {
    e?.preventDefault();
    if (!prompt.trim()) return;
    setIsLoading(true);
    setError(null);
    setAnswer(null);

    const context = {};
    if (contextType === 'job' && selectedContextId) context.target_job_id = selectedContextId;
    if (contextType === 'application' && selectedContextId) context.application_id = selectedContextId;

    try {
      const result = await askAssistant({ prompt: prompt.trim(), context });
      setAnswer(result);
    } catch (err) {
      const { message } = extractApiError(err, 'Could not get an answer right now. Please try again.');
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const actionHref = (action) => {
    if (!action?.type) return '#';
    if (action.href) return action.href;
    if (action.type === 'learning_task') return '/learning';
    if (action.type === 'interview_session') return '/interview/sessions/new';
    if (action.type === 'comparison') return '/dashboard';
    if (action.type === 'package' && action.application_id) return `/applications/${action.application_id}/package`;
    return '#';
  };

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="760px">
      {/* Header */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: '1.5rem', animation: 'fadeInDown 0.3s ease-out' }} aria-label="Breadcrumb">
        <Link href="/help" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Help</Link>
        <span>›</span>
        <span>AI Assistant</span>
      </nav>

      <div style={{ marginBottom: '1.75rem', animation: 'fadeInUp 0.35s ease-out' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.025em', marginBottom: '0.375rem' }}>
          AI Help Assistant
        </h1>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6, maxWidth: 560 }}>
          Ask a question about your job search progress. The assistant uses your CV analyses, applications, and learning tasks as context.
        </p>
      </div>

      {/* Prompt Chips */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem', animation: 'fadeIn 0.4s ease-out' }}>
        {PROMPT_CHIPS.map((chip) => (
          <button
            key={chip.id}
            type="button"
            onClick={() => handleChipClick(chip)}
            id={`prompt-chip-${chip.id}`}
            style={{
              padding: '0.5rem 0.875rem',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-full)',
              background: prompt.includes(chip.label.replace(/^[^\w]+/, '')) ? 'var(--color-primary-light)' : 'var(--color-card)',
              color: prompt.includes(chip.label.replace(/^[^\w]+/, '')) ? 'var(--color-primary)' : 'var(--color-text-secondary)',
              fontSize: 'var(--font-size-sm)',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
              fontFamily: 'var(--font-family)',
            }}
          >
            {chip.label}
          </button>
        ))}
      </div>

      {/* Ask Form */}
      <form onSubmit={handleAsk} style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.5rem', marginBottom: '1.5rem', animation: 'fadeInUp 0.4s ease-out' }}>
        {/* Context Selector */}
        <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
          <select
            value={contextType}
            onChange={(e) => { setContextType(e.target.value); setSelectedContextId(''); }}
            style={{ padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', outline: 'none', cursor: 'pointer' }}
            id="context-type-select"
          >
            <option value="">No specific context</option>
            <option value="job">Target Job</option>
            <option value="application">Application</option>
          </select>

          {contextType === 'job' && contextOptions.jobs.length > 0 && (
            <select
              value={selectedContextId}
              onChange={(e) => setSelectedContextId(e.target.value)}
              style={{ flex: 1, padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', outline: 'none', cursor: 'pointer' }}
              id="context-job-select"
            >
              <option value="">Select a job…</option>
              {contextOptions.jobs.map((j) => (
                <option key={j.id} value={j.id}>{j.company} — {j.job_title}</option>
              ))}
            </select>
          )}

          {contextType === 'application' && contextOptions.applications.length > 0 && (
            <select
              value={selectedContextId}
              onChange={(e) => setSelectedContextId(e.target.value)}
              style={{ flex: 1, padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', outline: 'none', cursor: 'pointer' }}
              id="context-application-select"
            >
              <option value="">Select an application…</option>
              {contextOptions.applications.map((a) => (
                <option key={a.id} value={a.id}>{a.company_name} — {a.job_title}</option>
              ))}
            </select>
          )}
        </div>

        {/* Prompt Input */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Ask a question… e.g. What skills should I focus on this week?"
          rows={3}
          style={{ width: '100%', padding: '0.75rem 1rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', fontFamily: 'var(--font-family)', lineHeight: 1.6, background: 'var(--color-bg)', color: 'var(--color-text)', outline: 'none', resize: 'vertical', transition: 'border-color var(--transition-fast)', marginBottom: '0.75rem' }}
          onFocus={(e) => { e.target.style.borderColor = 'var(--color-primary)'; }}
          onBlur={(e) => { e.target.style.borderColor = 'var(--color-border)'; }}
          id="assistant-prompt-input"
        />

        {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1.25rem', background: 'linear-gradient(135deg, var(--color-primary), #4F46E5)', color: 'white', border: 'none', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', cursor: 'pointer', transition: 'all var(--transition-fast)', opacity: (!prompt.trim() || isLoading) ? 0.6 : 1, fontFamily: 'var(--font-family)' }}
            id="ask-assistant-btn"
          >
            {isLoading ? (
              <>
                <span style={{ width: 14, height: 14, border: '2px solid rgba(255,255,255,0.3)', borderTopColor: 'white', borderRadius: '50%', animation: 'spin 0.7s linear infinite', display: 'inline-block' }} />
                Thinking…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
                Ask
              </>
            )}
          </button>
        </div>
      </form>

      {/* Answer Card */}
      {answer && (
        <div style={{ background: 'linear-gradient(135deg, #EFF6FF, #F5F3FF 60%, white)', border: '1px solid #BFDBFE', borderRadius: 'var(--radius-xl)', padding: '1.75rem', animation: 'scaleIn 0.35s ease-out', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <span style={{ fontSize: '1.25rem' }}>🤖</span>
            <span style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: 'var(--font-size-base)' }}>Assistant Answer</span>
          </div>

          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text)', lineHeight: 1.75, marginBottom: '1rem', whiteSpace: 'pre-wrap' }}>
            {answer.answer}
          </p>

          {/* Based On */}
          {answer.based_on?.length > 0 && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.7)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: '0.375rem' }}>
                Based On
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                {answer.based_on.map((ref, i) => (
                  <span key={i} style={{ padding: '2px 8px', background: 'var(--color-primary-light)', color: 'var(--color-primary)', borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>
                    {ref}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Limitations */}
          {answer.limitations?.length > 0 && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255, 243, 199, 0.6)', border: '1px solid #FDE68A', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#B45309', marginBottom: '0.375rem' }}>
                ⚠ Limitations
              </div>
              <ul style={{ listStyle: 'disc', paddingLeft: '1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {answer.limitations.map((l, i) => (
                  <li key={i} style={{ fontSize: 'var(--font-size-xs)', color: '#92400E', lineHeight: 1.5 }}>{l}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Action Buttons */}
          {answer.actions?.length > 0 && (
            <div>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: '0.625rem' }}>
                Suggested Actions
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {answer.actions.map((action, i) => (
                  <Link
                    key={i}
                    href={actionHref(action)}
                    style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.5rem 0.875rem', background: 'var(--color-primary)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}
                  >
                    {ACTION_ICONS[action.type] || '→'} {action.label}
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Empty / Fallback */}
      {!answer && !isLoading && !error && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)', animation: 'fadeIn 0.4s ease-out' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>💬</div>
          <p>Select a prompt chip or type your own question to get AI-powered guidance.</p>
        </div>
      )}

      {/* Nav links */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: 'var(--font-size-sm)', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
        <Link href="/help" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>← Help Guide</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/learning" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Learning Roadmap</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/interview/sessions" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Interview Practice</Link>
      </div>
    </PageShell>
  );
}
