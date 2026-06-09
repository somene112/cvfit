'use client';

import { useRef, useState, useCallback } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import { uploadCV } from '@/services/cvApi';
import { createScoreJob, getJobStatus, getJobResult } from '@/services/jobApi';
import { extractApiError } from '@/utils/errorHelpers';
import { ACCEPTED_EXTENSIONS, JOB_STATUS, POLL_INTERVAL_MS } from '@/utils/constants';
import styles from '@/styles/ReanalysisUpload.module.css';

const STATES = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  ANALYZING: 'analyzing',
  SUCCESS: 'success',
  ERROR: 'error',
};

/**
 * ReanalysisUpload — Phase 4 Re-upload Flow
 *
 * Allows user to upload a revised CV and re-run analysis
 * against the same JD text. Shows loading/success/error states.
 */
export default function ReanalysisUpload({
  jdText,
  targetRole,
  language,
  strictness,
  onReanalysisComplete,
  onCompare,
}) {
  const { t } = useLanguage();
  const fileInputRef = useRef(null);
  const [flowState, setFlowState] = useState(STATES.IDLE);
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState(null);
  const [errorHint, setErrorHint] = useState(null);

  const handleFile = useCallback(async (file) => {
    // Validate
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      setError(t('upload.error.format'));
      setFlowState(STATES.ERROR);
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError(t('upload.error.size'));
      setFlowState(STATES.ERROR);
      return;
    }

    try {
      // Step 1: Upload CV
      setFlowState(STATES.UPLOADING);
      setError(null);
      setErrorHint(null);

      const uploadData = await uploadCV(file, () => {});
      const cvFileId = uploadData.cv_file_id;

      // Step 2: Create score job
      setFlowState(STATES.ANALYZING);
      const jobData = await createScoreJob({
        cv_file_id: cvFileId,
        jd_text: jdText,
        options: {
          target_role: targetRole || undefined,
          language: language || 'en',
          strictness: strictness || 'balanced',
          output_formats: ['json', 'docx'],
        },
      });

      // Step 3: Poll until complete
      const result = await pollUntilDone(jobData.job_id, jobData.access_token);
      setFlowState(STATES.SUCCESS);

      if (onReanalysisComplete) {
        onReanalysisComplete(result, jobData.job_id, jobData.access_token);
      }
    } catch (err) {
      const { message, hint } = extractApiError(err, t('phase4.reanalysis.error'));
      setError(message);
      setErrorHint(hint);
      setFlowState(STATES.ERROR);
    }
  }, [jdText, targetRole, language, strictness, onReanalysisComplete, t]);

  const pollUntilDone = async (jobId, accessToken) => {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const statusData = await getJobStatus(jobId);
          if (statusData.status === JOB_STATUS.SUCCEEDED) {
            const result = await getJobResult(jobId, accessToken);
            resolve(result);
          } else if (statusData.status === JOB_STATUS.FAILED) {
            reject(new Error(statusData.error_message || 'Analysis failed.'));
          } else {
            setTimeout(poll, POLL_INTERVAL_MS);
          }
        } catch (err) {
          reject(err);
        }
      };
      poll();
    });
  };

  const handleDragOver = (e) => { e.preventDefault(); setIsDragOver(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setIsDragOver(false); };
  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer?.files?.[0];
    if (file) handleFile(file);
  };
  const handleClick = () => fileInputRef.current?.click();
  const handleInputChange = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };
  const handleReset = () => {
    setFlowState(STATES.IDLE);
    setError(null);
    setErrorHint(null);
  };

  return (
    <div className={styles.reanalysisContainer} id="reanalysis-upload">
      <div className={styles.header}>
        <div className={styles.headerIcon}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
          </svg>
        </div>
        <div>
          <h2 className={styles.headerTitle}>{t('phase4.reanalysis.title')}</h2>
          <p className={styles.headerSubtitle}>{t('phase4.reanalysis.subtitle')}</p>
        </div>
      </div>

      {/* Idle — show dropzone */}
      {flowState === STATES.IDLE && (
        <div
          className={`${styles.dropzone} ${isDragOver ? styles.dropzoneActive : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
          role="button"
          tabIndex={0}
          id="reanalysis-dropzone"
        >
          <input
            ref={fileInputRef}
            type="file"
            className={styles.hiddenInput}
            accept=".pdf,.docx"
            onChange={handleInputChange}
          />
          <div className={styles.dropzoneIcon}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <p className={styles.dropzoneText}>
            {t('phase4.reanalysis.dropzone').split(',')[0]}, <span>{t('phase4.reanalysis.dropzone').split(',')[1] || 'browse'}</span>
          </p>
        </div>
      )}

      {/* Uploading / Analyzing */}
      {(flowState === STATES.UPLOADING || flowState === STATES.ANALYZING) && (
        <div className={styles.statusContainer}>
          <div className={styles.spinner} />
          <span className={styles.statusText}>
            {flowState === STATES.UPLOADING
              ? t('phase4.reanalysis.uploading')
              : t('phase4.reanalysis.analyzing')}
          </span>
        </div>
      )}

      {/* Success */}
      {flowState === STATES.SUCCESS && (
        <div className={styles.statusContainer}>
          <div className={styles.successIcon}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          </div>
          <span className={styles.successText}>{t('phase4.reanalysis.success')}</span>
          {onCompare && (
            <button className={styles.compareButton} onClick={onCompare} id="reanalysis-compare-btn">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" />
                <line x1="12" y1="20" x2="12" y2="4" />
                <line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              {t('phase4.reanalysis.compareBtn')}
            </button>
          )}
        </div>
      )}

      {/* Error */}
      {flowState === STATES.ERROR && (
        <div className={styles.errorContainer}>
          <span className={styles.errorMessage}>{error}</span>
          {errorHint && <span className={styles.errorHint}>Hint: {errorHint}</span>}
          <button className={styles.retryButton} onClick={handleReset}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="14" height="14">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
            {t('resultV2.error.retry')}
          </button>
        </div>
      )}
    </div>
  );
}
