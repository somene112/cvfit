'use client';

import { useState, useCallback } from 'react';
import { uploadCV } from '@/services/cvApi';
import { extractApiError } from '@/utils/errorHelpers';

export function useUploadCV() {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [errorHint, setErrorHint] = useState(null);
  const [cvFileId, setCvFileId] = useState(null);

  const resetUpload = useCallback(() => {
    setFile(null);
    setProgress(0);
    setIsUploading(false);
    setError(null);
    setErrorHint(null);
    setCvFileId(null);
  }, []);

  const upload = useCallback(async (fileToUpload) => {
    const targetFile = fileToUpload || file;
    if (!targetFile) {
      setError('No file selected');
      setErrorHint(null);
      return null;
    }

    setIsUploading(true);
    setError(null);
    setErrorHint(null);
    setProgress(0);

    try {
      const data = await uploadCV(targetFile, (progressEvent) => {
        const percent = Math.round(
          (progressEvent.loaded * 100) / (progressEvent.total || progressEvent.loaded)
        );
        setProgress(percent);
      });

      setCvFileId(data.cv_file_id);
      setIsUploading(false);
      setProgress(100);
      return data.cv_file_id;
    } catch (err) {
      const { message, hint } = extractApiError(err, 'Upload failed. Please try again.');
      setError(message);
      setErrorHint(hint);
      setIsUploading(false);
      setProgress(0);
      return null;
    }
  }, [file]);

  return {
    file,
    setFile,
    upload,
    progress,
    isUploading,
    error,
    errorHint,
    cvFileId,
    resetUpload,
  };
}
