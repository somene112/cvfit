'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { useLanguage } from '@/context/LanguageContext';
import { getBillingOrders, getBillingUsage } from '@/services/billingApi';
import { ANALYTICS_EVENTS, trackEvent } from '@/lib/analytics';
import { BILLING_CREDIT_KEYS } from '@/types/billing';
import { formatBillingDate, formatVnd, getBillingCopy, getPlanName } from '@/utils/billingUi';
import styles from '@/styles/Billing.module.css';

function statusClass(status) {
  if (status === 'paid') return styles.statusPaid;
  if (status === 'pending' || status === 'created') return styles.statusPending;
  if (status === 'manual_review') return styles.statusReview;
  return styles.statusFailed;
}

export default function BillingPage() {
  const { isAuthChecking } = useRequireAuth();
  const { lang } = useLanguage();
  const copy = getBillingCopy(lang);
  const [usage, setUsage] = useState(null);
  const [orders, setOrders] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    trackEvent(ANALYTICS_EVENTS.BILLING_VIEWED, { feature_name: 'billing' });

    Promise.all([getBillingUsage(), getBillingOrders()])
      .then(([usageData, orderData]) => {
        if (!active) return;
        setUsage(usageData);
        setOrders(Array.isArray(orderData?.orders) ? orderData.orders : []);
      })
      .catch((err) => {
        if (!active) return;
        setError(err?.response?.status === 503 ? copy.billingUnavailable : copy.checkError);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => { active = false; };
  }, [copy.billingUnavailable, copy.checkError, isAuthChecking]);

  const pendingCount = orders.filter((order) => ['created', 'pending'].includes(order.status)).length;

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="1120px">
      <div className={styles.pageHeader}>
        <div>
          <span className={styles.eyebrow}>{usage?.month ? `${copy.month}: ${usage.month}` : 'Phase 7A'}</span>
          <h1 className={styles.pageTitle}>{copy.billingTitle}</h1>
          <p className={styles.pageSubtitle}>{copy.billingSubtitle}</p>
        </div>
        <div className={styles.headerActions}>
          <Link href="/usage" className={styles.secondaryButton}>{copy.backToUsage}</Link>
          <Link href="/pricing" className={styles.primaryLink}>{copy.viewPricing}</Link>
        </div>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading ? (
        <div className={styles.centerState}><LoadingSpinner label={copy.loadingBilling} /></div>
      ) : usage ? (
        <section aria-labelledby="credit-balances-title">
          <h2 id="credit-balances-title" className={styles.sectionTitle}>{copy.paidRemaining}</h2>
          <div className={styles.creditGrid}>
            {BILLING_CREDIT_KEYS.map((key) => (
              <article className={styles.creditCard} key={key}>
                <h3>{copy.creditLabels[key]}</h3>
                <div className={styles.creditTotal}>{usage.remaining_credits?.[key] || 0}</div>
                <dl className={styles.creditBreakdown}>
                  <div><dt>{copy.freeAllowance}</dt><dd>{usage.free_allowance?.[key] || 0}</dd></div>
                  <div><dt>{copy.usedThisMonth}</dt><dd>{usage.used_this_month?.[key] || 0}</dd></div>
                  <div><dt>{copy.freeRemaining}</dt><dd>{usage.free_remaining?.[key] || 0}</dd></div>
                </dl>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      {!isLoading && (
        <section className={styles.ordersSection} aria-labelledby="payment-history-title">
          <div className={styles.sectionHeadingRow}>
            <h2 id="payment-history-title" className={styles.sectionTitle}>{copy.orderHistory}</h2>
            {pendingCount > 0 && <span className={styles.pendingBadge}>{pendingCount} {copy.pendingLabel}</span>}
          </div>
          {pendingCount > 0 && <p className={styles.sectionHint}>{copy.pendingOrders}</p>}

          {orders.length === 0 ? (
            <div className={styles.emptyPanel}>
              <p>{copy.noOrders}</p>
              <Link href="/pricing" className={styles.primaryLink}>{copy.viewPricing}</Link>
            </div>
          ) : (
            <div className={styles.tableWrapper}>
              <table className={styles.ordersTable}>
                <thead>
                  <tr>
                    <th>{copy.plan}</th>
                    <th>{copy.amount}</th>
                    <th>{copy.status}</th>
                    <th>{copy.created}</th>
                    <th>{copy.paid}</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.payment_order_id}>
                      <td className={styles.planCode}>{getPlanName(order.plan_code, order.plan_code)}</td>
                      <td>{formatVnd(order.amount, lang)} <span className={styles.currency}>{order.currency}</span></td>
                      <td><span className={`${styles.statusBadge} ${statusClass(order.status)}`}>{copy.statusLabels[order.status] || order.status.replaceAll('_', ' ')}</span></td>
                      <td>{formatBillingDate(order.created_at, lang)}</td>
                      <td>{formatBillingDate(order.paid_at, lang)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </PageShell>
  );
}
