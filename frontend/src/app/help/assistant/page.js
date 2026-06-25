'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { getSuggestions, askAssistant } from '@/services/helpApi';
import { listApplications } from '@/services/applicationsApi';
import { listTargetJobs } from '@/services/targetJobsApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';

// Recommended product actions → Vietnamese label + destination.
const ACTION_META = {
  open_learning: { label: 'Mở lộ trình học tập', href: () => '/learning' },
  start_interview: { label: 'Luyện phỏng vấn', href: () => '/interview/sessions/new' },
  view_readiness: { label: 'Xem mức sẵn sàng', href: (c) => (c.application_id ? `/applications/${c.application_id}` : '/applications') },
  open_package: { label: 'Mở bộ hồ sơ', href: (c) => (c.application_id ? `/applications/${c.application_id}/package` : '/applications') },
  update_target_job: { label: 'Cập nhật việc làm mục tiêu', href: (c) => (c.target_job_id ? `/jobs/${c.target_job_id}` : '/jobs') },
  review_gap: { label: 'Xem lỗ hổng kỹ năng', href: (c) => (c.application_id ? `/applications/${c.application_id}` : '/applications') },
  attach_analysis: { label: 'Đính kèm phân tích', href: (c) => (c.application_id ? `/applications/${c.application_id}` : '/applications') },
  open_help: { label: 'Mở trợ giúp', href: () => '/help' },
};

export default function HelpAssistantPage() {
  const { isAuthChecking } = useRequireAuth();

  const [suggestions, setSuggestions] = useState([]);
  const [suggestionsLimitations, setSuggestionsLimitations] = useState('');
  const [loadingSuggestions, setLoadingSuggestions] = useState(true);

  const [contextType, setContextType] = useState('');
  const [contextOptions, setContextOptions] = useState({ jobs: [], applications: [] });
  const [selectedContextId, setSelectedContextId] = useState('');

  const [activeIntent, setActiveIntent] = useState(null);
  const [isAsking, setIsAsking] = useState(false);
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState(null);

  // Load suggestions + context options.
  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    trackEvent(ANALYTICS_EVENTS.HELP_ASSISTANT_OPENED, { feature_name: 'help' });

    (async () => {
      setLoadingSuggestions(true);
      try {
        const data = await getSuggestions('vi');
        if (!active) return;
        setSuggestions(data?.suggestions || []);
        setSuggestionsLimitations(data?.limitations || '');
      } catch (err) {
        if (!active) return;
        const { message } = extractApiError(err, 'Không thể tải gợi ý.');
        setError(message);
      } finally {
        if (active) setLoadingSuggestions(false);
      }
    })();

    Promise.allSettled([listTargetJobs(), listApplications()]).then(([jobs, apps]) => {
      if (!active) return;
      setContextOptions({
        jobs: jobs.status === 'fulfilled' ? (jobs.value?.items || []) : [],
        applications: apps.status === 'fulfilled' ? (apps.value?.items || []) : [],
      });
    });

    return () => { active = false; };
  }, [isAuthChecking]);

  const buildContext = () => {
    const ctx = {};
    if (contextType === 'job' && selectedContextId) ctx.target_job_id = selectedContextId;
    if (contextType === 'application' && selectedContextId) ctx.application_id = selectedContextId;
    return ctx;
  };

  const handleAsk = async (intent) => {
    setActiveIntent(intent);
    setIsAsking(true);
    setError(null);
    setAnswer(null);
    const context = buildContext();
    try {
      const result = await askAssistant({ intent, context, language: 'vi' });
      setAnswer({ ...result, _context: context });
      trackEvent(ANALYTICS_EVENTS.HELP_ASSISTANT_PROMPT_CLICKED, { feature_name: 'help', prompt_chip: intent });
    } catch (err) {
      const { message } = extractApiError(err, 'Không thể nhận câu trả lời lúc này. Vui lòng thử lại.');
      setError(message);
    } finally {
      setIsAsking(false);
    }
  };

  const answerContext = answer?._context || {};

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="760px">
      {/* Breadcrumb */}
      <nav style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: '1.5rem' }} aria-label="Breadcrumb">
        <Link href="/help" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Trợ giúp</Link>
        <span>›</span>
        <span>Trợ lý AI</span>
      </nav>

      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.025em', marginBottom: '0.375rem' }}>
          Trợ lý Trợ giúp AI
        </h1>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6, maxWidth: 560 }}>
          Chọn một câu hỏi gợi ý. Trợ lý dùng dữ liệu của riêng bạn (việc làm mục tiêu, phân tích, nhiệm vụ học tập, phiên phỏng vấn) làm ngữ cảnh. Không gửi nội dung CV/JD/câu trả lời.
        </p>
      </div>

      {/* Optional context selector */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        <select
          value={contextType}
          onChange={(e) => { setContextType(e.target.value); setSelectedContextId(''); }}
          style={{ padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', cursor: 'pointer' }}
          id="context-type-select"
        >
          <option value="">Không có ngữ cảnh cụ thể</option>
          <option value="job">Việc làm mục tiêu</option>
          <option value="application">Hồ sơ ứng tuyển</option>
        </select>

        {contextType === 'job' && contextOptions.jobs.length > 0 && (
          <select value={selectedContextId} onChange={(e) => setSelectedContextId(e.target.value)}
            style={{ flex: 1, minWidth: 180, padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', cursor: 'pointer' }}
            id="context-job-select">
            <option value="">Chọn việc làm…</option>
            {contextOptions.jobs.map((j) => <option key={j.id} value={j.id}>{j.company || j.company_name} — {j.job_title}</option>)}
          </select>
        )}
        {contextType === 'application' && contextOptions.applications.length > 0 && (
          <select value={selectedContextId} onChange={(e) => setSelectedContextId(e.target.value)}
            style={{ flex: 1, minWidth: 180, padding: '0.5rem 0.75rem', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', fontSize: 'var(--font-size-sm)', background: 'var(--color-bg)', color: 'var(--color-text)', cursor: 'pointer' }}
            id="context-application-select">
            <option value="">Chọn hồ sơ ứng tuyển…</option>
            {contextOptions.applications.map((a) => <option key={a.id} value={a.id}>{a.company_name} — {a.job_title}</option>)}
          </select>
        )}
      </div>

      {/* Suggestion chips */}
      {loadingSuggestions ? (
        <LoadingSpinner label="Đang tải gợi ý…" />
      ) : (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem' }}>
          {suggestions.map((s) => (
            <button
              key={s.intent}
              type="button"
              onClick={() => handleAsk(s.intent)}
              disabled={isAsking}
              id={`suggestion-${s.intent}`}
              style={{
                padding: '0.5rem 0.875rem',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-full)',
                background: activeIntent === s.intent ? 'var(--color-primary-light)' : 'var(--color-card)',
                color: activeIntent === s.intent ? 'var(--color-primary)' : 'var(--color-text-secondary)',
                fontSize: 'var(--font-size-sm)', fontWeight: 600, cursor: isAsking ? 'default' : 'pointer',
                fontFamily: 'var(--font-family)', opacity: isAsking && activeIntent !== s.intent ? 0.6 : 1,
              }}
            >
              {s.label}
            </button>
          ))}
        </div>
      )}

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}
      {isAsking && <LoadingSpinner label="Đang suy nghĩ…" />}

      {/* Answer card */}
      {answer && !isAsking && (
        <div style={{ background: 'linear-gradient(135deg, #EFF6FF, #F5F3FF 60%, white)', border: '1px solid #BFDBFE', borderRadius: 'var(--radius-xl)', padding: '1.75rem', marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <span style={{ fontSize: '1.25rem' }}>🤖</span>
            <span style={{ fontWeight: 700, color: 'var(--color-primary)', fontSize: 'var(--font-size-base)' }}>Trợ lý trả lời</span>
            {answer.fallback_used && (
              <span style={{ marginLeft: 'auto', padding: '2px 8px', background: '#FEF3C7', color: '#B45309', borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', fontWeight: 700 }}>
                Chưa đủ dữ liệu
              </span>
            )}
          </div>

          <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text)', lineHeight: 1.75, marginBottom: '1rem', whiteSpace: 'pre-wrap' }}>
            {answer.answer}
          </p>

          {Array.isArray(answer.based_on) && answer.based_on.length > 0 && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255,255,255,0.7)', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: '0.375rem' }}>Dựa trên</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
                {answer.based_on.map((ref, i) => (
                  <span key={i} style={{ padding: '2px 8px', background: 'var(--color-primary-light)', color: 'var(--color-primary)', borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>{ref}</span>
                ))}
              </div>
            </div>
          )}

          {answer.limitations && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'rgba(255, 243, 199, 0.6)', border: '1px solid #FDE68A', borderRadius: 'var(--radius-md)' }}>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#B45309', marginBottom: '0.375rem' }}>⚠ Giới hạn</div>
              <p style={{ fontSize: 'var(--font-size-xs)', color: '#92400E', lineHeight: 1.5, margin: 0 }}>{answer.limitations}</p>
            </div>
          )}

          {Array.isArray(answer.recommended_actions) && answer.recommended_actions.length > 0 && (
            <div>
              <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: '0.625rem' }}>Hành động đề xuất</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {answer.recommended_actions.map((key) => {
                  const meta = ACTION_META[key];
                  if (!meta) return null;
                  return (
                    <Link key={key} href={meta.href(answerContext)}
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', padding: '0.5rem 0.875rem', background: 'var(--color-primary)', color: 'white', borderRadius: 'var(--radius-md)', fontWeight: 600, fontSize: 'var(--font-size-sm)', textDecoration: 'none' }}>
                      → {meta.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}

      {!answer && !isAsking && !error && !loadingSuggestions && (
        <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>💬</div>
          <p>Chọn một câu hỏi gợi ý ở trên để nhận hướng dẫn từ trợ lý.</p>
          {suggestionsLimitations && <p style={{ fontSize: 'var(--font-size-xs)', marginTop: '0.5rem', maxWidth: 460, marginInline: 'auto' }}>{suggestionsLimitations}</p>}
        </div>
      )}

      {/* Nav links */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: 'var(--font-size-sm)', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
        <Link href="/help" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>← Hướng dẫn sử dụng</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/learning" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Lộ trình học tập</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/interview/sessions" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Luyện phỏng vấn</Link>
      </div>
    </PageShell>
  );
}
