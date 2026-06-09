import apiClient from './apiClient';

/**
 * Create a score job for CV analysis.
 * @param {Object} payload
 * @param {string} payload.cv_file_id
 * @param {string} payload.jd_text
 * @param {Object} payload.options
 * @returns {Promise<{job_id: string, access_token: string}>}
 */
export async function createScoreJob(payload) {
  const response = await apiClient.post('/v1/jobs/create-score', payload);
  const data = response.data;
  if (data?.job_id && data?.access_token) {
    try {
      const stored = JSON.parse(localStorage.getItem('cvfit_tokens') || '{}');
      stored[data.job_id] = data.access_token;
      localStorage.setItem('cvfit_tokens', JSON.stringify(stored));
    } catch (err) {
      // Ignore localStorage errors
    }
  }
  return data;
}

/**
 * Retrieve a stored access token for a given job ID.
 * @param {string} jobId
 * @returns {string|null}
 */
export function getStoredAccessToken(jobId) {
  try {
    const stored = JSON.parse(localStorage.getItem('cvfit_tokens') || '{}');
    return stored[jobId] || null;
  } catch {
    return null;
  }
}

/**
 * Poll the status of a job.
 * @param {string} jobId
 * @returns {Promise<{job_id: string, status: string, progress: number, error_message: string|null}>}
 */
export async function getJobStatus(jobId) {
  const response = await apiClient.get(`/v1/jobs/${jobId}`);
  return response.data;
}

/**
 * Get the authenticated user's job history.
 * @returns {Promise<{items: Array}>}
 */
export async function getJobHistory() {
  const response = await apiClient.get('/v1/jobs/history');
  return response.data;
}

/**
 * Get the analysis result for a completed job.
 * @param {string} jobId
 * @param {string} accessToken
 * @returns {Promise<Object>}
 */
export async function getJobResult(jobId, accessToken) {
  const params = accessToken ? { access_token: accessToken } : {};
  const response = await apiClient.get(`/v1/jobs/${jobId}/result`, { params });
  return response.data;
}

/**
 * Get report metadata for a completed job.
 * @param {string} jobId
 * @param {string} accessToken
 * @returns {Promise<Object>}
 */
export async function getReportMetadata(jobId, accessToken) {
  const params = accessToken ? { access_token: accessToken } : {};
  const response = await apiClient.get(`/v1/jobs/${jobId}/report`, { params });
  return response.data;
}

/**
 * Download the report file (DOCX).
 * @param {string} jobId
 * @param {string} accessToken
 * @returns {Promise<Blob>}
 */
export async function downloadReport(jobId, accessToken) {
  const response = await apiClient.get(`/v1/jobs/${jobId}/report/download`, {
    params: { access_token: accessToken },
    responseType: 'blob',
  });
  return response.data;
}
