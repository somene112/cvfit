import apiClient from './apiClient';

/**
 * Target Jobs API (Phase 6)
 * Endpoints under /v1/target-jobs
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 *
 * Status values: saved | analyzing | ready_to_apply | interviewing |
 *                applied | rejected | offer | archived
 */

/**
 * List all target jobs for the authenticated user.
 * @returns {Promise<{ items: Array, total: number }>}
 */
export async function listTargetJobs() {
  const response = await apiClient.get('/v1/target-jobs');
  return response.data;
}

/**
 * Create a new target job.
 * @param {{ job_title: string, company: string, jd_text: string, target_role?: string, source_url?: string }} payload
 * @returns {Promise<Object>}
 */
export async function createTargetJob(payload) {
  const response = await apiClient.post('/v1/target-jobs', payload);
  return response.data;
}

/**
 * Get a single target job by ID.
 * @param {string} id
 * @returns {Promise<Object>}
 */
export async function getTargetJob(id) {
  const response = await apiClient.get(`/v1/target-jobs/${id}`);
  return response.data;
}

/**
 * Update a target job (partial update).
 * @param {string} id
 * @param {Object} payload
 * @returns {Promise<Object>}
 */
export async function updateTargetJob(id, payload) {
  const response = await apiClient.patch(`/v1/target-jobs/${id}`, payload);
  return response.data;
}

/**
 * Delete a target job.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteTargetJob(id) {
  await apiClient.delete(`/v1/target-jobs/${id}`);
}
