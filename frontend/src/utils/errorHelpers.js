/**
 * Centralized API Error Extraction
 *
 * Parses Axios / FastAPI error responses to extract user-friendly
 * messages and optional hints. Follows the fallback order:
 *   1. detail.message  (FastAPI structured detail)
 *   2. detail.hint     (FastAPI structured hint)
 *   3. detail          (FastAPI string detail)
 *   4. data.message    (generic API)
 *   5. err.message     (Axios wrapper — only non-generic)
 *   6. HTTP status friendly message
 *   7. fallback string
 */

/**
 * Returns a human-friendly message for common HTTP status codes.
 * @param {number} status
 * @returns {string}
 */
export function getHttpErrorMessage(status) {
  switch (status) {
    case 401:
      return 'Your session has expired. Please log in again.';
    case 403:
      return "You don't have permission to perform this action.";
    case 404:
      return 'The requested resource was not found.';
    case 422:
      return 'The request could not be processed. Please check your input.';
    case 500:
      return 'A server error occurred. Please try again later.';
    case 502:
    case 503:
      return 'The service is temporarily unavailable. Please try again.';
    default:
      return `An error occurred (${status}). Please try again.`;
  }
}

/**
 * Detects whether a 422 error is the "attach analysis first" scenario.
 * Backend signals this when package/cover-letter generation is attempted
 * without an attached analysis.
 * @param {Error|Object} err
 * @returns {boolean}
 */
export function isAnalysisRequiredError(err) {
  const status = err?.response?.status;
  if (status !== 422) return false;
  const data = err?.response?.data;
  const detail = data?.detail;
  // Check structured detail
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    const msg = (detail.message || '').toLowerCase();
    const code = (detail.code || '').toLowerCase();
    return msg.includes('analysis') || code.includes('analysis');
  }
  // Check string detail
  if (typeof detail === 'string') {
    return detail.toLowerCase().includes('analysis');
  }
  return false;
}

/**
 * Extract a user-facing error object from an Axios error.
 * @param {Error|Object} err - Axios error or generic Error
 * @param {string} [fallback='Something went wrong. Please try again.']
 * @returns {{ message: string, hint: string|null }}
 */
export function extractApiError(err, fallback = 'Something went wrong. Please try again.') {
  const data = err?.response?.data;
  const detail = data?.detail;

  // FastAPI structured detail: { message, hint, ... }
  if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
    return {
      message: detail.message || fallback,
      hint: detail.hint || null,
    };
  }

  // FastAPI string detail
  if (typeof detail === 'string' && detail.length > 0) {
    return { message: detail, hint: null };
  }

  // FastAPI validation errors (array of details)
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0];
    const msg = first?.msg || first?.message || fallback;
    const loc = Array.isArray(first?.loc) ? first.loc.join(' → ') : null;
    return {
      message: msg,
      hint: loc ? `Field: ${loc}` : null,
    };
  }

  // Generic data.message
  if (data?.message && typeof data.message === 'string') {
    return { message: data.message, hint: null };
  }

  // data.error
  if (data?.error && typeof data.error === 'string') {
    return { message: data.error, hint: null };
  }

  // Axios error.message — skip generic ones that aren't helpful
  const genericMessages = [
    'Network Error',
    'Request failed with status code',
  ];
  if (err?.message && !genericMessages.some((g) => err.message.startsWith(g))) {
    return { message: err.message, hint: null };
  }

  // If we have a status code, use a friendly HTTP message
  if (err?.response?.status) {
    return {
      message: getHttpErrorMessage(err.response.status),
      hint: null,
    };
  }

  return { message: fallback, hint: null };
}
