'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { getJobStatus } from '@/services/jobApi';
import { JOB_STATUS, POLL_INTERVAL_MS } from '@/utils/constants';

export function useJobPolling(jobId) {
  const [status, setStatus] = useState(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  const intervalRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const startPolling = useCallback(() => {
    if (!jobId) return;

    setIsPolling(true);
    setError(null);
    setStatus(JOB_STATUS.QUEUED);
    setProgress(0);

    const poll = async () => {
      try {
        const data = await getJobStatus(jobId);
        setStatus(data.status);
        setProgress(data.progress || 0);

        if (data.status === JOB_STATUS.SUCCEEDED || data.status === JOB_STATUS.FAILED) {
          if (data.status === JOB_STATUS.FAILED) {
            setError(data.error_message || 'Analysis failed.');
          }
          stopPolling();
        }
      } catch (err) {
        const message =
          err.response?.data?.message || err.message || 'Failed to check job status.';
        setError(message);
        stopPolling();
      }
    };

    poll();
    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);
  }, [jobId, stopPolling]);

  const reset = useCallback(() => {
    stopPolling();
    setStatus(null);
    setProgress(0);
    setError(null);
  }, [stopPolling]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    status,
    progress,
    error,
    isPolling,
    startPolling,
    stopPolling,
    reset,
  };
}
