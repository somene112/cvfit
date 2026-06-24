'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { getAdminMe, getAdminOverview, getAdminRecentActivity } from '@/services/adminApi';
import { extractApiError } from '@/utils/errorHelpers';

function formatVnd(amount) {
  const value = Number(amount || 0);
  try {
    return `${new Intl.NumberFormat('vi-VN').format(value)} ₫`;
  } catch {
    return `${value} ₫`;
  }
}

function StatCard({ icon, label, value, sublabel }) {
  return (
    <div
      style={{
        background: 'var(--color-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-xl)',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '1.25rem' }}>{icon}</span>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
          {label}
        </span>
      </div>
      <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.03em' }}>
        {value}
      </div>
      {sublabel && (
        <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{sublabel}</div>
      )}
    </div>
  );
}

function FlagBadge({ label, enabled }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', padding: '0.625rem 0.875rem', background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
      <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>{label}</span>
      <span
        style={{
          padding: '2px 10px',
          borderRadius: 'var(--radius-full)',
          fontSize: 'var(--font-size-xs)',
          fontWeight: 700,
          background: enabled ? '#D1FAE5' : '#F1F5F9',
          color: enabled ? '#065F46' : '#64748B',
        }}
      >
        {enabled ? 'Bật' : 'Tắt'}
      </span>
    </div>
  );
}

function Breakdown({ title, data }) {
  const entries = Object.entries(data || {});
  if (entries.length === 0) return null;
  return (
    <div style={{ marginTop: '0.75rem' }}>
      <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>
        {title}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.375rem' }}>
        {entries.map(([key, count]) => (
          <span key={key} style={{ padding: '2px 8px', background: 'var(--color-primary-light)', color: 'var(--color-primary)', borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', fontWeight: 600 }}>
            {key}: {count}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function AdminPage() {
  const { isAuthChecking } = useRequireAuth();

  const [isLoading, setIsLoading] = useState(true);
  const [forbidden, setForbidden] = useState(false);
  const [error, setError] = useState(null);
  const [overview, setOverview] = useState(null);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;

    (async () => {
      setIsLoading(true);
      setError(null);
      setForbidden(false);
      try {
        await getAdminMe();
        const [ov, activity] = await Promise.allSettled([
          getAdminOverview(),
          getAdminRecentActivity(20),
        ]);
        if (!active) return;
        if (ov.status === 'fulfilled') setOverview(ov.value);
        if (activity.status === 'fulfilled') setRecent(activity.value?.items || []);
      } catch (err) {
        if (!active) return;
        if (err?.response?.status === 403) {
          setForbidden(true);
        } else {
          const { message } = extractApiError(err, 'Không thể tải bảng quản trị.');
          setError(message);
        }
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking]);

  const users = overview?.users || {};
  const jobs = overview?.analysis_jobs || {};
  const applications = overview?.applications || {};
  const interviews = overview?.interviews || {};
  const billing = overview?.billing || {};
  const usage = overview?.usage || {};
  const flags = overview?.flags || {};

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="1080px">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.025em', marginBottom: '0.375rem' }}>
          Bảng quản trị
        </h1>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          Theo dõi trạng thái hệ thống ở mức tổng quan. Chỉ hiển thị số liệu tổng hợp — không có nội dung riêng tư của người dùng.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullPage label="Đang tải bảng quản trị…" />}

      {!isLoading && forbidden && (
        <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--color-text-secondary)' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔒</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '0.5rem' }}>
            Không có quyền truy cập
          </h2>
          <p>Bạn không có quyền truy cập trang quản trị.</p>
          <Link href="/dashboard" style={{ color: 'var(--color-primary)', textDecoration: 'none', display: 'inline-block', marginTop: '1rem' }}>
            ← Về trang phân tích CV
          </Link>
        </div>
      )}

      {!isLoading && !forbidden && error && (
        <ErrorBanner message={error} onDismiss={() => setError(null)} />
      )}

      {!isLoading && !forbidden && overview && (
        <>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
              gap: '1rem',
              marginBottom: '1.5rem',
            }}
          >
            <StatCard icon="👥" label="Tổng người dùng" value={users.total_users ?? 0}
                      sublabel={`Đang hoạt động: ${users.active_users ?? 0} · Đã xác thực: ${users.verified_users ?? 0}`} />
            <StatCard icon="📊" label="Tổng lượt phân tích CV" value={jobs.analysis_jobs_total ?? 0} />
            <StatCard icon="🗂️" label="Hồ sơ ứng tuyển" value={applications.applications_total ?? 0}
                      sublabel={`Việc làm mục tiêu: ${applications.target_jobs_total ?? 0}`} />
            <StatCard icon="🎤" label="Phiên phỏng vấn" value={interviews.interview_sessions_total ?? 0} />
            <StatCard icon="🧾" label="Đơn thanh toán" value={billing.billing_orders_total ?? 0}
                      sublabel={`Đã thanh toán: ${billing.paid_orders_total ?? 0}`} />
            <StatCard icon="💰" label="Doanh thu đã xác nhận" value={formatVnd(billing.paid_revenue_vnd)} />
            <StatCard icon="🔎" label="Đơn cần kiểm tra" value={billing.manual_review_orders_total ?? 0}
                      sublabel={`Gói quyền lợi: ${billing.user_entitlements_total ?? 0}`} />
            <StatCard icon="⚡" label="Sự kiện sử dụng" value={usage.usage_events_total ?? 0} />
          </div>

          {/* Breakdowns */}
          <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.5rem' }}>
            <Breakdown title="Phân tích theo trạng thái" data={jobs.analysis_jobs_by_status} />
            <Breakdown title="Đơn thanh toán theo trạng thái" data={billing.billing_orders_by_status} />
            <Breakdown title="Sự kiện sử dụng theo loại" data={usage.usage_events_by_type} />
          </div>

          {/* Feature flags */}
          <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 700, color: 'var(--color-text)', marginBottom: '0.875rem' }}>
              Trạng thái tính năng
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
              <FlagBadge label="Thanh toán (Billing)" enabled={!!flags.ENABLE_BILLING} />
              <FlagBadge label="Giới hạn theo lượt (Credit gating)" enabled={!!flags.ENABLE_CREDIT_GATING} />
              <FlagBadge label="Liên kết chia sẻ (Share links)" enabled={!!flags.ENABLE_PHASE6_SHARE_LINKS} />
            </div>
          </div>

          {/* Recent activity */}
          {recent.length > 0 && (
            <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 700, color: 'var(--color-text)', marginBottom: '0.875rem' }}>
                Hoạt động gần đây
              </h2>
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                  <thead>
                    <tr style={{ textAlign: 'left', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      <th style={{ padding: '0.5rem 0.5rem 0.5rem 0' }}>Loại</th>
                      <th style={{ padding: '0.5rem' }}>Nguồn</th>
                      <th style={{ padding: '0.5rem' }}>Người dùng (ẩn danh)</th>
                      <th style={{ padding: '0.5rem' }}>Thời gian</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recent.map((item, i) => (
                      <tr key={i} style={{ borderTop: '1px solid var(--color-border)' }}>
                        <td style={{ padding: '0.5rem 0.5rem 0.5rem 0', color: 'var(--color-text)' }}>{item.type}</td>
                        <td style={{ padding: '0.5rem', color: 'var(--color-text-secondary)' }}>{item.status}</td>
                        <td style={{ padding: '0.5rem', color: 'var(--color-text-muted)', fontFamily: 'monospace' }}>{item.user_ref}</td>
                        <td style={{ padding: '0.5rem', color: 'var(--color-text-muted)' }}>
                          {item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Meta */}
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
            {overview.expected_alembic_head && <span>Phiên bản schema (alembic head): {overview.expected_alembic_head}</span>}
            {overview.generated_at && <span>Cập nhật lúc: {new Date(overview.generated_at).toLocaleString('vi-VN')}</span>}
          </div>
        </>
      )}
    </PageShell>
  );
}
