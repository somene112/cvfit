'use client';

import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import { useEffect } from 'react';

/**
 * Static guided Help / FAQ shell.
 *
 * Enhanced for Phase 6: adds AI Assistant CTA card at the top and preserves
 * all existing FAQs. No structural changes to FAQ content.
 */

const FAQS = [
  {
    q: 'What should I do first?',
    a: 'Start on CV Analysis. Upload your CV, paste a job description (JD), and run the analysis to get a fit score, matched/missing skills, and recommendations.',
  },
  {
    q: 'How do I analyze my CV against a job description?',
    a: 'Open CV Analysis, upload a PDF or DOCX CV, paste the JD, choose strictness and language, then start the analysis. The result appears with your fit score and skill gaps.',
  },
  {
    q: 'How do I create an application?',
    a: 'Go to Applications → New. Enter the company, role title, and the job description. Each application is a workspace for one target job.',
  },
  {
    q: 'How do I attach an analysis to an application?',
    a: 'Open the application and use "Attach analysis". Pick a recent completed analysis from the list, or paste a Job ID from your Analysis History. Attaching unlocks interview practice, cover letter, and the readiness package.',
  },
  {
    q: 'How do I use interview practice?',
    a: 'From an application with an attached analysis, open Interview. Answer each AI-generated question and review the structured rubric feedback. Your answers are saved as history.',
  },
  {
    q: 'How do I generate a cover letter or readiness package?',
    a: 'From the application, open Cover Letter or Package and click Generate. Both require an attached analysis. The cover letter is fully editable and saveable.',
  },
  {
    q: 'What analytics events are tracked?',
    a: 'Only privacy-safe product events (e.g. page navigation, login, analysis started/completed, application created, generate/save actions). We never send CV text, JD text, interview answers, cover letter text, emails, tokens, or IDs.',
  },
  {
    q: 'Why should demo data be synthetic?',
    a: 'For presentations, use synthetic CVs/JDs and a demo account only. Never present real candidate data. This protects privacy and keeps the demo reproducible.',
  },
];

export default function HelpPage() {
  const { isAuthChecking } = useRequireAuth();

  useEffect(() => {
    trackEvent(ANALYTICS_EVENTS.HELP_ASSISTANT_OPENED, { feature_name: 'help', source: 'help_page' });
  }, []);

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-text)', marginBottom: '0.5rem' }}>
        Help &amp; Guide
      </h1>
      <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6, marginBottom: '1.75rem', maxWidth: 640 }}>
        A quick guide to the AI CV Fit workflow. Follow it top to bottom:
        <strong> CV Analysis → Result → Application → Interview → Cover Letter → Package</strong>.
      </p>

      {/* Phase 6: AI Assistant CTA */}
      <div style={{ background: 'linear-gradient(135deg, #EFF6FF, #F5F3FF)', border: '1px solid #BFDBFE', borderRadius: 'var(--radius-xl)', padding: '1.5rem', marginBottom: '2rem', display: 'flex', alignItems: 'center', gap: '1.25rem', flexWrap: 'wrap', animation: 'fadeInUp 0.35s ease-out' }}>
        <div style={{ fontSize: '2.5rem', lineHeight: 1 }}>🤖</div>
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 700, color: 'var(--color-text)', marginBottom: '0.25rem' }}>
            AI Help Assistant
          </div>
          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.5, margin: 0 }}>
            Not sure what to do next? Ask the AI assistant — it reads your profile, analyses, and learning tasks to give personalised guidance.
          </p>
        </div>
        <Link
          href="/help/assistant"
          id="open-ai-assistant-btn"
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.625rem 1.25rem', background: 'linear-gradient(135deg, var(--color-primary), #4F46E5)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none', whiteSpace: 'nowrap', flexShrink: 0 }}
        >
          Open Assistant →
        </Link>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem', marginBottom: '2rem' }}>
        {FAQS.map((item, i) => (
          <div
            key={i}
            style={{ border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: '1rem 1.25rem', background: 'var(--color-surface, #fff)' }}
          >
            <div style={{ fontSize: 'var(--font-size-base)', fontWeight: 700, color: 'var(--color-text)', marginBottom: '0.375rem' }}>
              {item.q}
            </div>
            <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>
              {item.a}
            </p>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: 'var(--font-size-sm)' }}>
        <Link href="/dashboard" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>CV Analysis</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Applications</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/profile/evidence" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Evidence Vault</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/learning" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Learning</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/help/assistant" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>AI Assistant</Link>
      </div>
    </PageShell>
  );
}
