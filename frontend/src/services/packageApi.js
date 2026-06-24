import apiClient from './apiClient';

/**
 * Application Package API
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 */

/**
 * Generate an application package for the given application.
 * Requires an analysis to be attached first (otherwise returns 422).
 * The product is Vietnamese-first, so generated prose defaults to Vietnamese.
 * @param {string} appId
 * @param {string} [language='vi'] - "vi" | "en"
 * @returns {Promise<Object>}
 */
export async function generatePackage(appId, language = 'vi') {
  const response = await apiClient.post(
    `/v1/applications/${appId}/package/generate`,
    null,
    { params: { language } }
  );
  return response.data;
}

/**
 * Get the current package for an application.
 * @param {string} appId
 * @returns {Promise<Object>}
 */
export async function getPackage(appId) {
  const response = await apiClient.get(`/v1/applications/${appId}/package`);
  return response.data;
}
