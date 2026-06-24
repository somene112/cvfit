import apiClient from './apiClient';

/**
 * Interview Sessions V2 API (Phase 6)
 * Endpoints under /v1/interview/sessions
 * Separate from the per-application interview at /v1/applications/:id/interview
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 *
 * Question types: technical | behavioral | project | HR | gap_check
 * Difficulty:     easy | medium | hard
 * Rubric keys:    relevance | evidence | clarity | structure | confidence | risk
 */

/**
 * List all interview sessions for the authenticated user.
 * @returns {Promise<{ items: Array, total: number }>}
 */
export async function listSessions() {
  const response = await apiClient.get('/v1/interview/sessions');
  return response.data;
}

/**
 * Create a new interview session.
 * @param {{ question_type: string, difficulty: string, target_job_id?: string, application_id?: string }} payload
 * @returns {Promise<Object>}
 */
export async function createSession(payload) {
  const response = await apiClient.post('/v1/interview/sessions', payload);
  return response.data;
}

/**
 * Get a single session with its questions and answers.
 * @param {string} id
 * @returns {Promise<Object>}
 */
export async function getSession(id) {
  const response = await apiClient.get(`/v1/interview/sessions/${id}`);
  return response.data;
}

/**
 * Submit an answer for a question in a session.
 * The product is Vietnamese-first, so feedback prose defaults to Vietnamese.
 * @param {string} sessionId
 * @param {{ question_id: string, answer_text: string }} payload
 * @param {string} [language='vi'] - "vi" | "en"
 * @returns {Promise<Object>} feedback object with rubric breakdown
 */
export async function submitSessionAnswer(sessionId, payload, language = 'vi') {
  const response = await apiClient.post(
    `/v1/interview/sessions/${sessionId}/answers`,
    { ...payload, language }
  );
  return response.data;
}
