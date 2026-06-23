import apiClient from './apiClient';

/** @returns {Promise<import('@/types/billing').BillingPlansResponse>} */
export async function getBillingPlans() {
  const response = await apiClient.get('/v1/billing/plans');
  return response.data;
}

/** @returns {Promise<import('@/types/billing').BillingUsageResponse>} */
export async function getBillingUsage() {
  const response = await apiClient.get('/v1/billing/usage');
  return response.data;
}

/** @returns {Promise<{orders: import('@/types/billing').PaymentOrderSummary[]}>} */
export async function getBillingOrders() {
  const response = await apiClient.get('/v1/billing/orders');
  return response.data;
}

/**
 * @param {string} orderId
 * @returns {Promise<import('@/types/billing').PaymentOrderDetail>}
 */
export async function getBillingOrder(orderId) {
  const response = await apiClient.get(`/v1/billing/orders/${encodeURIComponent(orderId)}`);
  return response.data;
}

/**
 * Checkout accepts only a backend-owned plan identifier. Amount, currency,
 * status, user, provider, and credits are intentionally never sent.
 * @param {string} planCode
 * @returns {Promise<import('@/types/billing').CheckoutResponse>}
 */
export async function createBillingCheckout(planCode) {
  const response = await apiClient.post('/v1/billing/checkout', {
    plan_code: planCode,
  });
  return response.data;
}
