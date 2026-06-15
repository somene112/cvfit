import apiClient from './apiClient';

/**
 * Cover Letter API
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 */

/**
 * Generate a cover letter for the given application.
 * Requires an analysis to be attached first (otherwise returns 422).
 * @param {string} appId
 * @returns {Promise<Object>}
 */
export async function generateCoverLetter(appId) {
  const response = await apiClient.post(`/v1/applications/${appId}/cover-letter/generate`);
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
 * Update (save) the cover letter text.
 * @param {string} appId
 * @param {string} text - The edited cover letter text
 * @returns {Promise<Object>}
 */
export async function updateCoverLetter(appId, text) {
  const response = await apiClient.patch(`/v1/applications/${appId}/cover-letter`, {
    text,
  });
  return response.data;
}
