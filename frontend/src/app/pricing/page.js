'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import PageShell from '@/components/common/PageShell';
import ErrorBanner from '@/components/common/ErrorBanner';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { useLanguage } from '@/context/LanguageContext';
import { createBillingCheckout, getBillingPlans } from '@/services/billingApi';
import { storePendingBillingOrderId } from '@/services/billingStorage';
import { ANALYTICS_EVENTS, trackEvent } from '@/lib/analytics';
import { amountBucket, formatVnd, getBillingCopy, getSafeCheckoutUrl } from '@/utils/billingUi';
import { BILLING_CREDIT_KEYS } from '@/types/billing';
import styles from '@/styles/Billing.module.css';

export default function PricingPage() {
  const { isAuthChecking } = useRequireAuth();
  const { lang } = useLanguage();
  const copy = getBillingCopy(lang);
  const [plans, setPlans] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [checkoutPlan, setCheckoutPlan] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;

    trackEvent(ANALYTICS_EVENTS.PRICING_VIEWED, { feature_name: 'billing' });
    getBillingPlans()
      .then((data) => {
        if (active) setPlans(Array.isArray(data?.plans) ? data.plans : []);
      })
      .catch((err) => {
        if (!active) return;
        setError(err?.response?.status === 503 ? copy.billingUnavailable : copy.providerError);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => { active = false; };
  }, [copy.billingUnavailable, copy.providerError, isAuthChecking]);

  const startCheckout = async (plan) => {
    setCheckoutPlan(plan.plan_code);
    setError(null);
    const analyticsPayload = {
      plan_code: plan.plan_code,
      amount_bucket: amountBucket(plan.amount),
      provider: 'payos',
    };
    trackEvent(ANALYTICS_EVENTS.CHECKOUT_STARTED, analyticsPayload);

    try {
      const checkout = await createBillingCheckout(plan.plan_code);
      const checkoutUrl = getSafeCheckoutUrl(checkout?.checkout_url);
      if (!checkoutUrl || !checkout?.payment_order_id) {
        throw new Error('Invalid checkout response');
      }
      storePendingBillingOrderId(checkout.payment_order_id);
      trackEvent(ANALYTICS_EVENTS.CHECKOUT_REDIRECTED, analyticsPayload);
      window.location.assign(checkoutUrl);
    } catch (err) {
      setCheckoutPlan(null);
      setError(err?.response?.status === 503 ? copy.billingUnavailable : copy.providerError);
    }
  };

  return (
    <PageShell isAuthChecking={isAuthChecking} maxWidth="1040px">
      <div className={styles.pageHeader}>
        <div>
          <span className={styles.eyebrow}>Phase 7A</span>
          <h1 className={styles.pageTitle}>{copy.pricingTitle}</h1>
          <p className={styles.pageSubtitle}>{copy.pricingSubtitle}</p>
        </div>
        <Link href="/billing" className={styles.secondaryButton}>{copy.viewBilling}</Link>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading ? (
        <div className={styles.centerState}>
          <LoadingSpinner label={copy.pricingLoading} />
        </div>
      ) : (
        <div className={styles.planGrid}>
          {plans.map((plan, index) => (
            <article
              className={`${styles.planCard} ${index === 1 ? styles.planCardFeatured : ''}`}
              key={plan.plan_code}
            >
              {index === 1 && <span className={styles.featuredBadge}>{copy.demoValue}</span>}
              <h2 className={styles.planName}>{plan.name}</h2>
              <div className={styles.planPrice}>{formatVnd(plan.amount, lang)}</div>
              <div className={styles.oneTimeLabel}>{copy.oneTimePurchase}</div>
              {plan.description && <p className={styles.planDescription}>{plan.description}</p>}

              <ul className={styles.creditList}>
                {BILLING_CREDIT_KEYS.map((key) => (
                  <li key={key}>
                    <span>{copy.creditLabels[key]}</span>
                    <strong>+{plan.credits?.[key] || 0}</strong>
                  </li>
                ))}
              </ul>

              <button
                type="button"
                className={styles.primaryButton}
                onClick={() => startCheckout(plan)}
                disabled={Boolean(checkoutPlan)}
              >
                {checkoutPlan === plan.plan_code ? copy.buying : copy.buy}
              </button>
            </article>
          ))}
        </div>
      )}

      {!isLoading && plans.length === 0 && !error && (
        <div className={styles.emptyPanel}>{copy.billingUnavailable}</div>
      )}

      <div className={styles.securityNote}>
        <strong>{copy.serverVerifiedTitle}</strong>
        <span>{copy.serverVerifiedText}</span>
      </div>
    </PageShell>
  );
}
