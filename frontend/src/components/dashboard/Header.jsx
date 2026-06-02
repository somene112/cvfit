'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import LanguageSwitcher from '@/components/common/LanguageSwitcher';
import styles from '@/styles/Header.module.css';

export default function Header() {
  const router = useRouter();
  const { t } = useLanguage();
  const [userName, setUserName] = useState('');
  const [userInitial, setUserInitial] = useState('U');

  useEffect(() => {
    try {
      const userData = localStorage.getItem('user');
      if (userData) {
        const parsed = JSON.parse(userData);
        const name = parsed.name || parsed.email || 'User';
        setUserName(name);
        setUserInitial(name.charAt(0).toUpperCase());
      }
    } catch {
      setUserName('User');
      setUserInitial('U');
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  return (
    <header className={styles.header} id="dashboard-header">
      <div className={styles.left}>
        <div className={styles.logoIcon}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
          </svg>
        </div>
        <span className={styles.productName}>{t('landing.logo')}</span>
        <span className={styles.productBadge}>{t('header.badge')}</span>
      </div>

      <div className={styles.right}>
        <LanguageSwitcher />
        <div className={styles.userInfo}>
          <div className={styles.avatar}>{userInitial}</div>
          <span className={styles.userName}>{userName}</span>
        </div>
        <button
          className={styles.logoutButton}
          onClick={handleLogout}
          id="logout-button"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
          {t('header.logout')}
        </button>
      </div>
    </header>
  );
}
