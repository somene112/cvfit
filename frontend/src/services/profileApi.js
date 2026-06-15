import apiClient from './apiClient';

/**
 * Career Profile / Evidence Vault API
 * All routes require Bearer JWT (handled automatically by apiClient interceptor).
 */

/**
 * Get the authenticated user's career profile overview.
 * @returns {Promise<Object>}
 */
export async function getProfile() {
  const response = await apiClient.get('/v1/profile');
  return response.data;
}

/**
 * Get all evidence items for the user (skills, projects, achievements).
 * @returns {Promise<{ items: Array }>}
 */
export async function getEvidence() {
  const response = await apiClient.get('/v1/profile/items');
  return response.data;
}

/**
 * Create a new evidence item.
 * @param {{ type: 'skill'|'project'|'achievement', title: string, description?: string, tags?: string[] }} payload
 * @returns {Promise<Object>}
 */
export async function createEvidence(payload) {
  const response = await apiClient.post('/v1/profile/items', payload);
  return response.data;
}

/**
 * Update an evidence item (partial update).
 * @param {string} id
 * @param {Object} payload
 * @returns {Promise<Object>}
 */
export async function updateEvidence(id, payload) {
  const response = await apiClient.patch(`/v1/profile/items/${id}`, payload);
  return response.data;
}

/**
 * Delete an evidence item.
 * @param {string} id
 * @returns {Promise<void>}
 */
export async function deleteEvidence(id) {
  await apiClient.delete(`/v1/profile/items/${id}`);
}
