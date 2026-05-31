'use client';

import { useRef, useState, useCallback } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import styles from '@/styles/UploadCV.module.css';
import { ACCEPTED_EXTENSIONS } from '@/utils/constants';

export default function UploadCV({ file, onFileSelect, progress, isUploading, error, onRemove, disabled }) {
  const { t } = useLanguage();
  const fileInputRef = useRef(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const validateFile = useCallback((f) => {
    const ext = '.' + f.name.split('.').pop().toLowerCase();
    if (!ACCEPTED_EXTENSIONS.includes(ext)) {
      return t('upload.error.format');
    }
    if (f.size > 10 * 1024 * 1024) {
      return t('upload.error.size');
    }
    return null;
  }, [t]);

  const handleFile = useCallback((f) => {
    const validationError = validateFile(f);
    if (validationError) {
      alert(validationError);
      return;
    }
    onFileSelect(f);
  }, [validateFile, onFileSelect]);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    const droppedFile = e.dataTransfer?.files?.[0];
    if (droppedFile) {
      handleFile(droppedFile);
    }
  }, [handleFile]);

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleInputChange = (e) => {
    const selected = e.target.files?.[0];
    if (selected) {
      handleFile(selected);
    }
    e.target.value = '';
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getFileExtension = (name) => {
    return name.split('.').pop().toLowerCase();
  };

  return (
    <div className={styles.card} id="upload-cv-section">
      <div className={styles.cardHeader}>
        <div className={styles.cardIcon}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <div>
          <h2 className={styles.cardTitle}>{t('upload.title')}</h2>
          <p className={styles.cardSubtitle}>{t('upload.subtitle')}</p>
        </div>
      </div>

      <div
        className={`${styles.dropzone} ${isDragOver ? styles.dropzoneActive : ''} ${disabled ? styles.dropzoneDisabled : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        role="button"
        tabIndex={0}
        aria-label="Upload CV file"
        id="cv-dropzone"
      >
        <input
          ref={fileInputRef}
          type="file"
          className={styles.hiddenInput}
          accept=".pdf,.docx"
          onChange={handleInputChange}
          id="cv-file-input"
        />
        <div className={styles.uploadIconContainer}>
          <svg className={styles.uploadIcon} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p className={styles.dropzoneTitle}>
          {t('upload.dropzone.title1')} <span>{t('upload.dropzone.title2')}</span>
        </p>
        <p className={styles.dropzoneSubtext}>{t('upload.dropzone.subtext')}</p>
      </div>

      {file && (
        <div className={styles.filePreview} id="file-preview">
          <div className={`${styles.fileIcon} ${getFileExtension(file.name) === 'pdf' ? styles.fileIconPdf : styles.fileIconDocx}`}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <div className={styles.fileDetails}>
            <p className={styles.fileName}>{file.name}</p>
            <p className={styles.fileSize}>{formatFileSize(file.size)} • {getFileExtension(file.name).toUpperCase()}</p>
          </div>
          {!isUploading && (
            <button
              className={styles.removeButton}
              onClick={(e) => {
                e.stopPropagation();
                onRemove();
              }}
              aria-label="Remove file"
              id="remove-file-button"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          )}
        </div>
      )}

      {isUploading && (
        <div className={styles.progressContainer}>
          <div className={styles.progressBar}>
            <div
              className={styles.progressFill}
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className={styles.progressText}>
            <span>{t('upload.progress.uploading')}</span>
            <span>{progress}%</span>
          </div>
        </div>
      )}

      {error && (
        <div className={styles.errorText} role="alert" id="upload-error">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      )}
    </div>
  );
}
