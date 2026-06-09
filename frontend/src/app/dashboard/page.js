'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Header from '@/components/dashboard/Header';
import UploadCV from '@/components/dashboard/UploadCV';
import JobDescription from '@/components/dashboard/JobDescription';
import AnalysisProgress from '@/components/dashboard/AnalysisProgress';
import ResultCard from '@/components/dashboard/ResultCard';
import ResultCardV2 from '@/components/dashboard/ResultCardV2';
import EmptyState from '@/components/dashboard/EmptyState';
import ErrorState from '@/components/dashboard/ErrorState';
import ComparisonDashboard from '@/components/results/ComparisonDashboard';
import ReanalysisUpload from '@/components/results/ReanalysisUpload';
import { isResultV2 } from '@/utils/resultHelpers';
import { extractApiError } from '@/utils/errorHelpers';
import { useUploadCV } from '@/hooks/useUploadCV';
import { useJobPolling } from '@/hooks/useJobPolling';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import { createScoreJob, getJobResult, getJobStatus } from '@/services/jobApi';
import { useLanguage } from '@/context/LanguageContext';
import {
  STRICTNESS_OPTIONS,
  LANGUAGE_OPTIONS,
  WORKFLOW_STEPS,
  JOB_STATUS,
} from '@/utils/constants';
import styles from '@/styles/Dashboard.module.css';

function DashboardContent() {
  const { t } = useLanguage();
  const { isAuthChecking } = useRequireAuth();
  const searchParams = useSearchParams();
  const router = useRouter();

  /* ──── State ──── */
  const [jdText, setJdText] = useState('');
  const [targetRole, setTargetRole] = useState('');
  const [language, setLanguage] = useState('en');
  const [strictness, setStrictness] = useState('balanced');

  const [workflowStep, setWorkflowStep] = useState(WORKFLOW_STEPS.IDLE);
  const [jobId, setJobId] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [result, setResult] = useState(null);
  const [previousResult, setPreviousResult] = useState(null);
  const [isComparing, setIsComparing] = useState(false);
  const [workflowError, setWorkflowError] = useState(null);

  const {
    file,
    setFile,
    upload,
    progress: uploadProgress,
    isUploading,
    error: uploadError,
    resetUpload,
  } = useUploadCV();

  const {
    status: jobStatus,
    progress: jobProgress,
    error: pollingError,
    startPolling,
    reset: resetPolling,
  } = useJobPolling(jobId);

  /* ──── Fetch result when job succeeds ──── */
  useEffect(() => {
    if (jobStatus === JOB_STATUS.SUCCEEDED && jobId && accessToken && workflowStep !== WORKFLOW_STEPS.RESULT) {
      (async () => {
        try {
          const data = await getJobResult(jobId, accessToken);
          setResult(data);
          setWorkflowStep(WORKFLOW_STEPS.RESULT);
        } catch (err) {
          const { message } = extractApiError(err, 'Failed to fetch results.');
          setWorkflowError(message);
          setWorkflowStep(WORKFLOW_STEPS.ERROR);
        }
      })();
    }
    if (jobStatus === JOB_STATUS.FAILED && workflowStep !== WORKFLOW_STEPS.ERROR) {
      setWorkflowStep(WORKFLOW_STEPS.ERROR);
      setWorkflowError(pollingError || 'Analysis failed. Please try again.');
    }
  }, [jobStatus, jobId, accessToken, pollingError, workflowStep]);

  /* ──── Load from URL Params (History Link) ──── */
  useEffect(() => {
    const urlJobId = searchParams.get('job_id');
    const urlToken = searchParams.get('access_token');
    const compareWithJobId = searchParams.get('compare_with');
    
    if (urlJobId && !isAuthChecking) {
      setWorkflowStep(WORKFLOW_STEPS.POLLING);
      setJobId(urlJobId);
      if (urlToken) setAccessToken(urlToken);
      
      // If comparing, fetch the previous result immediately
      if (compareWithJobId) {
        (async () => {
          try {
            const prevData = await getJobResult(compareWithJobId, urlToken);
            setPreviousResult(prevData);
            setIsComparing(true);
          } catch (err) {
            console.error('Failed to load previous result for comparison', err);
          }
        })();
      }

      // Clean up URL without reloading page
      const currentUrl = new URL(window.location.href);
      currentUrl.search = '';
      window.history.replaceState({}, document.title, currentUrl.pathname);
    }
  }, [searchParams, isAuthChecking]);

  /* ──── Analyze Handler ──── */
  const handleAnalyze = useCallback(async () => {
    if (!file) {
      alert(t('analyze.alert.noCv'));
      return;
    }
    if (!jdText.trim()) {
      alert(t('analyze.alert.noJd'));
      return;
    }

    setWorkflowError(null);
    setResult(null);

    /* Step 1: Upload CV */
    setWorkflowStep(WORKFLOW_STEPS.UPLOADING);
    const cvFileId = await upload();
    if (!cvFileId) {
      setWorkflowStep(WORKFLOW_STEPS.ERROR);
      setWorkflowError('CV upload failed. Please try again.');
      return;
    }

    /* Step 2: Create Score Job */
    setWorkflowStep(WORKFLOW_STEPS.CREATING_JOB);
    try {
      const jobData = await createScoreJob({
        cv_file_id: cvFileId,
        jd_text: jdText.trim(),
        options: {
          target_role: targetRole.trim() || undefined,
          language,
          strictness,
          output_formats: ['json', 'docx'],
        },
      });

      setJobId(jobData.job_id);
      setAccessToken(jobData.access_token);

      /* Step 3: Start Polling */
      setWorkflowStep(WORKFLOW_STEPS.POLLING);
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to create analysis job.');
      setWorkflowError(message);
      setWorkflowStep(WORKFLOW_STEPS.ERROR);
    }
  }, [file, jdText, targetRole, language, strictness, upload, t]);

  /* ──── Reanalysis Handler ──── */
  const handleReanalysisComplete = useCallback((newResult, newJobId, newAccessToken) => {
    setPreviousResult(result);
    setResult(newResult);
    setJobId(newJobId);
    setAccessToken(newAccessToken);
    setIsComparing(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [result]);

  /* Start polling when jobId is set and we're in polling step */
  useEffect(() => {
    if (workflowStep === WORKFLOW_STEPS.POLLING && jobId) {
      startPolling();
    }
  }, [workflowStep, jobId, startPolling]);

  /* ──── Reset / New Analysis ──── */
  const handleNewAnalysis = useCallback(() => {
    setWorkflowStep(WORKFLOW_STEPS.IDLE);
    setJobId(null);
    setAccessToken(null);
    setResult(null);
    setPreviousResult(null);
    setIsComparing(false);
    setWorkflowError(null);
    setJdText('');
    setTargetRole('');
    setLanguage('en');
    setStrictness('balanced');
    resetUpload();
    resetPolling();
  }, [resetUpload, resetPolling]);

  /* ──── Derived ──── */
  const isAnalyzing = [
    WORKFLOW_STEPS.UPLOADING,
    WORKFLOW_STEPS.CREATING_JOB,
    WORKFLOW_STEPS.POLLING,
  ].includes(workflowStep);

  const showProgress = isAnalyzing || workflowStep === WORKFLOW_STEPS.ERROR;
  const showResult = workflowStep === WORKFLOW_STEPS.RESULT && result;
  const canAnalyze =
    workflowStep === WORKFLOW_STEPS.IDLE || workflowStep === WORKFLOW_STEPS.ERROR;

  const combinedProgress =
    workflowStep === WORKFLOW_STEPS.UPLOADING
      ? Math.round(uploadProgress * 0.2)
      : workflowStep === WORKFLOW_STEPS.CREATING_JOB
        ? 20
        : workflowStep === WORKFLOW_STEPS.POLLING
          ? 20 + Math.round(jobProgress * 0.8)
          : workflowStep === WORKFLOW_STEPS.RESULT
            ? 100
            : 0;

  if (isAuthChecking) {
    return (
      <div className={styles.page}>
        <main className={styles.main}>
          <h1 className={styles.pageTitle}>{t('login.btn.signingIn')}</h1>
        </main>
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <Header />
      <main className={styles.main}>
        <h1 className={styles.pageTitle}>{t('dashboard.title')}</h1>
        <p className={styles.pageSubtitle}>
          {t('dashboard.subtitle')}
        </p>

        {!showResult ? (
          <div className={styles.grid}>
            {/* Upload CV */}
            <UploadCV
              file={file}
              onFileSelect={setFile}
              progress={uploadProgress}
              isUploading={isUploading}
              error={uploadError}
              onRemove={resetUpload}
              disabled={isAnalyzing}
            />

            {/* Job Description */}
            <JobDescription
              value={jdText}
              onChange={setJdText}
              disabled={isAnalyzing}
            />

            {/* Analysis Settings */}
            <div className={styles.settingsCard} id="analysis-settings">
              <div className={styles.settingsHeader}>
                <div className={styles.settingsIcon}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="3" />
                    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                  </svg>
                </div>
                <div>
                  <h2 className={styles.settingsTitle}>{t('settings.title')}</h2>
                  <p className={styles.settingsSubtitle}>{t('settings.subtitle')}</p>
                </div>
              </div>

              <div className={styles.settingsGrid}>
                <div className={styles.fieldGroup}>
                  <label className={styles.fieldLabel} htmlFor="target-role">
                    {t('settings.role.label')}
                  </label>
                  <input
                    id="target-role"
                    className={styles.fieldInput}
                    type="text"
                    placeholder={t('settings.role.placeholder')}
                    value={targetRole}
                    onChange={(e) => setTargetRole(e.target.value)}
                    disabled={isAnalyzing}
                  />
                </div>

                <div className={styles.fieldGroup}>
                  <label className={styles.fieldLabel} htmlFor="language-select">
                    {t('settings.lang.label')}
                  </label>
                  <div className={styles.selectWrapper}>
                    <select
                      id="language-select"
                      className={styles.fieldInput}
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      disabled={isAnalyzing}
                    >
                      {LANGUAGE_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className={styles.fieldGroup}>
                  <label className={styles.fieldLabel} htmlFor="strictness-select">
                    {t('settings.strict.label')}
                  </label>
                  <div className={styles.selectWrapper}>
                    <select
                      id="strictness-select"
                      className={styles.fieldInput}
                      value={strictness}
                      onChange={(e) => setStrictness(e.target.value)}
                      disabled={isAnalyzing}
                    >
                      {STRICTNESS_OPTIONS.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>

            {/* Analyze Button */}
            <button
              className={styles.analyzeButton}
              onClick={handleAnalyze}
              disabled={!canAnalyze || !file || !jdText.trim()}
              id="analyze-button"
            >
              <span className={styles.analyzeButtonContent}>
                {isAnalyzing ? (
                  <>
                    <span className={styles.analyzeSpinner} />
                    {t('analyze.btn.analyzing')}
                  </>
                ) : (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                    </svg>
                    {t('analyze.btn.analyze')}
                  </>
                )}
              </span>
            </button>

            {/* Progress */}
            {showProgress && (
              <AnalysisProgress
                workflowStep={workflowStep}
                jobStatus={jobStatus}
                progress={combinedProgress}
                error={workflowError || pollingError}
              />
            )}
          </div>
        ) : (
          /* Results */
          <div className={styles.resultsWrapper} style={{ display: 'flex', flexDirection: 'column', gap: '2rem', width: '100%' }}>
            {isComparing && previousResult && result && (
              <ComparisonDashboard
                previousResult={previousResult}
                currentResult={result}
              />
            )}
            
            {isResultV2(result) ? (
              <ResultCardV2
                result={result}
                jobId={jobId}
                accessToken={accessToken}
                onNewAnalysis={handleNewAnalysis}
              />
            ) : (
              <ResultCard
                result={result}
                jobId={jobId}
                accessToken={accessToken}
                onNewAnalysis={handleNewAnalysis}
              />
            )}

            {/* Reanalysis Flow below results */}
            <div style={{ marginTop: '1rem' }}>
              <ReanalysisUpload
                jdText={jdText}
                targetRole={targetRole}
                language={language}
                strictness={strictness}
                onReanalysisComplete={handleReanalysisComplete}
                onCompare={() => setIsComparing(true)}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <Suspense fallback={
      <div className={styles.page}>
        <main className={styles.main}>
          <div className={styles.analyzeSpinner} style={{ margin: '0 auto', display: 'block', width: '40px', height: '40px', borderWidth: '4px' }} />
        </main>
      </div>
    }>
      <DashboardContent />
    </Suspense>
  );
}
