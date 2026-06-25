import apiClient from './apiClient';

/**
 * Help Assistant API (Phase 6) — intent-based, NOT free-form chat.
 * Backend endpoints:
 *   GET  /v1/help/suggestions   → { suggestions: [{intent,label,recommended_actions}], limitations }
 *   POST /v1/help/assistant     → { intent, answer, based_on, recommended_actions, limitations, fallback_used }
 * Bearer JWT is handled by the apiClient interceptor. No LLM / external calls.
 * Only safe owned-object references are sent as context — never raw CV/JD/answer text.
 */

export const VALID_INTENTS = [
  'next_best_action',
  'explain_score',
  'explain_gap',
  'suggest_learning',
  'suggest_interview_practice',
  'explain_application_status',
  'help_product_usage',
];

const CONTEXT_KEYS = ['target_job_id', 'application_id', 'analysis_job_id', 'task_id', 'session_id'];

/**
 * Load the context-aware suggestion chips (Vietnamese labels by default).
 */
export async function getSuggestions(language = 'vi') {
  const response = await apiClient.get('/v1/help/suggestions', { params: { language } });
  return response.data;
}

/**
 * Ask the assistant for a specific supported intent.
 * @param {{ intent: string, context?: object, language?: string }} params
 */
export async function askAssistant({ intent, context = {}, language = 'vi' }) {
  const body = { intent, language };
  CONTEXT_KEYS.forEach((key) => {
    if (context[key]) body[key] = context[key];
  });
  const response = await apiClient.post('/v1/help/assistant', body);
  return response.data;
}
