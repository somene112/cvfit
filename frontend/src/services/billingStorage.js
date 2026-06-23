const PENDING_BILLING_ORDER_KEY = 'pending_billing_order_id';
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export function isSafePaymentOrderId(value) {
  return typeof value === 'string' && UUID_PATTERN.test(value);
}

export function storePendingBillingOrderId(orderId) {
  if (typeof window === 'undefined' || !isSafePaymentOrderId(orderId)) return false;
  try {
    sessionStorage.setItem(PENDING_BILLING_ORDER_KEY, orderId);
    return true;
  } catch {
    return false;
  }
}

export function getPendingBillingOrderId() {
  if (typeof window === 'undefined') return null;
  try {
    const orderId = sessionStorage.getItem(PENDING_BILLING_ORDER_KEY);
    return isSafePaymentOrderId(orderId) ? orderId : null;
  } catch {
    return null;
  }
}

export function clearPendingBillingOrderId() {
  if (typeof window === 'undefined') return;
  try {
    sessionStorage.removeItem(PENDING_BILLING_ORDER_KEY);
  } catch {
    // Storage can be unavailable in privacy-restricted browser contexts.
  }
}
