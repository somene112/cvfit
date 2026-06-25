import apiClient from './apiClient';

/**
 * Learning Roadmap API (Phase 6)
 * Endpoints under /v1/learning/tasks (list/get/update). All routes require
 * Bearer JWT (handled by the apiClient interceptor).
 *
 * Task status values: todo | in_progress | done
 * Priority values:    high | medium | low
 * Task type values:   article | project | practice | interview_prep | profile_evidence
 */

// The backend returns `task_type`; the UI reads `type` (for the icon). Keep both.
function normalizeTask(task) {
  if (!task || typeof task !== 'object') return task;
  return { ...task, type: task.task_type ?? task.type };
}

/**
 * Get the authenticated user's personalised learning roadmap (task list).
 * Returns an empty list (not a 404) when the user has no tasks yet.
 * @param {{ target_job_id?: string, status?: string, priority?: string, task_type?: string }} [params]
 * @returns {Promise<{ items: Array, total: number }>}
 */
export async function getLearningRoadmap(params = {}) {
  const response = await apiClient.get('/v1/learning/tasks', { params });
  const data = response.data || {};
  return { ...data, items: Array.isArray(data.items) ? data.items.map(normalizeTask) : [] };
}

/**
 * Get a single learning task by ID.
 * @param {string} id
 * @returns {Promise<Object>}
 */
export async function getLearningTask(id) {
  const response = await apiClient.get(`/v1/learning/tasks/${id}`);
  return normalizeTask(response.data);
}

/**
 * Update a learning task (e.g. its status).
 * @param {string} id
 * @param {{ status?: 'todo'|'in_progress'|'done' }} payload
 * @returns {Promise<Object>}
 */
export async function updateLearningTask(id, payload) {
  const response = await apiClient.patch(`/v1/learning/tasks/${id}`, payload);
  return normalizeTask(response.data);
}
