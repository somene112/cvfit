'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import PageShell from '@/components/common/PageShell';
import LoadingSpinner from '@/components/common/LoadingSpinner';
import ErrorBanner from '@/components/common/ErrorBanner';
import { getProfile } from '@/services/profileApi';
import { getStoredUser } from '@/services/authStorage';
import { extractApiError } from '@/utils/errorHelpers';
import styles from '@/styles/Profile.module.css';

export default function ProfilePage() {
  const { isAuthChecking, user: authUser } = useRequireAuth();
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Get user from local storage as a fallback
  const storedUser = typeof window !== 'undefined' ? getStoredUser() : null;
  const displayUser = authUser || storedUser;

  useEffect(() => {
    if (isAuthChecking) return;
    let active = true;
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const data = await getProfile();
        if (!active) return;
        setProfile(data);
      } catch (err) {
        if (!active) return;
        // Profile endpoint may not exist yet — gracefully degrade
        if (err?.response?.status !== 404) {
          const { message } = extractApiError(err, 'Could not load profile.');
          setError(message);
        }
      } finally {
        if (active) setIsLoading(false);
      }
    })();

    return () => { active = false; };
  }, [isAuthChecking]);

  const name = displayUser?.full_name || displayUser?.email || 'User';
  const initial = name.charAt(0).toUpperCase();

  return (
    <PageShell isAuthChecking={isAuthChecking}>
      <h1 className={styles.pageTitle}>Career Profile</h1>
      <p className={styles.pageSubtitle}>Your professional profile and evidence vault.</p>

      {error && <ErrorBanner message={error} onDismiss={() => setError(null)} />}

      {isLoading ? (
        <LoadingSpinner fullPage label="Loading profile…" />
      ) : (
        <>
          {/* Profile card */}
          <div className={styles.profileCard}>
            <div className={styles.profileHeader}>
              <div className={styles.avatar} aria-hidden="true">{initial}</div>
              <div>
                <p className={styles.profileName}>{name}</p>
                {displayUser?.email && (
                  <p className={styles.profileEmail}>{displayUser.email}</p>
                )}
              </div>
            </div>

            {/* Stats row */}
            <div className={styles.statsGrid}>
              <div className={styles.stat}>
                <div className={styles.statValue}>
                  {profile?.applications_count ?? '—'}
                </div>
                <div className={styles.statLabel}>Applications</div>
              </div>
              <div className={styles.stat}>
                <div className={styles.statValue}>
                  {profile?.avg_fit_score != null
                    ? `${Math.round(profile.avg_fit_score)}%`
                    : '—'}
                </div>
                <div className={styles.statLabel}>Avg Fit Score</div>
              </div>
              <div className={styles.stat}>
                <div className={styles.statValue}>
                  {profile?.evidence_count ?? '—'}
                </div>
                <div className={styles.statLabel}>Evidence Items</div>
              </div>
              <div className={styles.stat}>
                <div className={styles.statValue}>
                  {profile?.interviews_completed ?? '—'}
                </div>
                <div className={styles.statLabel}>Interviews Done</div>
              </div>
            </div>
          </div>

          {/* Quick links */}
          <div className={styles.quickLinks}>
            <Link href="/profile/evidence" className={styles.quickLink} id="go-to-evidence-btn">
              <div className={styles.quickLinkIcon} style={{ background: '#EFF6FF' }}>
                🗂️
              </div>
              <div>
                <p className={styles.quickLinkTitle}>Evidence Vault</p>
                <p className={styles.quickLinkDesc}>Manage your skills, projects & achievements</p>
              </div>
            </Link>
            <Link href="/applications" className={styles.quickLink}>
              <div className={styles.quickLinkIcon} style={{ background: '#F0FDF4' }}>
                📋
              </div>
              <div>
                <p className={styles.quickLinkTitle}>My Applications</p>
                <p className={styles.quickLinkDesc}>View all your tracked job applications</p>
              </div>
            </Link>
            <Link href="/history" className={styles.quickLink}>
              <div className={styles.quickLinkIcon} style={{ background: '#FEF3C7' }}>
                📊
              </div>
              <div>
                <p className={styles.quickLinkTitle}>Analysis History</p>
                <p className={styles.quickLinkDesc}>All your CV analysis results</p>
              </div>
            </Link>
            <Link href="/dashboard" className={styles.quickLink}>
              <div className={styles.quickLinkIcon} style={{ background: '#F5F3FF' }}>
                ⚡
              </div>
              <div>
                <p className={styles.quickLinkTitle}>New Analysis</p>
                <p className={styles.quickLinkDesc}>Run a new CV fit analysis</p>
              </div>
            </Link>
          </div>
        </>
      )}
    </PageShell>
  );
}
