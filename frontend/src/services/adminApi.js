import apiClient from './apiClient';

/**
 * Admin Monitoring API (read-only).
 * All routes require a Bearer JWT whose email is in the backend ADMIN_EMAILS
 * allow-list. Non-admins receive 403; the UI treats that as "not an admin".
 * These endpoints only return aggregate metrics — never private user content.
 */

/**
 * Confirm the current user is an admin. Resolves to { is_admin, email } for
 * admins; rejects with a 403 for authenticated non-admins.
 * @returns {Promise<{ is_admin: boolean, email: string }>}
 */
export async function getAdminMe() {
  const response = await apiClient.get('/v1/admin/me');
  return response.data;
}

/**
 * Fetch aggregate system metrics + current feature flags (admin only).
 * @returns {Promise<Object>}
 */
export async function getAdminOverview() {
  const response = await apiClient.get('/v1/admin/overview');
  return response.data;
}

/**
 * Fetch recent, masked, content-free activity metadata (admin only).
 * @param {number} [limit=20]
 * @returns {Promise<{ items: Array, total: number }>}
 */
export async function getAdminRecentActivity(limit = 20) {
  const response = await apiClient.get('/v1/admin/recent-activity', { params: { limit } });
  return response.data;
}
