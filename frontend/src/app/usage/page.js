'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import { getUsage } from '@/services/usageApi';
import { extractApiError } from '@/utils/errorHelpers';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
import styles from '@/styles/Usage.module.css';

const UPGRADE_FEATURES = [
  'Unlimited CV analyses per month',
  'Unlimited interview sessions',
  'Unlimited cover letters & packages',
  'Up to 25 active share links',
  'Priority AI response speed',
  'Advanced rubric feedback',
];

const METRIC_META = {
  analyses:             { icon: '📊', label: 'CV Analyses', sublabel: 'This month' },
  interview_answers:    { icon: '🎤', label: 'Interview Answers', sublabel: 'This month' },
  cover_letters:        { icon: '✉️', label: 'Cover Letters', sublabel: 'Generated' },
  application_packages: { icon: '📦', label: 'App Packages', sublabel: 'Generated' },
  share_links:          { icon: '🔗', label: 'Share Links', sublabel: 'Active' },
};

function getProgressVariant(pct) {
  if (pct >= 90) return styles['progressFill--danger'];
  if (pct >= 70) return styles['progressFill--warning'];
  return styles['progressFill--normal'];
}

function MetricCard({ metricKey, data, index }) {
  const meta = METRIC_META[metricKey] || { icon: '📈', label: metricKey, sublabel: '' };
  const { used, limit } = data || { used: 0, limit: null };
  const pct = limit ? Math.min(100, Math.round((used / limit) * 100)) : 0;
  const isUnlimited = limit === null || limit === -1;

  const iconBgs = [
    { bg: '#EFF6FF', color: 'var(--color-primary)' },
    { bg: '#F5F3FF', color: '#7C3AED' },
    { bg: '#ECFDF5', color: '#059669' },
    { bg: '#FFF7ED', color: '#D97706' },
    { bg: '#FDF4FF', color: '#9333EA' },
  ];
  const iconStyle = iconBgs[index % iconBgs.length];

  return (
    <div className={styles.metricCard} style={{ animationDelay: `${index * 0.07}s` }}>
      <div className={styles.metricHeader}>
        <div className={styles.metricIcon} style={{ background: iconStyle.bg, color: iconStyle.color }}>
          {meta.icon}
        </div>
        <div>
          <div className={styles.metricLabel}>{meta.label}</div>
          <div className={styles.metricSublabel}>{meta.sublabel}</div>
        </div>
      </div>

      {isUnlimited ? (
        <div>
          <div className={styles.progressNumbers}>
            <span className={styles.progressUsed}>{used}</span>
            <span className={styles.unlimitedBadge}>
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Unlimited
            </span>
          </div>
          <p className={styles.progressCaption}>No limit on your current plan</p>
        </div>
      ) : (
        <div className={styles.progressWrapper}>
          <div className={styles.progressNumbers}>
            <span className={styles.progressUsed}>{used}</span>
            <span className={styles.progressLimit}>/ {limit}</span>
          </div>
          <div className={styles.progressTrack}>
            <div
              className={`${styles.progressFill} ${getProgressVariant(pct)}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className={styles.progressCaption}>
            {pct >= 90 ? '⚠ Nearly at limit — consider upgrading' :
             pct >= 70 ? `${limit - used} remaining this period` :
             `${limit - used} remaining this period`}
          </p>
        </div>
      )}
    </div>
  );
}

function SkeletonMetric() {
  return (
    <div className={styles.metricCard}>
      <div style={{ height: 40, background: 'var(--color-border)', borderRadius: 'var(--radius-md)', marginBottom: '1rem', width: '60%', animation: 'shimmer 1.5s infinite', backgroundSize: '200% 100%', backgroundImage: 'linear-gradient(90deg, var(--color-border) 25%, #F1F5F9 50%, var(--color-border) 75%)' }} />
      <div style={{ height: 32, background: 'var(--color-border)', borderRadius: 'var(--radius-md)', marginBottom: '0.5rem', width: '40%', animation: 'shimmer 1.5s infinite', backgroundSize: '200% 100%', backgroundImage: 'linear-gradient(90deg, var(--color-border) 25%, #F1F5F9 50%, var(--color-border) 75%)' }} />
      <div style={{ height: 8, background: 'var(--color-border)', borderRadius: 'var(--radius-full)', animation: 'shimmer 1.5s infinite', backgroundSize: '200% 100%', backgroundImage: 'linear-gradient(90deg, var(--color-border) 25%, #F1F5F9 50%, var(--color-border) 75%)' }} />
    </div>
  );
}

export default function UsagePage() {
  const { isAuthChecking } = useRequireAuth();
  const [usageData, setUsageData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await getUsage();
        if (!active) return;
        setUsageData(data);
        trackEvent(ANALYTICS_EVENTS.USAGE_PAGE_VIEWED, {
          feature_name: 'usage',
          plan_name: data?.plan?.name || 'unknown',
        });
      } catch (err) {
        if (!active) return;
        const { message } = extractApiError(err, 'Could not load your usage data.');
        setError(message);
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking]);

  const plan = usageData?.plan;
  const usage = usageData?.usage || {};
  const usageKeys = Object.keys(METRIC_META);

  const formatPeriod = (start, end) => {
    if (!start || !end) return null;
    const s = new Date(start);
    const e = new Date(end);
    if (isNaN(s.getTime()) || isNaN(e.getTime())) return null;
    return `${s.toLocaleDateString()} – ${e.toLocaleDateString()}`;
  };

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="960px">
      {/* Page Header */}
      <div className={styles.pageHeader}>
        <h1 className={styles.pageTitle}>Usage &amp; Plan</h1>
        <p className={styles.pageSubtitle}>
          Track your monthly usage across all AI features. Limits reset at the start of each billing period.
        </p>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Plan Card */}
      {(isLoading || plan) && (
        <div className={styles.planCard}>
          <div className={styles.planBadge}>Current Plan</div>
          <div className={styles.planName}>
            {isLoading ? 'Loading…' : (plan?.name || 'Free')}
          </div>
          <p className={styles.planDesc}>
            {isLoading ? '' : (plan?.description || 'Your current plan includes access to all core features.')}
          </p>
          {usageData?.period_start && usageData?.period_end && (
            <div className={styles.planPeriod}>
              Billing period: {formatPeriod(usageData.period_start, usageData.period_end)}
            </div>
          )}
        </div>
      )}

      {/* Usage Metrics */}
      <div className={styles.usageGrid}>
        {isLoading
          ? [1, 2, 3, 4, 5].map((k) => <SkeletonMetric key={k} />)
          : usageKeys.map((key, i) => (
              <MetricCard
                key={key}
                metricKey={key}
                data={usage[key]}
                index={i}
              />
            ))}
      </div>

      {/* Upgrade Teaser — UI only, no payment flow */}
      {!isLoading && plan?.tier !== 'premium' && (
        <div className={styles.upgradeCard}>
          <div className={styles.upgradeHeader}>
            <div className={styles.upgradeIcon}>🚀</div>
            <div style={{ flex: 1 }}>
              <div className={styles.upgradeTitle}>Unlock Unlimited Access</div>
              <p className={styles.upgradeDesc}>
                Remove all monthly limits and get faster AI responses, richer rubric feedback, and more share links — all with a Pro plan.
              </p>
            </div>
          </div>

          <div className={styles.upgradeFeatures}>
            {UPGRADE_FEATURES.map((feature) => (
              <div key={feature} className={styles.upgradeFeature}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {feature}
              </div>
            ))}
          </div>

          <p className={styles.upgradeNote}>
            Interested in upgrading? Contact the team or check your account settings. Payment is handled securely outside this app.
          </p>
        </div>
      )}

      {/* Footer */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.75rem', fontSize: 'var(--font-size-sm)', marginTop: '2rem', paddingTop: '1.5rem', borderTop: '1px solid var(--color-border)' }}>
        <Link href="/dashboard" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>CV Analysis</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/applications" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Applications</Link>
        <span style={{ color: 'var(--color-text-muted)' }}>·</span>
        <Link href="/help" style={{ color: 'var(--color-primary)', textDecoration: 'none' }}>Help</Link>
      </div>
    </PageShell>
  );
}
