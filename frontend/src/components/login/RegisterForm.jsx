'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useLanguage } from '@/context/LanguageContext';
import { register } from '@/services/authApi';
import { storeAuthSession } from '@/services/authStorage';
import GoogleSignInButton from '@/components/login/GoogleSignInButton';
import styles from '@/styles/LoginForm.module.css';

export default function RegisterForm() {
  const router = useRouter();
  const { t } = useLanguage();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password.trim()) {
      setError(t('register.error.empty'));
      return;
    }
    if (password.length < 8) {
      setError(t('register.error.password'));
      return;
    }

    setIsLoading(true);
    try {
      const authResponse = await register({
        email: email.trim(),
        password,
        full_name: fullName.trim() || null,
      });
      storeAuthSession(authResponse);
      router.push('/dashboard');
    } catch (err) {
      setError(t('register.error.invalid'));
    } finally {
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
        <p className={styles.subtitle}>{t('register.subtitle')}</p>

        <form className={styles.form} onSubmit={handleSubmit} id="register-form">
          {error && (
            <div className={styles.errorMessage} role="alert" id="register-error">
              <svg className={styles.errorIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
              {error}
            </div>
          )}

          <div className={styles.inputGroup}>
            <label className={styles.inputLabel} htmlFor="register-full-name">
              {t('register.fullName')}
            </label>
            <div className={styles.inputWrapper}>
              <input
                id="register-full-name"
                className={styles.input}
                type="text"
                placeholder="Nguyen Van A"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                autoComplete="name"
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.inputLabel} htmlFor="register-email">
              {t('login.email')}
            </label>
            <div className={styles.inputWrapper}>
              <input
                id="register-email"
                className={styles.input}
                type="email"
                placeholder="you@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>
          </div>

          <div className={styles.inputGroup}>
            <label className={styles.inputLabel} htmlFor="register-password">
              {t('login.password')}
            </label>
            <div className={styles.inputWrapper}>
              <input
                id="register-password"
                className={styles.input}
                type="password"
                placeholder="********"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="new-password"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className={styles.submitButton}
            disabled={isLoading}
            id="register-submit"
          >
            <span className={styles.buttonContent}>
              {isLoading && <span className={styles.spinner} />}
              {isLoading ? t('register.btn.creating') : t('register.btn.create')}
            </span>
          </button>
        </form>

        <GoogleSignInButton
          onSuccess={() => router.push('/dashboard')}
          onError={(message) => setError(message)}
        />

        <p className={styles.footer}>
          {t('register.footer.text')}{' '}
          <Link href="/login" className={styles.footerLink}>
            {t('register.footer.link')}
          </Link>
        </p>
      </div>
    </div>
  );
}
