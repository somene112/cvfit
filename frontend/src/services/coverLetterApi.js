import apiClient from './apiClient';

/**
 * Cover Letter API
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 */

/**
 * Generate a cover letter for the given application.
 * Requires an analysis to be attached first (otherwise returns 422).
 * The product is Vietnamese-first, so generated prose defaults to Vietnamese.
 * @param {string} appId
 * @param {string} [language='vi'] - "vi" | "en"
 * @returns {Promise<Object>}
 */
export async function generateCoverLetter(appId, language = 'vi') {
  const response = await apiClient.post(
    `/v1/applications/${appId}/cover-letter/generate`,
    null,
    { params: { language } }
  );
  return response.data;
}

/**
 * Get the current cover letter for an application.
 * @param {string} appId
 * @returns {Promise<Object>}
 */
export async function getCoverLetter(appId) {
  const response = await apiClient.get(`/v1/applications/${appId}/cover-letter`);
  return response.data;
}

/**
 * Update cover letter sections.
 * @param {string} appId
 * @param {{ opening?: string, why_role_company?: string, contribution_fit?: string, closing?: string, review_notes?: string[] }} fields
 * @returns {Promise<Object>}
 */
export async function updateCoverLetter(appId, fields) {
  const response = await apiClient.patch(`/v1/applications/${appId}/cover-letter`, fields);
  return response.data;
}
