'use client';

import { useMemo } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/ScoreCircle.module.css';

export default function ScoreCircle({ score = 0 }) {
  const { t } = useLanguage();
  const radius = 75;
  const circumference = 2 * Math.PI * radius;

  const { offset, color, glowColor, matchText, matchClass } = useMemo(() => {
    const clampedScore = Math.min(100, Math.max(0, score));
    const calculatedOffset = circumference - (clampedScore / 100) * circumference;

    let strokeColor, glow, text, cls;
    if (clampedScore >= 75) {
      strokeColor = '#10B981';
      glow = 'rgba(16, 185, 129, 0.4)';
      text = t('result.score.high');
      cls = styles.matchHigh;
    } else if (clampedScore >= 50) {
      strokeColor = '#F59E0B';
      glow = 'rgba(245, 158, 11, 0.4)';
      text = t('result.score.medium');
      cls = styles.matchMedium;
    } else {
      strokeColor = '#EF4444';
      glow = 'rgba(239, 68, 68, 0.4)';
      text = t('result.score.low');
      cls = styles.matchLow;
    }

    return { offset: calculatedOffset, color: strokeColor, glowColor: glow, matchText: text, matchClass: cls };
  }, [score, circumference, t]);

  return (
    <div className={styles.container} id="score-circle">
      <div className={styles.circleWrapper}>
        <svg className={styles.svg} viewBox="0 0 170 170">
          <circle
            className={styles.trackCircle}
            cx="85"
            cy="85"
            r={radius}
          />
          <circle
            className={styles.progressCircle}
            cx="85"
            cy="85"
            r={radius}
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{
              '--glow-color': glowColor,
              '--circumference': circumference,
              '--offset': offset,
              animation: `drawCircle 1.5s ease-out forwards`,
            }}
          />
        </svg>
        <div className={styles.scoreDisplay}>
          <span className={styles.scoreValue} style={{ color }}>
            {Math.round(score)}
            <span className={styles.scoreUnit}>%</span>
          </span>
          <span className={styles.scoreLabel}>{t('result.score.label')}</span>
        </div>
      </div>
      <span className={`${styles.matchLabel} ${matchClass}`}>{matchText}</span>
    </div>
  );
}
