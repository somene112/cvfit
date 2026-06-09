'use client';

import { useState, useMemo } from 'react';
import { useLanguage } from '@/context/LanguageContext';
import {
  deduplicateEvidence,
  groupEvidenceBySkill,
  truncateText,
} from '@/utils/resultHelpers';
import styles from '@/styles/EvidenceSection.module.css';

const INITIAL_ITEMS_PER_GROUP = 2;
const TRUNCATE_LENGTH = 120;

/**
 * EvidenceSection — Phase 4 evidence rendering with:
 * - Deduplication
 * - Grouping by skill/category
 * - Truncation with expand/collapse
 * - Show more / show less per group
 */
export default function EvidenceSection({ evidence }) {
  const { t } = useLanguage();
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedGroups, setExpandedGroups] = useState(new Set());
  const [expandedTexts, setExpandedTexts] = useState(new Set());
  const [expandedGroupItems, setExpandedGroupItems] = useState(new Set());

  const dedupedEvidence = useMemo(
    () => deduplicateEvidence(evidence),
    [evidence]
  );

  const groupedEvidence = useMemo(
    () => groupEvidenceBySkill(dedupedEvidence),
    [dedupedEvidence]
  );

  if (!evidence || evidence.length === 0) {
    return (
      <div className={styles.emptyEvidence}>
        {t('phase4.evidence.empty')}
      </div>
    );
  }

  const toggleGroup = (groupKey) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupKey)) next.delete(groupKey);
      else next.add(groupKey);
      return next;
    });
  };

  const toggleText = (evId) => {
    setExpandedTexts((prev) => {
      const next = new Set(prev);
      if (next.has(evId)) next.delete(evId);
      else next.add(evId);
      return next;
    });
  };

  const toggleGroupItems = (groupKey) => {
    setExpandedGroupItems((prev) => {
      const next = new Set(prev);
      if (next.has(groupKey)) next.delete(groupKey);
      else next.add(groupKey);
      return next;
    });
  };

  const groupEntries = Array.from(groupedEvidence.entries());

  return (
    <div className={styles.evidenceSection}>
      {/* Toggle all evidence */}
      <button
        className={`${styles.toggleButton} ${isExpanded ? styles.toggleButtonExpanded : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
        id="evidence-toggle-all"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="6 9 12 15 18 9" />
        </svg>
        {isExpanded ? t('phase4.evidence.hideAll') : t('phase4.evidence.showAll')}
        <span className={styles.skillGroupCount}>
          {dedupedEvidence.length}
        </span>
      </button>

      {isExpanded && (
        <>
          {groupEntries.map(([groupKey, items], gIndex) => {
            const isGroupOpen = expandedGroups.has(groupKey);
            const showAll = expandedGroupItems.has(groupKey);
            const visibleItems = showAll ? items : items.slice(0, INITIAL_ITEMS_PER_GROUP);
            const hiddenCount = items.length - INITIAL_ITEMS_PER_GROUP;

            return (
              <div
                key={groupKey}
                className={styles.skillGroup}
                style={{ animationDelay: `${gIndex * 0.05}s` }}
              >
                {/* Group header */}
                <div
                  className={styles.skillGroupHeader}
                  onClick={() => toggleGroup(groupKey)}
                  role="button"
                  tabIndex={0}
                  aria-expanded={isGroupOpen}
                >
                  <div className={styles.skillGroupLeft}>
                    <span className={styles.skillGroupName}>{groupKey}</span>
                    <span className={styles.skillGroupCount}>
                      {items.length} {items.length === 1 ? 'item' : 'items'}
                    </span>
                  </div>
                  <svg
                    className={`${styles.skillGroupChevron} ${isGroupOpen ? styles.skillGroupChevronExpanded : ''}`}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </div>

                {/* Group items */}
                {isGroupOpen && (
                  <div className={styles.skillGroupItems}>
                    {visibleItems.map((ev, eIndex) => {
                      const evId = ev.id ?? `ev-${gIndex}-${eIndex}`;
                      const isTextExpanded = expandedTexts.has(evId);
                      const needsTruncation = (ev.text || '').length > TRUNCATE_LENGTH;
                      const displayText = isTextExpanded
                        ? ev.text
                        : truncateText(ev.text, TRUNCATE_LENGTH);

                      return (
                        <div
                          key={evId}
                          className={styles.evidenceItem}
                          style={{ animationDelay: `${eIndex * 0.03}s` }}
                        >
                          <div className={styles.evidenceBullet} />
                          <div className={styles.evidenceContent}>
                            <div className={isTextExpanded ? styles.evidenceTextFull : styles.evidenceTextTruncated}>
                              {displayText}
                              {needsTruncation && (
                                <button
                                  className={styles.textToggle}
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    toggleText(evId);
                                  }}
                                >
                                  {isTextExpanded ? t('phase4.evidence.showLess') : t('phase4.evidence.showFull')}
                                </button>
                              )}
                            </div>
                            <div className={styles.evidenceMeta}>
                              <span className={`${styles.sourceBadge} ${ev.source === 'cv' ? styles.sourceCv : styles.sourceJd}`}>
                                {ev.source === 'cv' ? 'CV' : 'JD'}
                              </span>
                              {ev.location?.section && (
                                <span className={styles.sectionTag}>
                                  {ev.location.section}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}

                    {!showAll && hiddenCount > 0 && (
                      <button
                        className={styles.showMoreButton}
                        onClick={() => toggleGroupItems(groupKey)}
                      >
                        +{hiddenCount} {t('phase4.evidence.showMore')}
                      </button>
                    )}
                    {showAll && hiddenCount > 0 && (
                      <button
                        className={styles.showMoreButton}
                        onClick={() => toggleGroupItems(groupKey)}
                      >
                        {t('phase4.evidence.showLess')}
                      </button>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
