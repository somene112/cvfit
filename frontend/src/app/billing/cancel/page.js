'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import PageShell from '@/components/common/PageShell';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { useLanguage } from '@/context/LanguageContext';
import { clearPendingBillingOrderId } from '@/services/billingStorage';
import { ANALYTICS_EVENTS, trackEvent } from '@/lib/analytics';
import { getBillingCopy } from '@/utils/billingUi';
import styles from '@/styles/Billing.module.css';

export default function BillingCancelPage() {
  const { isAuthChecking } = useRequireAuth();
  const { lang } = useLanguage();
  const copy = getBillingCopy(lang);

  useEffect(() => {
    if (isAuthChecking) return;
    clearPendingBillingOrderId();
    trackEvent(ANALYTICS_EVENTS.PAYMENT_CANCEL_VIEWED, {
      feature_name: 'billing',
      provider: 'payos',
    });
  }, [isAuthChecking]);

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="720px">
      <div className={`${styles.resultPanel} ${styles['resultPanel--failed']}`}>
        <div className={styles.resultIcon} aria-hidden="true">×</div>
        <h1 className={styles.resultTitle}>{copy.cancelTitle}</h1>
        <p className={styles.resultText}>{copy.cancelText}</p>
        <div className={styles.resultActions}>
          <Link href="/billing" className={styles.primaryLink}>{copy.backBilling}</Link>
          <Link href="/pricing" className={styles.secondaryButton}>{copy.tryAgain}</Link>
        </div>
      </div>
    </PageShell>
  );
}
