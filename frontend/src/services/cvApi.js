import apiClient from './apiClient';

/**
 * Upload a CV file to the backend.
 * @param {File} file - The CV file to upload (PDF or DOCX)
 * @param {Function} onUploadProgress - Axios progress callback
 * @returns {Promise<{cv_file_id: string}>}
 */
export async function uploadCV(file, onUploadProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/v1/cv/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress,
  });

  return response.data;
}
