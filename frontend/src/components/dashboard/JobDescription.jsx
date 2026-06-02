'use client';

import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/JobDescription.module.css';
import { MAX_JD_CHARACTERS } from '@/utils/constants';

export default function JobDescription({ value, onChange, disabled }) {
  const { t } = useLanguage();
  const charCount = value.length;
  const charPercent = (charCount / MAX_JD_CHARACTERS) * 100;

  let counterClass = styles.counter;
  if (charPercent >= 100) {
    counterClass = `${styles.counter} ${styles.counterDanger}`;
  } else if (charPercent >= 80) {
    counterClass = `${styles.counter} ${styles.counterWarning}`;
  }

  return (
    <div className={styles.card} id="job-description-section">
      <div className={styles.cardHeader}>
        <div className={styles.cardIcon}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
        </div>
        <div>
          <h2 className={styles.cardTitle}>{t('jd.title')}</h2>
          <p className={styles.cardSubtitle}>{t('jd.subtitle')}</p>
        </div>
      </div>

      <div className={styles.textareaWrapper}>
        <textarea
          className={styles.textarea}
          id="jd-textarea"
          value={value}
          onChange={(e) => {
            if (e.target.value.length <= MAX_JD_CHARACTERS) {
              onChange(e.target.value);
            }
          }}
          placeholder={t('jd.placeholder')}
          disabled={disabled}
          rows={8}
          aria-label="Job description text"
        />
        <div className={counterClass}>
          <span>{charCount.toLocaleString()} / {MAX_JD_CHARACTERS.toLocaleString()} {t('jd.chars')}</span>
        </div>
      </div>
    </div>
  );
}
