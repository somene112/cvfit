/**
 * @typedef {Object} BillingCredits
 * @property {number} analysis
 * @property {number} interview
 * @property {number} cover_letter
 * @property {number} package
 */

/**
 * @typedef {Object} BillingPlan
 * @property {string} plan_code
 * @property {string} name
 * @property {number} amount
 * @property {'VND'} currency
 * @property {string|null} description
 * @property {BillingCredits} credits
 */

/**
 * @typedef {Object} BillingPlansResponse
 * @property {'VND'} currency
 * @property {BillingPlan[]} plans
 */

/**
 * @typedef {Object} BillingUsageResponse
 * @property {string} month
 * @property {string} timezone
 * @property {BillingCredits} free_allowance
 * @property {BillingCredits} used_this_month
 * @property {BillingCredits} free_remaining
 * @property {BillingCredits} remaining_credits
 */

/**
 * @typedef {Object} PaymentOrderSummary
 * @property {string} payment_order_id
 * @property {string} plan_code
 * @property {number} amount
 * @property {'VND'} currency
 * @property {string} status
 * @property {string} created_at
 * @property {string|null} paid_at
 */

/**
 * @typedef {PaymentOrderSummary & {credits_granted: BillingCredits|null}} PaymentOrderDetail
 */

/**
 * @typedef {Object} CheckoutResponse
 * @property {string} payment_order_id
 * @property {string} provider
 * @property {string} plan_code
 * @property {number} amount
 * @property {'VND'} currency
 * @property {'pending'} status
 * @property {string} checkout_url
 * @property {string|null} expires_at
 */

export const BILLING_CREDIT_KEYS = [
  'analysis',
  'interview',
  'cover_letter',
  'package',
];
