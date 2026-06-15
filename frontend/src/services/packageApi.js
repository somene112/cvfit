import apiClient from './apiClient';

/**
 * Application Package API
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 */

/**
 * Generate an application package for the given application.
 * Requires an analysis to be attached first (otherwise returns 422).
 * @param {string} appId
 * @returns {Promise<Object>}
 */
export async function generatePackage(appId) {
  const response = await apiClient.post(`/v1/applications/${appId}/package/generate`);
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
