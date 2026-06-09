/**
 * Centralized API Error Extraction
 *
 * Parses Axios / FastAPI error responses to extract user-friendly
 * messages and optional hints. Follows the fallback order:
 *   1. detail.message  (FastAPI structured detail)
 *   2. detail          (FastAPI string detail)
 *   3. data.message    (generic API)
 *   4. err.message     (Axios wrapper — only non-generic)
 *   5. fallback string
 */

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

  // If we have a status code, include it in the message
  if (err?.response?.status) {
    return {
      message: `${fallback} (Error ${err.response.status})`,
      hint: null,
    };
  }

  return { message: fallback, hint: null };
}
