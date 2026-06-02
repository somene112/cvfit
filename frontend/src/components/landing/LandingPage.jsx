'use client';

import Link from 'next/link';
import { useLanguage } from '@/context/LanguageContext';
import LanguageSwitcher from '@/components/common/LanguageSwitcher';
import styles from '@/styles/LandingPage.module.css';

export default function LandingPage() {
  const { t } = useLanguage();

  return (
    <div className={styles.page}>
      {/* Navigation */}
      <nav className={styles.navbar}>
        <Link href="/" className={styles.logo}>
          <div className={styles.logoIcon}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          {t('landing.logo')}
        </Link>
        <div className={styles.navLinks}>
          <LanguageSwitcher />
          <Link href="/login" className={styles.signInBtn}>{t('landing.signIn')}</Link>
          <Link href="/login" className={styles.getStartedBtnNav}>{t('landing.getStarted')}</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className={styles.hero}>
        <div className={styles.heroBg}>
          <div className={styles.orb1} />
          <div className={styles.orb2} />
        </div>
        
        <div className={styles.heroContent}>
          <div className={styles.badge}>{t('landing.badge')}</div>
          <h1 className={styles.headline}>
            {t('landing.headline.1')} <span>{t('landing.headline.2')}</span> {t('landing.headline.3')}
          </h1>
          <p className={styles.subheadline}>
            {t('landing.subheadline')}
          </p>
          <div className={styles.ctaGroup}>
            <Link href="/login" className={styles.primaryCta}>
              {t('landing.ctaPrimary')}
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className={styles.features}>
        <h2 className={styles.sectionTitle}>{t('landing.features.title')}</h2>
        <div className={styles.featuresGrid}>
          {/* Feature 1 */}
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
                <path d="M2 12h20" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('landing.feature1.title')}</h3>
            <p className={styles.featureDesc}>
              {t('landing.feature1.desc')}
            </p>
          </div>

          {/* Feature 2 */}
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('landing.feature2.title')}</h3>
            <p className={styles.featureDesc}>
              {t('landing.feature2.desc')}
            </p>
          </div>

          {/* Feature 3 */}
          <div className={styles.featureCard}>
            <div className={styles.featureIcon}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('landing.feature3.title')}</h3>
            <p className={styles.featureDesc}>
              {t('landing.feature3.desc')}
            </p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className={styles.howItWorks}>
        <h2 className={styles.sectionTitle}>{t('landing.how.title')}</h2>
        <div className={styles.stepsGrid}>
          <div className={styles.step}>
            <div className={styles.stepNum}>1</div>
            <h3 className={styles.stepTitle}>{t('landing.how1.title')}</h3>
            <p className={styles.stepDesc}>{t('landing.how1.desc')}</p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>2</div>
            <h3 className={styles.stepTitle}>{t('landing.how2.title')}</h3>
            <p className={styles.stepDesc}>{t('landing.how2.desc')}</p>
          </div>
          <div className={styles.step}>
            <div className={styles.stepNum}>3</div>
            <h3 className={styles.stepTitle}>{t('landing.how3.title')}</h3>
            <p className={styles.stepDesc}>{t('landing.how3.desc')}</p>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className={styles.bottomCta}>
        <h2 className={styles.bottomCtaTitle}>{t('landing.bottomCta.title')}</h2>
        <p className={styles.bottomCtaDesc}>{t('landing.bottomCta.desc')}</p>
        <Link href="/login" className={styles.bottomCtaBtn}>
          {t('landing.bottomCta.btn')}
        </Link>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <p>{t('landing.footer')}</p>
      </footer>
    </div>
  );
}
