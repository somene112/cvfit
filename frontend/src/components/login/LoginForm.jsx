'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/LoginForm.module.css';

export default function LoginForm() {
  const router = useRouter();
  const { t } = useLanguage();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password.trim()) {
      setError(t('login.error.empty'));
      return;
    }

    setIsLoading(true);

    try {
      /* 
        Since this is a frontend-only app, we simulate login.
        Replace this with actual authentication API call when backend is ready.
      */
      await new Promise((resolve) => setTimeout(resolve, 1200));
      localStorage.setItem('auth_token', 'session_token_placeholder');
      localStorage.setItem(
        'user',
        JSON.stringify({ email, name: email.split('@')[0] })
      );
      router.push('/dashboard');
    } catch (err) {
      setError(t('login.error.invalid'));
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.loginPage}>
      <div className={styles.backgroundGrid} />
      <div className={styles.card}>
        <div className={styles.logoContainer}>
          <div className={styles.logoIcon}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          </div>
          <span className={styles.logoText}>{t('landing.logo')}</span>
        </div>
        <p className={styles.subtitle}>{t('login.subtitle')}</p>

        <form className={styles.form} onSubmit={handleSubmit} id="login-form">
          {error && (
            <div className={styles.errorMessage} role="alert" id="login-error">
              <svg className={styles.errorIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
              {error}
            </div>
          )}

          <div className={styles.inputGroup}>
            <label className={styles.inputLabel} htmlFor="login-email">
              {t('login.email')}
            </label>
            <div className={styles.inputWrapper}>
              <input
                id="login-email"
                className={styles.input}
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
              <svg className={styles.inputIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                <polyline points="22,6 12,13 2,6" />
              </svg>
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.inputLabel} htmlFor="login-password">
              {t('login.password')}
            </label>
            <div className={styles.inputWrapper}>
              <input
                id="login-password"
                className={styles.input}
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
              <svg className={styles.inputIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </div>
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isLoading}
            id="login-submit"
          >
            <span className={styles.buttonContent}>
              {isLoading && <span className={styles.spinner} />}
              {isLoading ? t('login.btn.signingIn') : t('login.btn.signIn')}
            </span>
          </button>
        </form>

        <div className={styles.divider}>
          <span className={styles.dividerText}>{t('login.divider')}</span>
        </div>

        <p className={styles.footer}>
          {t('login.footer.text')}{' '}
          <span className={styles.footerLink}>{t('login.footer.link')}</span>
        </p>
      </div>
    </div>
  );
}
