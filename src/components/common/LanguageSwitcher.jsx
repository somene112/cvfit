'use client';

import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/LanguageSwitcher.module.css';

export default function LanguageSwitcher() {
  const { lang, changeLanguage } = useLanguage();

  return (
    <div className={styles.toggleContainer}>
      <button
        className={`${styles.toggleBtn} ${lang === 'vi' ? styles.active : ''}`}
        onClick={() => changeLanguage('vi')}
        aria-label="Tiếng Việt"
      >
        VI
      </button>
      <button
        className={`${styles.toggleBtn} ${lang === 'en' ? styles.active : ''}`}
        onClick={() => changeLanguage('en')}
        aria-label="English"
      >
        EN
      </button>
    </div>
  );
}
