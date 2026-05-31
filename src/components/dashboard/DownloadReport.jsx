'use client';

import { useState } from 'react';
import { downloadReport } from '@/services/jobApi';
import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/DownloadReport.module.css';

export default function DownloadReport({ jobId, accessToken }) {
  const { t } = useLanguage();
  const [isDownloading, setIsDownloading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);

  const handleDownload = async () => {
    if (!jobId || !accessToken) return;

    setIsDownloading(true);
    setIsSuccess(false);

    try {
      const blob = await downloadReport(jobId, accessToken);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `cv-analysis-report-${jobId}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      setIsSuccess(true);
      setTimeout(() => setIsSuccess(false), 3000);
    } catch (err) {
      console.error('Download failed:', err);
      alert(t('download.error'));
    } finally {
      setIsDownloading(false);
    }
  };

  const buttonClass = isSuccess
    ? `${styles.button} ${styles.successState}`
    : styles.button;

  return (
    <button
      className={buttonClass}
      onClick={handleDownload}
      disabled={isDownloading || !jobId || !accessToken}
      id="download-report-button"
    >
      {isDownloading ? (
        <>
          <span className={styles.spinner} />
          {t('download.btn.downloading')}
        </>
      ) : isSuccess ? (
        <>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          {t('download.btn.downloaded')}
        </>
      ) : (
        <>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          {t('download.btn.download')}
        </>
      )}
    </button>
  );
}
