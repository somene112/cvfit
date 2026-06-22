import apiClient from './apiClient';

/**
 * Usage & Plan API (Phase 6)
 * Endpoint: GET /v1/usage
 * Requires Bearer JWT (handled automatically by apiClient interceptor).
 *
 * No payment / checkout functionality — UI only shows plan info and usage meters.
 */

/**
 * Get the authenticated user's current plan and monthly usage metrics.
 * @returns {Promise<{
 *   plan: { name: string, tier: string },
 *   usage: {
 *     analyses: { used: number, limit: number },
 *     interview_answers: { used: number, limit: number },
 *     cover_letters: { used: number, limit: number },
 *     application_packages: { used: number, limit: number },
 *     share_links: { used: number, limit: number }
 *   },
 *   period_start: string,
 *   period_end: string
 * }>}
 */
export async function getUsage() {
  const response = await apiClient.get('/v1/usage');
  return response.data;
}
