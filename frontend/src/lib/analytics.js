/**
 * Frontend analytics helper.
 *
 * Pushes safe custom events to window.dataLayer so Google Tag Manager can
 * forward them to GA4. Base page_view tracking is handled by the Google tag
 * configured in GTM — this module only adds product events.
 *
 * Privacy: never pass raw user content (CV text, JD text, interview answers,
 * cover letter text, profile/evidence text), credentials, raw email, storage
 * keys, database IDs, full UUIDs, or raw API response bodies. The param
 * allow-list below is the last line of defence — only whitelisted, low-
 * cardinality keys are forwarded.
 */

export const ANALYTICS_EVENTS = {
  LANDING_CTA_CLICK: 'landing_cta_click',
  LOGIN_SUCCESS: 'login_success',
  LOGOUT_CLICK: 'logout_click',
  LANGUAGE_SWITCH: 'language_switch',

  CV_ANALYSIS_SUBMIT: 'cv_analysis_submit',
  CV_ANALYSIS_SUCCESS: 'cv_analysis_success',
  CV_ANALYSIS_ERROR: 'cv_analysis_error',
  RESULT_VIEW: 'result_view',
  DOWNLOAD_REPORT_CLICK: 'download_report_click',

  APPLICATION_CREATE_SUCCESS: 'application_create_success',
  APPLICATION_DETAIL_VIEW: 'application_detail_view',
  ATTACH_ANALYSIS_SUCCESS: 'attach_analysis_success',

  PROFILE_ITEM_CREATE_SUCCESS: 'profile_item_create_success',

  INTERVIEW_START: 'interview_start',
  INTERVIEW_ANSWER_SUBMIT_SUCCESS: 'interview_answer_submit_success',

  PACKAGE_GENERATE_SUCCESS: 'package_generate_success',

  COVER_LETTER_GENERATE_SUCCESS: 'cover_letter_generate_success',
  COVER_LETTER_SAVE_SUCCESS: 'cover_letter_save_success',

  // Phase 6 — Target Jobs
  TARGET_JOB_CREATED: 'target_job_created',
  TARGET_JOB_UPDATED: 'target_job_updated',
  TARGET_JOB_STATUS_CHANGED: 'target_job_status_changed',

  // Phase 6 — Learning Roadmap
  LEARNING_TASK_STARTED: 'learning_task_started',
  LEARNING_TASK_COMPLETED: 'learning_task_completed',

  // Phase 6 — Interview Sessions V2
  INTERVIEW_SESSION_CREATED: 'interview_session_created',
  INTERVIEW_ANSWER_SUBMITTED: 'interview_answer_submitted',

  // Phase 6 — Help Assistant
  HELP_ASSISTANT_OPENED: 'help_assistant_opened',
  HELP_ASSISTANT_PROMPT_CLICKED: 'help_assistant_prompt_clicked',

  // Phase 6 — Share
  SHARE_LINK_CREATED: 'share_link_created',
  SHARE_LINK_OPENED: 'share_link_opened',

  // Phase 6 — Usage
  USAGE_PAGE_VIEWED: 'usage_page_viewed',
};

/**
 * Bucket a 0–100 fit score into a coarse range so the raw value never leaves
 * the browser. Returns 'unknown' for null/NaN input.
 * @param {number|null|undefined} score
 * @returns {'0_20'|'20_40'|'40_60'|'60_80'|'80_100'|'unknown'}
 */
export function scoreBucket(score) {
  const n = Number(score);
  if (!Number.isFinite(n)) return 'unknown';
  const s = Math.max(0, Math.min(100, n));
  if (s < 20) return '0_20';
  if (s < 40) return '20_40';
  if (s < 60) return '40_60';
  if (s < 80) return '60_80';
  return '80_100';
}

/**
 * Push a custom event to the GTM dataLayer. No-ops safely when running on the
 * server or when GTM/dataLayer is unavailable (e.g. blocked by an ad blocker).
 * @param {string} eventName GA4-compatible event name
 * @param {Object} [params] Safe, low-cardinality params (see allow-list)
 */
export function trackEvent(eventName, params = {}) {
  if (typeof window === 'undefined') return;

  // GA4-compatible event names: start with a letter, use letters/numbers/underscore.
  if (!/^[a-z][a-z0-9_]{0,39}$/.test(eventName)) return;

  window.dataLayer = window.dataLayer || [];

  const safeParams = sanitizeAnalyticsParams(params);

  window.dataLayer.push({
    event: eventName,
    ...safeParams,
  });
}

function sanitizeAnalyticsParams(params) {
  const allowedKeys = new Set([
    'feature_name',
    'route',
    'status',
    'status_code',
    'error_type',
    'item_type',
    'interview_type',
    'application_status',
    'has_analysis',
    'score_bucket',
    'language',
    'source',
    // Phase 6 additions
    'question_type',
    'difficulty',
    'task_type',
    'prompt_chip',
    'plan_name',
    'visibility',
    'job_status',
  ]);

  const output = {};

  for (const [key, value] of Object.entries(params || {})) {
    if (!allowedKeys.has(key)) continue;

    if (typeof value === 'string') {
      output[key] = value.slice(0, 100);
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      output[key] = value;
    }
  }

  const path = typeof window !== 'undefined' ? window.location.pathname : undefined;
  if (path && !output.route) {
    output.route = path;
  }

  return output;
}
