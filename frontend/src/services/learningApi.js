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

/**
 * Return the job_id of the user's most recent SUCCEEDED analysis, or null.
 * Uses the existing /v1/jobs/history (safe metadata only — no raw CV/JD).
 */
export async function getLatestSuccessfulAnalysisId() {
  const response = await apiClient.get('/v1/jobs/history');
  const items = Array.isArray(response.data?.items) ? response.data.items : [];
  const latest = items.find((j) => j.status === 'succeeded');
  return latest?.job_id ?? null;
}

/**
 * Generate (and persist) a learning roadmap from an analysis/application/target
 * job. Vietnamese by default for the VI-first product.
 * @param {{ analysis_job_id?: string, application_id?: string, target_job_id?: string, language?: string }} params
 * @returns {Promise<{ tasks: Array, total: number, limitations: string }>}
 */
export async function generateRoadmap(params = {}) {
  const { analysis_job_id, application_id, target_job_id, language = 'vi' } = params;
  const body = { language };
  if (analysis_job_id) body.analysis_job_id = analysis_job_id;
  if (application_id) body.application_id = application_id;
  if (target_job_id) body.target_job_id = target_job_id;
  const response = await apiClient.post('/v1/learning/roadmaps/generate', body);
  return response.data;
}
