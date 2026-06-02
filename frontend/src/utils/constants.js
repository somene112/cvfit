export const API_BASE_URL =
  typeof window !== 'undefined' && process.env.NEXT_PUBLIC_API_BASE_URL
    ? process.env.NEXT_PUBLIC_API_BASE_URL
    : 'http://localhost:8000';

export const COLORS = {
  primary: '#2563EB',
  secondary: '#60A5FA',
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  background: '#F8FAFC',
  card: '#FFFFFF',
};

export const STRICTNESS_OPTIONS = [
  { value: 'lenient', label: 'Lenient', description: 'More forgiving analysis' },
  { value: 'balanced', label: 'Balanced', description: 'Standard evaluation' },
  { value: 'strict', label: 'Strict', description: 'Rigorous assessment' },
];

export const LANGUAGE_OPTIONS = [
  { value: 'en', label: 'English' },
  { value: 'id', label: 'Indonesian' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ja', label: 'Japanese' },
];

export const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
};

export const ACCEPTED_EXTENSIONS = ['.pdf', '.docx'];

export const JOB_STATUS = {
  QUEUED: 'queued',
  RUNNING: 'running',
  SUCCEEDED: 'succeeded',
  FAILED: 'failed',
};

export const POLL_INTERVAL_MS = 2000;

export const MAX_JD_CHARACTERS = 5000;

export const WORKFLOW_STEPS = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  CREATING_JOB: 'creating_job',
  POLLING: 'polling',
  RESULT: 'result',
  ERROR: 'error',
};
