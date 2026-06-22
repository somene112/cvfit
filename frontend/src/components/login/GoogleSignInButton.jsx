'use client';

import { useCallback, useEffect, useRef } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { loginWithGoogle } from '@/services/authApi';
import { storeAuthSession } from '@/services/authStorage';
import { GOOGLE_CLIENT_ID } from '@/utils/constants';
import styles from '@/styles/LoginForm.module.css';

const GSI_SRC = 'https://accounts.google.com/gsi/client';

// Load the Google Identity Services script exactly once per page.
let gsiScriptPromise = null;

function loadGsiScript() {
  if (typeof window === 'undefined') {
    return Promise.reject(new Error('not in browser'));
  }
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }
  if (gsiScriptPromise) {
    return gsiScriptPromise;
  }
  gsiScriptPromise = new Promise((resolve, reject) => {
    const onError = () => {
      gsiScriptPromise = null;
      reject(new Error('failed to load Google Identity Services'));
    };
    const existing = document.querySelector(`script[src="${GSI_SRC}"]`);
    if (existing) {
      existing.addEventListener('load', () => resolve());
      existing.addEventListener('error', onError);
      return;
    }
    const script = document.createElement('script');
    script.src = GSI_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = onError;
    document.head.appendChild(script);
  });
  return gsiScriptPromise;
}

/**
 * Renders the "Continue with Google" button using Google Identity Services.
 * When NEXT_PUBLIC_GOOGLE_CLIENT_ID is unset, shows a safe disabled note instead
 * so the surrounding email/password form keeps working.
 *
 * The Google credential (an ID token) is never logged — it is forwarded directly
 * to the backend and the returned app session is stored like a normal login.
 */
export default function GoogleSignInButton({ onSuccess, onError }) {
  const { t } = useLanguage();
  const buttonRef = useRef(null);

  const handleCredential = useCallback(
    async (response) => {
      const credential = response?.credential;
      if (!credential) {
        onError?.(t('login.google.error'));
        return;
      }
      try {
        const authResponse = await loginWithGoogle(credential);
        storeAuthSession(authResponse);
        onSuccess?.();
      } catch {
        onError?.(t('login.google.error'));
      }
    },
    [onSuccess, onError, t]
  );

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) {
      return undefined;
    }
    let cancelled = false;
    loadGsiScript()
      .then(() => {
        if (cancelled || !window.google?.accounts?.id || !buttonRef.current) {
          return;
        }
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleCredential,
        });
        buttonRef.current.innerHTML = '';
        window.google.accounts.id.renderButton(buttonRef.current, {
          type: 'standard',
          theme: 'outline',
          size: 'large',
          text: 'continue_with',
          shape: 'pill',
          logo_alignment: 'center',
          width: 320,
        });
      })
      .catch(() => {
        if (!cancelled) {
          onError?.(t('login.google.error'));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [handleCredential, onError, t]);

  if (!GOOGLE_CLIENT_ID) {
    return (
      <div className={styles.googleSection}>
        <div className={styles.divider}>
          <span className={styles.dividerText}>{t('login.google.or')}</span>
        </div>
        <p className={styles.googleDisabled}>{t('login.google.unconfigured')}</p>
      </div>
    );
  }

  return (
    <div className={styles.googleSection}>
      <div className={styles.divider}>
        <span className={styles.dividerText}>{t('login.google.or')}</span>
      </div>
      <div
        ref={buttonRef}
        className={styles.googleButtonWrapper}
        aria-label={t('login.google.button')}
      />
    </div>
  );
}
