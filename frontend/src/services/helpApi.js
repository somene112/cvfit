import apiClient from './apiClient';

/**
 * Help Assistant API (Phase 6)
 * Endpoint: POST /v1/help/ask
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 *
 * The assistant answer shape:
 * {
 *   answer: string,
 *   limitations: string[],
 *   based_on: string[],
 *   actions: { type: string, label: string, href: string }[]
 * }
 */

/**
 * Ask the AI help assistant a question with optional context.
 * @param {{
 *   prompt: string,
 *   context?: {
 *     target_job_id?: string,
 *     application_id?: string,
 *     analysis_job_id?: string
 *   }
 * }} payload
 * @returns {Promise<{ answer: string, limitations: string[], based_on: string[], actions: Array }>}
 */
export async function askAssistant(payload) {
  const response = await apiClient.post('/v1/help/ask', payload);
  return response.data;
}
