'use client';

import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/AnalysisProgress.module.css';
import { JOB_STATUS } from '@/utils/constants';

function getStepState(stepKey, workflowStep, jobStatus) {
  if (stepKey === 'upload') {
    if (workflowStep === 'uploading') return 'active';
    if (['creating_job', 'polling', 'result'].includes(workflowStep)) return 'completed';
    if (workflowStep === 'error') return 'failed';
    return 'pending';
  }
  if (stepKey === 'analyze') {
    if (['creating_job', 'polling'].includes(workflowStep)) {
      if (jobStatus === JOB_STATUS.FAILED) return 'failed';
      return 'active';
    }
    if (workflowStep === 'result') return 'completed';
    if (workflowStep === 'error') return 'failed';
    return 'pending';
  }
  if (stepKey === 'complete') {
    if (workflowStep === 'result') return 'completed';
    if (workflowStep === 'error' || jobStatus === JOB_STATUS.FAILED) return 'failed';
    return 'pending';
  }
  return 'pending';
}

function getStatusBadgeClass(status) {
  switch (status) {
    case JOB_STATUS.QUEUED: return styles.statusQueued;
    case JOB_STATUS.RUNNING: return styles.statusRunning;
    case JOB_STATUS.SUCCEEDED: return styles.statusSucceeded;
    case JOB_STATUS.FAILED: return styles.statusFailed;
    default: return styles.statusQueued;
  }
}

function getProgressBarClass(status) {
  if (status === JOB_STATUS.SUCCEEDED) return `${styles.progressBarFill} ${styles.progressBarFillSuccess}`;
  if (status === JOB_STATUS.FAILED) return `${styles.progressBarFill} ${styles.progressBarFillFailed}`;
  return styles.progressBarFill;
}

export default function AnalysisProgress({ workflowStep, jobStatus, progress, error }) {
  const { t } = useLanguage();
  const displayProgress = jobStatus === JOB_STATUS.SUCCEEDED ? 100 : progress;

  const STEPS = [
    { key: 'upload', label: t('progress.step1'), number: 1 },
    { key: 'analyze', label: t('progress.step2'), number: 2 },
    { key: 'complete', label: t('progress.step3'), number: 3 },
  ];

  return (
    <div className={styles.card} id="analysis-progress-section">
      <h2 className={styles.title}>{t('progress.title')}</h2>

      <div className={styles.steps}>
        {STEPS.map((step) => {
          const state = getStepState(step.key, workflowStep, jobStatus);
          let stepClass = styles.step;
          if (state === 'active') stepClass = `${styles.step} ${styles.stepActive}`;
          if (state === 'completed') stepClass = `${styles.step} ${styles.stepCompleted}`;
          if (state === 'failed') stepClass = `${styles.step} ${styles.stepFailed}`;

          return (
            <div key={step.key} className={stepClass}>
              <div className={styles.stepCircle}>
                {state === 'completed' ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : state === 'failed' ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                ) : (
                  step.number
                )}
              </div>
              <span className={styles.stepLabel}>{step.label}</span>
            </div>
          );
        })}
      </div>

      <div className={styles.progressWrapper}>
        <div className={styles.progressBarTrack}>
          <div
            className={getProgressBarClass(jobStatus)}
            style={{ width: `${displayProgress}%` }}
          />
        </div>
        <div className={styles.progressInfo}>
          <span className={styles.progressPercent}>{displayProgress}%</span>
          {jobStatus && (
            <span className={`${styles.statusBadge} ${getStatusBadgeClass(jobStatus)}`}>
              <span className={styles.statusDot} />
              {jobStatus}
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className={styles.errorContainer} role="alert" id="analysis-error">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p>{error}</p>
        </div>
      )}
    </div>
  );
}
