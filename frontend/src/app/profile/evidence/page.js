'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ErrorBanner from '@/components/common/ErrorBanner';
import EmptyStatePage from '@/components/common/EmptyStatePage';
import { getEvidence, createEvidence, updateEvidence, deleteEvidence } from '@/services/profileApi';
import { extractApiError } from '@/utils/errorHelpers';
import { deduplicateByKey } from '@/utils/riskHelpers';
import styles from '@/styles/Evidence.module.css';

const TABS = [
  { id: 'skill', label: '🛠 Skills' },
  { id: 'project', label: '📁 Projects' },
  { id: 'achievement', label: '🏆 Achievements' },
];

const EMPTY_FORM = { title: '', description: '', tags: '' };

/** Single evidence card with edit + delete actions */
function EvidenceCard({ item, onEdit, onDelete, isDeleting }) {
  const tags = deduplicateByKey(
    (item.tags || []).map((t) => ({ t })),
    't'
  ).map((x) => x.t);

  return (
    <div className={styles.card} id={`evidence-card-${item.id}`}>
      <div className={styles.cardHeader}>
        <p className={styles.cardTitle}>{item.title || '—'}</p>
        <div className={styles.cardActions}>
          <button
            className={styles.iconBtn}
            onClick={() => onEdit(item)}
            aria-label="Edit"
            title="Edit"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
          </button>
          <button
            className={`${styles.iconBtn} ${styles.delete}`}
            onClick={() => onDelete(item.id)}
            disabled={isDeleting}
            aria-label="Delete"
            title="Delete"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
            </svg>
          </button>
        </div>
      </div>
      {item.description && (
        <p className={styles.cardDesc}>{item.description}</p>
      )}
      {tags.length > 0 && (
        <div className={styles.tags}>
          {tags.map((tag) => (
            <span key={tag} className={styles.tag}>{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}

/** Add / Edit form */
function EvidenceForm({ activeTab, editingItem, onSave, onCancel, isSaving }) {
  const [form, setForm] = useState(
    editingItem
      ? { title: editingItem.title || '', description: editingItem.description || '', tags: (editingItem.tags || []).join(', ') }
      : EMPTY_FORM
  );

  function handleChange(e) {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const payload = {
      type: activeTab,
      title: form.title.trim(),
      description: form.description.trim() || undefined,
      tags: form.tags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean),
    };
    onSave(payload);
  }

  const isEditing = Boolean(editingItem);
  const typeLabels = { skill: 'Skill', project: 'Project', achievement: 'Achievement' };

  return (
    <div className={styles.addCard}>
      <p className={styles.addTitle}>
        {isEditing ? `Edit ${typeLabels[activeTab]}` : `Add ${typeLabels[activeTab]}`}
      </p>
      <form onSubmit={handleSubmit}>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel} htmlFor={`evidence-title-${activeTab}`}>
            {activeTab === 'skill' ? 'Skill Name' : 'Title'} *
          </label>
          <input
            id={`evidence-title-${activeTab}`}
            name="title"
            type="text"
            className={styles.fieldInput}
            value={form.title}
            onChange={handleChange}
            placeholder={
              activeTab === 'skill'
                ? 'e.g. Python, React, FastAPI'
                : activeTab === 'project'
                  ? 'e.g. E-commerce Platform'
                  : 'e.g. Increased revenue by 30%'
            }
            required
            disabled={isSaving}
          />
        </div>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel} htmlFor={`evidence-desc-${activeTab}`}>
            Description (optional)
          </label>
          <textarea
            id={`evidence-desc-${activeTab}`}
            name="description"
            className={styles.fieldTextarea}
            value={form.description}
            onChange={handleChange}
            placeholder="Brief description…"
            disabled={isSaving}
          />
        </div>
        <div className={styles.fieldGroup}>
          <label className={styles.fieldLabel} htmlFor={`evidence-tags-${activeTab}`}>
            Tags (comma-separated, optional)
          </label>
          <input
            id={`evidence-tags-${activeTab}`}
            name="tags"
            type="text"
            className={styles.fieldInput}
            value={form.tags}
            onChange={handleChange}
            placeholder="e.g. backend, api, python"
            disabled={isSaving}
          />
        </div>
        <div className={styles.addActions}>
          <button type="button" className={styles.btnGhost} onClick={onCancel} disabled={isSaving}>
            Cancel
          </button>
          <button
            type="submit"
            className={styles.btnPrimary}
            disabled={isSaving || !form.title.trim()}
            id="save-evidence-btn"
          >
            {isSaving ? 'Saving…' : isEditing ? 'Update' : 'Add'}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function EvidencePage() {
  const { isAuthChecking } = useRequireAuth();
  const [activeTab, setActiveTab] = useState('skill');
  const [allItems, setAllItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const loadEvidence = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getEvidence();
      setAllItems(Array.isArray(data?.items) ? data.items : []);
    } catch (err) {
      const { message } = extractApiError(err, 'Could not load evidence items.');
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthChecking) return;
    loadEvidence();
  }, [isAuthChecking, loadEvidence]);

  // Filter and deduplicate items for active tab
  const tabItems = deduplicateByKey(
    allItems.filter((item) => item.type === activeTab),
    'title'
  );

  const handleSave = async (payload) => {
    setIsSaving(true);
    setError(null);
    try {
      if (editingItem) {
        const updated = await updateEvidence(editingItem.id, payload);
        setAllItems((prev) =>
          prev.map((item) => (item.id === editingItem.id ? updated : item))
        );
      } else {
        const created = await createEvidence(payload);
        setAllItems((prev) => [...prev, created]);
      }
      setShowForm(false);
      setEditingItem(null);
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to save. Please try again.');
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this evidence item?')) return;
    setDeletingId(id);
    try {
      await deleteEvidence(id);
      setAllItems((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      const { message } = extractApiError(err, 'Failed to delete item.');
      setError(message);
    } finally {
      setDeletingId(null);
    }
  };

  const handleEdit = (item) => {
    setEditingItem(item);
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingItem(null);
  };

  const vaultIcon = (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </svg>
  );

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      <div className={styles.topRow}>
        <div>
          <h1 className={styles.pageTitle}>Evidence Vault</h1>
          <p className={styles.pageSubtitle}>
            Manage your skills, projects, and achievements. Used to personalise AI-generated materials.
          </p>
        </div>
        <Link href="/profile" style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-primary)', textDecoration: 'none' }}>
          ← Back to Profile
        </Link>
      </div>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {/* Tabs */}
      <div className={styles.tabs} role="tablist" aria-label="Evidence categories">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            className={`${styles.tabBtn} ${activeTab === tab.id ? styles.active : ''}`}
            onClick={() => { setActiveTab(tab.id); setShowForm(false); setEditingItem(null); }}
            id={`tab-${tab.id}`}
          >
            {tab.label}
            {allItems.filter((i) => i.type === tab.id).length > 0 && (
              <span style={{ marginLeft: '4px', background: 'var(--color-primary-light)', color: 'var(--color-primary)', borderRadius: '999px', padding: '0 6px', fontSize: '0.6875rem', fontWeight: 700 }}>
                {allItems.filter((i) => i.type === tab.id).length}
              </span>
            )}
          </button>
        ))}
      </div>

      {isLoading && <LoadingSpinner fullPage label="Loading evidence…" />}

      {!isLoading && (
        <>
          <div className={styles.grid}>
            {/* Add / Edit form */}
            {showForm && (
              <EvidenceForm
                activeTab={activeTab}
                editingItem={editingItem}
                onSave={handleSave}
                onCancel={handleCancelForm}
                isSaving={isSaving}
              />
            )}

            {/* Evidence cards */}
            {tabItems.map((item, i) => (
              <EvidenceCard
                key={item.id}
                item={item}
                onEdit={handleEdit}
                onDelete={handleDelete}
                isDeleting={deletingId === item.id}
              />
            ))}

            {/* Add button card (when form is hidden) */}
            {!showForm && (
              <button
                className={styles.addCard}
                onClick={() => { setEditingItem(null); setShowForm(true); }}
                id={`add-${activeTab}-btn`}
                style={{ textAlign: 'center', cursor: 'pointer', color: 'var(--color-text-muted)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', border: '2px dashed var(--color-border)', background: 'transparent' }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="32" height="32">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="16" />
                  <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
                <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 600 }}>
                  Add {activeTab}
                </span>
              </button>
            )}
          </div>

          {/* Empty state when no items and form not shown */}
          {tabItems.length === 0 && !showForm && (
            <EmptyStatePage
              icon={vaultIcon}
              title={`No ${activeTab}s yet`}
              description={`Add your first ${activeTab} to start building your evidence vault. This information helps personalise your AI-generated cover letters and packages.`}
            />
          )}
        </>
      )}
    </PageShell>
  );
}
