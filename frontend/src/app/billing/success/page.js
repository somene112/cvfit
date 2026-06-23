'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import PageShell from '@/components/common/PageShell';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { useLanguage } from '@/context/LanguageContext';
import { getBillingOrder, getBillingUsage } from '@/services/billingApi';
import {
  clearPendingBillingOrderId,
  getPendingBillingOrderId,
  isSafePaymentOrderId,
} from '@/services/billingStorage';
import { ANALYTICS_EVENTS, trackEvent } from '@/lib/analytics';
import { BILLING_CREDIT_KEYS } from '@/types/billing';
import { getBillingCopy } from '@/utils/billingUi';
import styles from '@/styles/Billing.module.css';

const MAX_POLL_ATTEMPTS = 20;
const POLL_DELAY_MS = 3000;

export default function BillingSuccessPage() {
  const { isAuthChecking } = useRequireAuth();
  const { lang } = useLanguage();
  const copy = getBillingCopy(lang);
  const [viewState, setViewState] = useState('verifying');
  const [usage, setUsage] = useState(null);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    let timer = null;
    let attempts = 0;

    trackEvent(ANALYTICS_EVENTS.PAYMENT_RETURN_SUCCESS_VIEWED, {
      feature_name: 'billing',
      provider: 'payos',
    });

    const query = new URLSearchParams(window.location.search);
    const queryOrderId = query.get('payment_order_id');
    const orderId = isSafePaymentOrderId(queryOrderId)
      ? queryOrderId
      : getPendingBillingOrderId();

    if (!orderId) {
      setViewState('unidentified');
      return () => { active = false; };
    }

    const poll = async () => {
      attempts += 1;
      try {
        const [orderResult, usageResult] = await Promise.allSettled([
          getBillingOrder(orderId),
          getBillingUsage(),
        ]);
        if (!active) return;
        if (orderResult.status !== 'fulfilled') throw orderResult.reason;
        const order = orderResult.value;
        if (usageResult.status === 'fulfilled') setUsage(usageResult.value);

        if (order.status === 'paid') {
          clearPendingBillingOrderId();
          setViewState('paid');
          return;
        }
        if (order.status === 'manual_review') {
          setViewState('manual_review');
          return;
        }
        if (['cancelled', 'failed', 'expired', 'refunded'].includes(order.status)) {
          clearPendingBillingOrderId();
          setViewState('failed');
          return;
        }

        setViewState('pending');
        if (attempts < MAX_POLL_ATTEMPTS) {
          timer = window.setTimeout(poll, POLL_DELAY_MS);
        }
      } catch {
        if (active) setViewState('error');
      }
    };

    poll();
    return () => {
      active = false;
      if (timer) window.clearTimeout(timer);
    };
  }, [isAuthChecking]);

  const stateContent = {
    verifying: [copy.verifyingTitle, copy.verifyingText],
    pending: [copy.verifyingTitle, copy.pendingText],
    paid: [copy.confirmedTitle, copy.confirmedText],
    manual_review: [copy.reviewTitle, copy.reviewText],
    failed: [copy.failedTitle, copy.failedText],
    unidentified: [copy.unidentifiedTitle, copy.unidentifiedText],
    error: [copy.reviewTitle, copy.checkError],
  }[viewState];

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="760px">
      <div className={`${styles.resultPanel} ${styles[`resultPanel--${viewState}`] || ''}`}>
        <div className={styles.resultIcon} aria-hidden="true">
          {viewState === 'paid' ? '✓' : viewState === 'failed' ? '×' : '…'}
        </div>
        <h1 className={styles.resultTitle}>{stateContent[0]}</h1>
        <p className={styles.resultText}>{stateContent[1]}</p>

        {viewState === 'paid' && usage && (
          <div className={styles.balanceSummary}>
            {BILLING_CREDIT_KEYS.map((key) => (
              <div key={key}>
                <span>{copy.creditLabels[key]}</span>
                <strong>{usage.remaining_credits?.[key] || 0}</strong>
              </div>
            ))}
          </div>
        )}

        <div className={styles.resultActions}>
          <Link href="/billing" className={styles.primaryLink}>{copy.backBilling}</Link>
          {['failed', 'error'].includes(viewState) && (
            <Link href="/pricing" className={styles.secondaryButton}>{copy.tryAgain}</Link>
          )}
        </div>
      </div>
    </PageShell>
  );
}
