'use client';

import { useState, useCallback } from 'react';
import { uploadCV } from '@/services/cvApi';

export function useUploadCV() {
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [cvFileId, setCvFileId] = useState(null);

  const resetUpload = useCallback(() => {
    setFile(null);
    setProgress(0);
    setIsUploading(false);
    setError(null);
    setCvFileId(null);
  }, []);

  const upload = useCallback(async (fileToUpload) => {
    const targetFile = fileToUpload || file;
    if (!targetFile) {
      setError('No file selected');
      return null;
    }

    setIsUploading(true);
    setError(null);
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
      const detail = err.response?.data?.detail;
      const message =
        (detail && typeof detail === 'object' && detail.message)
          ? detail.message
          : (typeof detail === 'string' && detail)
          ? detail
          : err.response?.data?.message
          || err.message
          || 'Upload failed. Please try again.';
      setError(message);
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
    cvFileId,
    resetUpload,
  };
}
