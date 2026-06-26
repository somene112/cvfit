'use client';

import Link from 'next/link';
import { useLanguage } from '@/context/LanguageContext';
import LanguageSwitcher from '@/components/common/LanguageSwitcher';
import { trackEvent, ANALYTICS_EVENTS } from '@/lib/analytics';
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

        <div className={styles.heroInner}>
          {/* Left: Content */}
          <div className={styles.heroContent}>
            <div className={styles.badge}>{t('landing.badge')}</div>
            <h1 className={styles.headline}>
              {t('landing.headline.1')}{' '}
              <span>{t('landing.headline.2')}</span>
              {t('landing.headline.3') ? ` ${t('landing.headline.3')}` : ''}
            </h1>
            <p className={styles.subheadline}>
              {t('landing.subheadline')}
            </p>
            <div className={styles.ctaGroup}>
              <Link
                href="/login"
                className={styles.primaryCta}
                onClick={() => trackEvent(ANALYTICS_EVENTS.LANDING_CTA_CLICK, { feature_name: 'landing', source: 'hero_cta' })}
              >
                {t('landing.ctaPrimary')}
              </Link>
              <a href="#how-it-works" className={styles.secondaryCta}>
                Xem cách hoạt động
              </a>
            </div>
          </div>

          {/* Right: Mock Score Card */}
          <div className={styles.heroVisual}>
            {/* Floating success chip */}
            <div className={styles.floatingChip}>
              <span className={styles.chipDot}></span>
              <span className={styles.chipText}>Phân tích hoàn tất!</span>
            </div>

            <div className={styles.scoreCard}>
              {/* SVG gradient definition */}
              <svg width="0" height="0" style={{ position: 'absolute' }}>
                <defs>
                  <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#6366f1" />
                    <stop offset="100%" stopColor="#8b5cf6" />
                  </linearGradient>
                </defs>
              </svg>

              <div className={styles.cardHeader}>
                <span className={styles.cardTitle}>Kết quả phân tích CV</span>
                <span className={styles.cardBadge}>AI Sẵn sàng</span>
              </div>

              {/* Score ring */}
              <div className={styles.scoreRing}>
                <div className={styles.ringWrap}>
                  <svg viewBox="0 0 100 100">
                    <circle className={styles.ringBg} cx="50" cy="50" r="40" />
                    <circle className={styles.ringFg} cx="50" cy="50" r="40" />
                  </svg>
                  <div className={styles.ringText}>
                    <span className={styles.ringScore}>87%</span>
                    <span className={styles.ringLabel}>Phù hợp</span>
                  </div>
                </div>
                <div className={styles.scoreInfo}>
                  <div className={styles.scoreLevel}>Phù hợp xuất sắc</div>
                  <div className={styles.scoreSub}>CV của bạn đáp ứng 87% yêu cầu của vị trí Senior Developer</div>
                </div>
              </div>

              {/* Skill bars */}
              <div className={styles.skillBars}>
                <div className={styles.skillRow}>
                  <div className={styles.skillMeta}>
                    <span className={styles.skillName}>Kỹ năng kỹ thuật</span>
                    <span className={styles.skillPct}>92%</span>
                  </div>
                  <div className={styles.barTrack}>
                    <div className={styles.barFill} style={{ width: '92%' }}></div>
                  </div>
                </div>
                <div className={styles.skillRow}>
                  <div className={styles.skillMeta}>
                    <span className={styles.skillName}>Kinh nghiệm làm việc</span>
                    <span className={styles.skillPct}>78%</span>
                  </div>
                  <div className={styles.barTrack}>
                    <div className={`${styles.barFill} ${styles.green}`} style={{ width: '78%' }}></div>
                  </div>
                </div>
                <div className={styles.skillRow}>
                  <div className={styles.skillMeta}>
                    <span className={styles.skillName}>Kỹ năng mềm</span>
                    <span className={styles.skillPct}>85%</span>
                  </div>
                  <div className={styles.barTrack}>
                    <div className={`${styles.barFill} ${styles.blue}`} style={{ width: '85%' }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating tip chip */}
            <div className={styles.floatingChip2}>
              <span className={styles.chipIcon}>💡</span>
              <span className={styles.chipText2}>3 gợi ý cải thiện CV</span>
            </div>
          </div>
        </div>
      </section>

      {/*
        Value strip — honest product positioning only.
        Intentionally non-numeric: no fake scale, accuracy, speed, or rating
        claims. Each label describes a real product capability surfaced in
        Sections 2–7 of the demo flow.
      */}
      <div className={styles.statsBar}>
        <div className={styles.statsInner}>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>Phân tích CV theo JD</div>
          </div>
          <div className={styles.statDivider}></div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>Gợi ý cải thiện có kiểm soát</div>
          </div>
          <div className={styles.statDivider}></div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>Lộ trình học tập cá nhân hoá</div>
          </div>
          <div className={styles.statDivider}></div>
          <div className={styles.statItem}>
            <div className={styles.statLabel}>Thanh toán đang thử nghiệm</div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section className={styles.features}>
        <div className={styles.sectionLabel}>Tính năng nổi bật</div>
        <h2 className={styles.sectionTitle}>{t('landing.features.title')}</h2>
        <p className={styles.sectionSubtitle}>
          Mọi thứ bạn cần để tối ưu hóa CV và gia tăng cơ hội được tuyển dụng.
        </p>
        <div className={styles.featuresGrid}>
          {/* Feature 1 */}
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.indigo}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <polyline points="12 6 12 12 16 14" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('landing.feature1.title')}</h3>
            <p className={styles.featureDesc}>{t('landing.feature1.desc')}</p>
          </div>

          {/* Feature 2 */}
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.violet}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('landing.feature2.title')}</h3>
            <p className={styles.featureDesc}>{t('landing.feature2.desc')}</p>
          </div>

          {/* Feature 3 */}
          <div className={styles.featureCard}>
            <div className={`${styles.featureIcon} ${styles.blue}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 20h9" />
                <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z" />
              </svg>
            </div>
            <h3 className={styles.featureTitle}>{t('landing.feature3.title')}</h3>
            <p className={styles.featureDesc}>{t('landing.feature3.desc')}</p>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className={styles.howItWorks}>
        <div className={styles.sectionLabel}>Quy trình</div>
        <h2 className={styles.sectionTitle}>{t('landing.how.title')}</h2>
        <p className={styles.sectionSubtitle}>
          Chỉ 3 bước đơn giản để có được báo cáo phân tích CV chi tiết.
        </p>
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
          {t('landing.bottomCta.btn')} →
        </Link>
      </section>

      {/* Footer */}
      <footer className={styles.footer}>
        <p>{t('landing.footer')}</p>
      </footer>
    </div>
  );
}
