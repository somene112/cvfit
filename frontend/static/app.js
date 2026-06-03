const cvFileInput = document.getElementById('cvFile');
const fileName = document.getElementById('fileName');
const jobDescription = document.getElementById('jobDescription');
const analyzeBtn = document.getElementById('analyzeBtn');
const statusCard = document.getElementById('statusCard');
const statusTitle = document.getElementById('statusTitle');
const statusPercent = document.getElementById('statusPercent');
const statusMessage = document.getElementById('statusMessage');
const progressBar = document.getElementById('progressBar');
const errorState = document.getElementById('errorState');
const resultCard = document.getElementById('resultCard');
const resultSummary = document.getElementById('resultSummary');
const fitScore = document.getElementById('fitScore');
const scoreBreakdown = document.getElementById('scoreBreakdown');
const skillGaps = document.getElementById('skillGaps');
const downloadReport = document.getElementById('downloadReport');

const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 60;
const TERMINAL_STATUSES = new Set(['succeeded', 'failed']);
const SUPPORTED_EXTENSIONS = ['.pdf', '.docx'];

let activeRunId = 0;

cvFileInput?.addEventListener('change', () => {
  const file = cvFileInput.files?.[0];
  fileName.textContent = file ? file.name : 'Select a PDF or DOCX CV';
  clearError();
});

analyzeBtn?.addEventListener('click', async () => {
  const runId = activeRunId + 1;
  activeRunId = runId;
  setRunning(true);
  resetResult();
  clearError();

  try {
    const file = validateInputs();

    updateStatus('Uploading CV', 5, 'Sending the selected CV to the analyzer.');
    const upload = await uploadCv(file);
    if (!upload.cv_file_id) {
      throw new Error('Upload succeeded but did not return a CV file id.');
    }

    updateStatus('Creating analysis job', 10, 'Submitting the job description.');
    const created = await createScoreJob(upload.cv_file_id, jobDescription.value.trim());
    if (!created.job_id || !created.access_token) {
      throw new Error('Analysis job response was missing required fields.');
    }

    const finalStatus = await pollJob(created.job_id, runId);
    if (finalStatus.status === 'failed') {
      throw new Error(finalStatus.error_message || 'The analysis job failed.');
    }

    updateStatus('Loading result', 96, 'Fetching the score and report metadata.');
    const result = await fetchResult(created.job_id, created.access_token);
    const report = await fetchReport(created.job_id, created.access_token);

    renderResult(result.result, report);
    updateStatus('Analysis complete', 100, 'The fit score and DOCX report are ready.');
  } catch (error) {
    showError(error);
  } finally {
    if (runId === activeRunId) {
      setRunning(false);
    }
  }
});

function validateInputs() {
  const file = cvFileInput.files?.[0];
  if (!file) {
    throw new Error('Select a PDF or DOCX CV before analyzing.');
  }

  const lowerName = file.name.toLowerCase();
  if (!SUPPORTED_EXTENSIONS.some((ext) => lowerName.endsWith(ext))) {
    throw new Error('Only PDF and DOCX CV files are supported.');
  }

  const jdText = jobDescription.value.trim();
  if (jdText.length < 30) {
    throw new Error('Paste a job description with at least 30 characters.');
  }

  return file;
}

async function uploadCv(file) {
  const formData = new FormData();
  formData.append('file', file);
  return requestJson('/v1/cv/upload', {
    method: 'POST',
    body: formData,
  });
}

async function createScoreJob(cvFileId, jdText) {
  return requestJson('/v1/jobs/create-score', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      cv_file_id: cvFileId,
      jd_text: jdText,
      options: {
        target_role: null,
        language: 'en',
        strictness: 'balanced',
        output_formats: ['json', 'docx'],
      },
    }),
  });
}

async function pollJob(jobId, runId) {
  for (let attempt = 1; attempt <= MAX_POLL_ATTEMPTS; attempt += 1) {
    if (runId !== activeRunId) {
      throw new Error('Analysis was interrupted.');
    }

    const status = await requestJson(`/v1/jobs/${encodeURIComponent(jobId)}`);
    const progress = normalizeProgress(status.progress);
    const label = status.status || 'queued';
    updateStatus(
      formatStatus(label),
      progress,
      `Job ${formatStatus(label).toLowerCase()} (${progress}%).`
    );

    if (TERMINAL_STATUSES.has(label)) {
      return status;
    }

    await sleep(POLL_INTERVAL_MS);
  }

  throw new Error('Analysis timed out. The job may still finish later.');
}

async function fetchResult(jobId, accessToken) {
  const token = encodeURIComponent(accessToken);
  return requestJson(`/v1/jobs/${encodeURIComponent(jobId)}/result?access_token=${token}`);
}

async function fetchReport(jobId, accessToken) {
  const token = encodeURIComponent(accessToken);
  const report = await requestJson(`/v1/jobs/${encodeURIComponent(jobId)}/report?access_token=${token}`);
  if (Object.prototype.hasOwnProperty.call(report, 'local_path')) {
    throw new Error('Report metadata returned an unsafe field.');
  }
  if (report.format !== 'docx' || typeof report.download_url !== 'string') {
    throw new Error('Report metadata did not include a DOCX download URL.');
  }
  return report;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  let payload = null;

  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const detail = safeDetail(payload);
    const message = detail ? `Request failed (${response.status}): ${detail}` : `Request failed with HTTP ${response.status}.`;
    throw new Error(redactToken(message));
  }

  return payload || {};
}

function renderResult(result, report) {
  const scores = result?.scores || {};
  const score = scores.fit_score;

  fitScore.textContent = Number.isFinite(Number(score)) ? `${score}` : '--';
  resultSummary.textContent = buildSummary(result);
  renderScoreBreakdown(scores);
  renderSkillGaps(result?.skill_gap || {});

  downloadReport.href = report.download_url;
  downloadReport.classList.remove('hidden');
  resultCard.classList.remove('hidden');
}

function buildSummary(result) {
  const fileNameValue = result?.cv?.file_name;
  const confidence = result?.cv?.parsed_confidence;
  const pieces = [];

  if (fileNameValue) {
    pieces.push(`CV: ${fileNameValue}`);
  }
  if (confidence !== undefined && confidence !== null) {
    pieces.push(`Parser confidence: ${confidence}`);
  }

  return pieces.length ? pieces.join(' | ') : 'Analysis complete.';
}

function renderScoreBreakdown(scores) {
  const entries = [
    ['Skill match', scores.skill_match],
    ['Responsibility match', scores.responsibility_match],
    ['Experience level', scores.experience_level],
    ['Project relevance', scores.project_relevance],
    ['CV quality', scores.cv_quality],
  ];

  scoreBreakdown.replaceChildren();
  entries.forEach(([label, value]) => {
    if (value === undefined || value === null) {
      return;
    }
    const row = document.createElement('div');
    row.className = 'score-row';

    const labelEl = document.createElement('span');
    labelEl.textContent = label;

    const valueEl = document.createElement('strong');
    valueEl.textContent = `${value}`;

    row.append(labelEl, valueEl);
    scoreBreakdown.appendChild(row);
  });
}

function renderSkillGaps(gap) {
  const gaps = [
    ...(gap.missing_must_have || []),
    ...(gap.missing_nice_to_have || []),
  ].slice(0, 6);

  skillGaps.replaceChildren();
  if (!gaps.length) {
    const item = document.createElement('li');
    item.textContent = 'No major skill gaps were detected in the result.';
    skillGaps.appendChild(item);
    return;
  }

  gaps.forEach((gapText) => {
    const item = document.createElement('li');
    item.textContent = gapText;
    skillGaps.appendChild(item);
  });
}

function updateStatus(title, percent, message) {
  const safePercent = normalizeProgress(percent);
  statusCard.classList.remove('hidden');
  statusTitle.textContent = title;
  statusPercent.textContent = `${safePercent}%`;
  statusMessage.textContent = message;
  progressBar.style.width = `${safePercent}%`;
}

function setRunning(isRunning) {
  analyzeBtn.disabled = isRunning;
  analyzeBtn.textContent = isRunning ? 'Analyzing...' : 'Analyze CV';
}

function resetResult() {
  resultCard.classList.add('hidden');
  downloadReport.classList.add('hidden');
  downloadReport.removeAttribute('href');
  fitScore.textContent = '--';
  resultSummary.textContent = 'Analysis complete.';
  scoreBreakdown.replaceChildren();
  skillGaps.replaceChildren();
}

function showError(error) {
  const message = redactToken(error?.message || 'Something went wrong. Try again.');
  errorState.textContent = message;
  errorState.classList.remove('hidden');
  updateStatus('Analysis stopped', 0, 'Review the message and try again.');
}

function clearError() {
  errorState.textContent = '';
  errorState.classList.add('hidden');
}

function safeDetail(payload) {
  const detail = payload?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item?.msg || item?.detail || 'Validation error').join('; ');
  }
  if (typeof detail === 'string') {
    return detail;
  }
  return '';
}

function redactToken(value) {
  return String(value).replace(/access_token=([^&\s]+)/g, 'access_token=<hidden>');
}

function normalizeProgress(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round(numeric)));
}

function formatStatus(value) {
  return String(value || 'queued')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function sleep(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms);
  });
}
