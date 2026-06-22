import apiClient from './apiClient';

/**
 * Shareable Readiness API (Phase 6)
 * Endpoints under /v1/share
 *
 * Owner endpoints require Bearer JWT.
 * Public endpoint (getPublicShare) is unauthenticated.
 *
 * Visibility options:
 *   summary_only | include_score_breakdown | include_package |
 *   include_cover_letter | include_learning_roadmap |
 *   hide_raw_cv | hide_raw_jd
 */

/**
 * Get the share settings for an application.
 * @param {string} applicationId
 * @returns {Promise<{ token: string|null, expires_at: string|null, visibility: string[], is_active: boolean }>}
 */
export async function getShareSettings(applicationId) {
  const response = await apiClient.get(`/v1/share/application/${applicationId}`);
  return response.data;
}

/**
 * Create or regenerate a share link for an application.
 * @param {string} applicationId
 * @param {{ visibility: string[], expires_in_days?: number }} payload
 * @returns {Promise<{ token: string, share_url: string, expires_at: string|null }>}
 */
export async function createShareLink(applicationId, payload) {
  const response = await apiClient.post(`/v1/share/application/${applicationId}`, payload);
  return response.data;
}

/**
 * Revoke the share link for an application.
 * @param {string} applicationId
 * @returns {Promise<void>}
 */
export async function revokeShareLink(applicationId) {
  await apiClient.delete(`/v1/share/application/${applicationId}`);
}

/**
 * Get the public share view by token (unauthenticated).
 * Never returns raw CV, raw JD, tokens, or private IDs.
 * @param {string} token
 * @returns {Promise<Object>}
 */
export async function getPublicShare(token) {
  const response = await apiClient.get(`/v1/share/${token}`);
  return response.data;
}
