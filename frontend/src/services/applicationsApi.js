import apiClient from './apiClient';

/**
 * Applications API
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 */

/**
 * List all applications for the authenticated user.
 * @returns {Promise<{ items: Array, total: number }>}
 */
export async function listApplications() {
  const response = await apiClient.get('/v1/applications');
  return response.data;
}

/**
 * Create a new application.
 * @param {{ company_name: string, role_title: string, job_description: string, notes?: string }} payload
 * @returns {Promise<Object>}
 */
export async function createApplication(payload) {
  const response = await apiClient.post('/v1/applications', payload);
  return response.data;
}

/**
 * Get a single application by ID.
 * @param {string} id
 * @returns {Promise<Object>}
 */
export async function getApplication(id) {
  const response = await apiClient.get(`/v1/applications/${id}`);
  return response.data;
}

/**
 * Update an application (partial update).
 * @param {string} id
 * @param {Object} payload
 * @returns {Promise<Object>}
 */
export async function updateApplication(id, payload) {
  const response = await apiClient.patch(`/v1/applications/${id}`, payload);
  return response.data;
}

/**
 * Delete an application.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteApplication(id) {
  await apiClient.delete(`/v1/applications/${id}`);
}

/**
 * Attach an existing analysis (job) to an application.
 * @param {string} appId - Application ID
 * @param {string} jobId - Job ID from the score analysis
 * @returns {Promise<Object>}
 */
export async function attachAnalysis(appId, jobId) {
  const response = await apiClient.post(`/v1/applications/${appId}/attach-analysis`, {
    job_id: jobId,
  });
  return response.data;
}
