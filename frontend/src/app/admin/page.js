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

// Percentages/averages are null when their denominator is zero — show a dash,
// never a misleading 0.
const fmtPct = (v) => (v === null || v === undefined ? '—' : `${v}%`);
const fmtNum = (v) => (v === null || v === undefined ? '—' : v);
const fmtDateTime = (iso) => {
  if (!iso) return 'Chưa có dữ liệu';
  const d = new Date(iso);
  return isNaN(d.getTime()) ? 'Chưa có dữ liệu' : d.toLocaleString('vi-VN');
};

function Section({ title, children, subtitle }) {
  return (
    <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.25rem', marginBottom: '1.5rem' }}>
      <h2 style={{ fontSize: 'var(--font-size-base)', fontWeight: 700, color: 'var(--color-text)', marginBottom: subtitle ? '0.25rem' : '0.875rem' }}>
        {title}
      </h2>
      {subtitle && (
        <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: '0.875rem' }}>{subtitle}</p>
      )}
      {children}
    </div>
  );
}

function StatCard({ icon, label, value, sublabel }) {
  return (
    <div style={{ background: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-xl)', padding: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontSize: '1.25rem' }}>{icon}</span>
        <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>{label}</span>
      </div>
      <div style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 800, color: 'var(--color-text)', letterSpacing: '-0.03em' }}>{value}</div>
      {sublabel && <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>{sublabel}</div>}
    </div>
  );
}

function FunnelStep({ label, count, pct, isFirst }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.25rem' }}>
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>{label}</span>
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text)', fontWeight: 700 }}>
            {fmtNum(count)}{!isFirst && pct !== null && pct !== undefined ? ` · ${pct}%` : ''}
          </span>
        </div>
        <div style={{ height: 8, background: 'var(--color-bg)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${isFirst ? 100 : Math.min(100, Number(pct) || 0)}%`, background: 'linear-gradient(90deg, var(--color-primary), #4F46E5)', borderRadius: 'var(--radius-full)' }} />
        </div>
      </div>
    </div>
  );
}

function FlagBadge({ label, enabled }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.75rem', padding: '0.625rem 0.875rem', background: 'var(--color-bg)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
      <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', fontWeight: 600 }}>{label}</span>
      <span style={{ padding: '2px 10px', borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', fontWeight: 700, background: enabled ? '#D1FAE5' : '#F1F5F9', color: enabled ? '#065F46' : '#64748B' }}>
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
      <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--color-text-muted)', marginBottom: '0.5rem' }}>{title}</div>
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

const CARD_GRID = { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '1rem' };

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

  const jobs = overview?.analysis_jobs || {};
  const billing = overview?.billing || {};
  const usage = overview?.usage || {};
  const flags = overview?.flags || {};
  const funnel = overview?.product_funnel || {};
  const conversion = overview?.conversion_rates || {};
  const timeline = overview?.activity_timeline || {};
  const health = overview?.analysis_health || {};
  const depth = overview?.engagement_depth || {};
  const billingReadiness = overview?.billing_readiness || {};
  const w7 = timeline.last_7_days || {};
  const w30 = timeline.last_30_days || {};

  const activityRows = [
    ['Người dùng mới', 'new_users'],
    ['Phân tích CV', 'analysis_jobs_created'],
    ['Hồ sơ ứng tuyển', 'applications_created'],
    ['Phiên phỏng vấn', 'interview_sessions_created'],
  ];

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="1080px">
      <div style={{ marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: 'var(--font-size-2xl)', fontWeight: 700, color: 'var(--color-text)', letterSpacing: '-0.025em', marginBottom: '0.375rem' }}>
          Bảng quản trị
        </h1>
        <p style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', lineHeight: 1.6 }}>
          Theo dõi mức sử dụng sản phẩm từ dữ liệu nội bộ (PostgreSQL). Chỉ hiển thị số liệu tổng hợp — không có nội dung riêng tư của người dùng.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullPage label="Đang tải bảng quản trị…" />}

      {!isLoading && forbidden && (
        <div style={{ textAlign: 'center', padding: '4rem 2rem', color: 'var(--color-text-secondary)' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔒</div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--color-text)', marginBottom: '0.5rem' }}>Không có quyền truy cập</h2>
          <p>Bạn không có quyền truy cập trang quản trị.</p>
          <Link href="/dashboard" style={{ color: 'var(--color-primary)', textDecoration: 'none', display: 'inline-block', marginTop: '1rem' }}>
            ← Về trang phân tích CV
          </Link>
        </div>
      )}

      {!isLoading && !forbidden && error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {!isLoading && !forbidden && overview && (
        <>
          {/* 1. Product usage overview */}
          <Section title="Tổng quan sử dụng sản phẩm">
            <div style={CARD_GRID}>
              <StatCard icon="👥" label="Tổng người dùng" value={fmtNum(funnel.total_users)} />
              <StatCard icon="🧑‍💻" label="Người dùng đã phân tích CV" value={fmtNum(funnel.users_with_analysis)}
                        sublabel={`Tỉ lệ: ${fmtPct(conversion.analysis_per_user_rate)}`} />
              <StatCard icon="📊" label="Tổng lượt phân tích CV" value={fmtNum(funnel.analysis_jobs_total)} />
              <StatCard icon="✅" label="Tỉ lệ phân tích thành công" value={fmtPct(health.success_rate)}
                        sublabel={`Thất bại: ${fmtPct(health.failure_rate)}`} />
              <StatCard icon="🗂️" label="Hồ sơ ứng tuyển" value={fmtNum(funnel.applications_total)} />
              <StatCard icon="🎤" label="Phiên phỏng vấn" value={fmtNum(funnel.interview_sessions_total)} />
              <StatCard icon="🕒" label="Hoạt động gần nhất" value={fmtDateTime(timeline.latest_activity_at)} />
            </div>
          </Section>

          {/* 2. Usage funnel */}
          <Section title="Phễu sử dụng" subtitle="Số người dùng đi qua từng bước (phần trăm so với bước trước).">
            <FunnelStep label="Người dùng" count={funnel.total_users} isFirst />
            <FunnelStep label="Đã phân tích CV" count={funnel.users_with_analysis} pct={conversion.analysis_per_user_rate} />
            <FunnelStep label="Tạo hồ sơ ứng tuyển" count={funnel.users_with_application} pct={conversion.application_per_analysis_user_rate} />
            <FunnelStep label="Luyện phỏng vấn" count={funnel.users_with_interview_session} pct={conversion.interview_per_application_user_rate} />
          </Section>

          {/* 3. Activity windows */}
          <Section title="Hoạt động 7 ngày / 30 ngày">
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 'var(--font-size-sm)' }}>
                <thead>
                  <tr style={{ textAlign: 'left', color: 'var(--color-text-muted)', fontSize: 'var(--font-size-xs)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <th style={{ padding: '0.5rem 0.5rem 0.5rem 0' }}>Chỉ số</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right' }}>7 ngày</th>
                    <th style={{ padding: '0.5rem', textAlign: 'right' }}>30 ngày</th>
                  </tr>
                </thead>
                <tbody>
                  {activityRows.map(([label, key]) => (
                    <tr key={key} style={{ borderTop: '1px solid var(--color-border)' }}>
                      <td style={{ padding: '0.5rem 0.5rem 0.5rem 0', color: 'var(--color-text)' }}>{label}</td>
                      <td style={{ padding: '0.5rem', textAlign: 'right', color: 'var(--color-text-secondary)' }}>{fmtNum(w7[key])}</td>
                      <td style={{ padding: '0.5rem', textAlign: 'right', color: 'var(--color-text-secondary)' }}>{fmtNum(w30[key])}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          {/* 4. Engagement depth */}
          <Section title="Độ sâu sử dụng">
            <div style={CARD_GRID}>
              <StatCard icon="📈" label="Phân tích TB / người dùng" value={fmtNum(depth.average_analysis_jobs_per_user)} />
              <StatCard icon="🗂️" label="Hồ sơ ứng tuyển TB / người dùng" value={fmtNum(depth.average_applications_per_user)} />
              <StatCard icon="🎤" label="Phiên phỏng vấn TB / người dùng" value={fmtNum(depth.average_interview_sessions_per_user)} />
              <StatCard icon="💬" label="Câu trả lời TB / phiên" value={fmtNum(depth.average_interview_answers_per_session)} />
            </div>
          </Section>

          {/* 5. Billing readiness */}
          <Section title="Thanh toán">
            {billingReadiness.billing_enabled ? (
              <div style={CARD_GRID}>
                <StatCard icon="🧾" label="Đơn thanh toán" value={fmtNum(billingReadiness.payment_orders_total)}
                          sublabel={`Đã thanh toán: ${fmtNum(billingReadiness.paid_orders_total)}`} />
                <StatCard icon="💰" label="Doanh thu đã xác nhận" value={formatVnd(billingReadiness.paid_revenue_vnd)} />
                <StatCard icon="🔎" label="Đơn cần kiểm tra" value={fmtNum(billingReadiness.manual_review_orders_total)} />
              </div>
            ) : (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                  <span style={{ padding: '3px 12px', borderRadius: 'var(--radius-full)', fontSize: 'var(--font-size-xs)', fontWeight: 700, background: '#F1F5F9', color: '#64748B' }}>
                    {billingReadiness.billing_status_label || 'Chưa bật'}
                  </span>
                  <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)' }}>
                    Thanh toán chưa được mở cho người dùng thật.
                  </span>
                </div>
                <p style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  Số liệu vận hành (thứ cấp): {fmtNum(billingReadiness.payment_orders_total)} đơn ·
                  {' '}{fmtNum(billingReadiness.paid_orders_total)} đã thanh toán ·
                  {' '}{fmtNum(billingReadiness.manual_review_orders_total)} cần kiểm tra.
                </p>
              </div>
            )}
          </Section>

          {/* 6. Feature flags */}
          <Section title="Trạng thái tính năng">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.75rem' }}>
              <FlagBadge label="Thanh toán (Billing)" enabled={!!flags.ENABLE_BILLING} />
              <FlagBadge label="Giới hạn theo lượt (Credit gating)" enabled={!!flags.ENABLE_CREDIT_GATING} />
              <FlagBadge label="Liên kết chia sẻ (Share links)" enabled={!!flags.ENABLE_PHASE6_SHARE_LINKS} />
            </div>
          </Section>

          {/* Status breakdowns */}
          <Section title="Phân loại trạng thái">
            <Breakdown title="Phân tích theo trạng thái" data={jobs.analysis_jobs_by_status} />
            <Breakdown title="Đơn thanh toán theo trạng thái" data={billing.billing_orders_by_status} />
            <Breakdown title="Sự kiện sử dụng theo loại" data={usage.usage_events_by_type} />
          </Section>

          {/* Recent activity */}
          {recent.length > 0 && (
            <Section title="Hoạt động gần đây">
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
                        <td style={{ padding: '0.5rem', color: 'var(--color-text-muted)' }}>{fmtDateTime(item.created_at)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}

          {/* Meta */}
          <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
            {overview.expected_alembic_head && <span>Phiên bản schema (alembic head): {overview.expected_alembic_head}</span>}
            {overview.generated_at && <span>Cập nhật lúc: {fmtDateTime(overview.generated_at)}</span>}
          </div>
        </>
      )}
    </PageShell>
  );
}
