import apiClient from './apiClient';

/**
 * Interview Practice API
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 */

/**
 * Get interview questions for an application.
 * @param {string} appId
 * @returns {Promise<{ questions: Array }>}
 */
export async function getInterviewQuestions(appId) {
  const response = await apiClient.get(`/v1/applications/${appId}/interview/questions`);
  return response.data;
}

/**
 * Submit an answer to an interview question.
 * @param {string} appId
 * @param {{ question_id: string, question: string, answer_text: string }} payload
 * @returns {Promise<Object>} feedback object
 */
export async function submitAnswer(appId, payload) {
  const response = await apiClient.post(`/v1/applications/${appId}/interview/answer`, payload);
  return response.data;
}
