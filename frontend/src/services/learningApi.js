import apiClient from './apiClient';

/**
 * Learning Roadmap API (Phase 6)
 * Endpoints under /v1/learning
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 *
 * Task status values: todo | in_progress | done
 * Priority values:    high | medium | low
 * Task type values:   article | project | practice | interview_prep | profile_evidence
 */

/**
 * Get the authenticated user's personalised learning roadmap.
 * @param {{ job_id?: string, application_id?: string }} [params]
 * @returns {Promise<{ items: Array, categories: Array }>}
 */
export async function getLearningRoadmap(params = {}) {
  const response = await apiClient.get('/v1/learning', { params });
  return response.data;
}

/**
 * Get a single learning task by ID.
 * @param {string} id
 * @returns {Promise<Object>}
 */
export async function getLearningTask(id) {
  const response = await apiClient.get(`/v1/learning/${id}`);
  return response.data;
}

/**
 * Update the status of a learning task.
 * @param {string} id
 * @param {{ status: 'todo'|'in_progress'|'done' }} payload
 * @returns {Promise<Object>}
 */
export async function updateLearningTask(id, payload) {
  const response = await apiClient.patch(`/v1/learning/${id}`, payload);
  return response.data;
}
