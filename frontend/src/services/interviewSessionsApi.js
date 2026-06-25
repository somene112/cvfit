import apiClient from './apiClient';

/**
 * Interview Sessions V2 API (Phase 6)
 * Endpoints under /v1/interview/sessions. All routes require Bearer JWT
 * (handled by the apiClient interceptor).
 *
 * The backend contract uses `question_text` and a nested
 * `{ session, questions, total_questions }` detail shape, plus a 0-5 rubric in
 * `score` and feedback in `feedback`. The page renders a flatter shape with
 * `q.text`, `feedback.overall_score`, etc. on a 0-10 scale. These normalizers
 * adapt the (already-tested) backend contract to what the page expects, so the
 * backend response contract is not changed.
 *
 * Question types: technical | behavioral | project | HR | gap_check
 * Difficulty:     easy | medium | hard
 * Rubric keys:    relevance | evidence | clarity | structure | confidence | risk
 */

const RUBRIC_KEYS = ['relevance', 'evidence', 'clarity', 'structure', 'confidence', 'risk'];
// The backend rubric is 0-5; the UI displays a 0-10 scale.
const UI_SCALE = 2;

function scaleScore(value) {
  return typeof value === 'number' ? Math.round(value * UI_SCALE * 10) / 10 : value;
}

function normalizeQuestion(q) {
  return {
    id: q.id,
    text: q.question_text,
    type: q.question_type,
    difficulty: q.difficulty,
    related_evidence: q.related_evidence ?? null,
    rubric: q.rubric ?? null,
  };
}

function normalizeSessionDetail(data) {
  const s = data?.session ?? {};
  return {
    id: s.id,
    question_type: s.session_type,
    difficulty: s.difficulty,
    status: s.status,
    created_at: s.created_at,
    questions: Array.isArray(data?.questions) ? data.questions.map(normalizeQuestion) : [],
    // The detail endpoint does not return prior answers; the page answers live.
    answers: [],
  };
}

function normalizeAnswerFeedback(answer) {
  const score = answer?.score ?? {};
  const feedback = answer?.feedback ?? {};
  const rubric = {};
  RUBRIC_KEYS.forEach((key) => { rubric[key] = scaleScore(score[key]); });
  return {
    answer_id: answer?.id,
    question_id: answer?.question_id,
    attempt_number: answer?.attempt_number,
    overall_score: scaleScore(score.overall),
    ...rubric,
    rubric,
    // The backend returns structured strengths/improvements; surface them in the
    // shape the page renders (a summary paragraph + a suggestions list).
    feedback_text: Array.isArray(feedback.strengths) ? feedback.strengths.join(' ') : '',
    strengths: feedback.strengths ?? [],
    suggestions: feedback.improvements ?? [],
    risk_flags: feedback.risk_flags ?? [],
    disclaimer: feedback.disclaimer ?? null,
  };
}

/**
 * List all interview sessions for the authenticated user.
 */
export async function listSessions() {
  const response = await apiClient.get('/v1/interview/sessions');
  return response.data;
}

/**
 * Create a new interview session. Maps the UI `question_type` to the backend
 * `session_type` so the chosen focus is preserved on the session.
 */
export async function createSession(payload = {}) {
  const body = {
    session_type: payload.session_type || payload.question_type || 'mixed',
    difficulty: payload.difficulty || 'medium',
  };
  if (payload.target_job_id) body.target_job_id = payload.target_job_id;
  if (payload.application_id) body.application_id = payload.application_id;
  if (payload.analysis_job_id) body.analysis_job_id = payload.analysis_job_id;
  const response = await apiClient.post('/v1/interview/sessions', body);
  return response.data;
}

/**
 * Get a single session with its questions, normalized to the page shape.
 */
export async function getSession(id) {
  const response = await apiClient.get(`/v1/interview/sessions/${id}`);
  return normalizeSessionDetail(response.data);
}

/**
 * Generate questions for a session (Vietnamese by default). A "mixed" session
 * sends no type filter so the backend returns a mix.
 */
export async function generateSessionQuestions(sessionId, options = {}) {
  const { question_type, difficulty, count = 5, language = 'vi' } = options;
  const body = { count, language };
  if (difficulty) body.difficulty = difficulty;
  if (question_type && question_type !== 'mixed') body.question_type = question_type;
  const response = await apiClient.post(`/v1/interview/sessions/${sessionId}/questions/generate`, body);
  return response.data;
}

/**
 * Submit an answer; returns normalized feedback (0-10 scale, page field names).
 * Feedback prose is Vietnamese by default.
 */
export async function submitSessionAnswer(sessionId, payload, language = 'vi') {
  const response = await apiClient.post(
    `/v1/interview/sessions/${sessionId}/answers`,
    { ...payload, language }
  );
  return normalizeAnswerFeedback(response.data);
}
