'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { getCurrentUser, logout, type User } from '@/lib/auth';

interface Case {
  id: string;
  title: string;
  description: string;
  difficulty: number;
  total_points: number;
  is_active: boolean;
  created_at: string;
}

interface CaseProgress {
  case_id: string;
  solved_challenges: number;
  total_challenges: number;
  points_earned: number;
  total_points: number;
}

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [progress, setProgress] = useState<Record<string, CaseProgress>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    // Get user
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      router.push('/login');
      return;
    }
    setUser(currentUser);

    // Get cases
    const casesResponse = await api.getCases();
    if (casesResponse.status === 200 && casesResponse.data) {
      // API returns { cases: [], total, page, ... }
      const casesList = (casesResponse.data as any).cases || [];
      setCases(casesList);

      // Get status for each case
      const progressData: Record<string, CaseProgress> = {};
      for (const c of casesList) {
        const statusResponse = await api.getCaseStatus(c.id);
        if (statusResponse.status === 200 && statusResponse.data) {
          const status = statusResponse.data as any;
          progressData[c.id] = {
            case_id: c.id,
            solved_challenges: status.is_solved ? 1 : 0,
            total_challenges: 1,
            points_earned: status.points_earned || 0,
            total_points: c.total_points,
          };
        }
      }
      setProgress(progressData);
    }

    setLoading(false);
  };

  const handleLogout = async () => {
    await logout();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-investigation-muted text-xs">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-12 pb-6 border-b border-investigation-border">
          <div>
            <h1 className="investigation-heading text-2xl mb-2">
              Investigation Portal
            </h1>
            <p className="text-xs text-investigation-muted">
              {user?.email} | Classification: CONFIDENTIAL
            </p>
          </div>
          <div className="flex gap-4">
            {user?.is_admin && (
              <Link href="/admin" className="investigation-button text-xs">
                Admin Panel
              </Link>
            )}
            <button onClick={handleLogout} className="investigation-button text-xs">
              Sign Out
            </button>
          </div>
        </div>

        {/* Cases List */}
        <div className="space-y-1">
          <div className="mb-6">
            <h2 className="investigation-heading text-sm mb-1">Active Cases</h2>
            <p className="text-xs text-investigation-muted">
              {cases.filter(c => c.is_active).length} case file(s) available for review
            </p>
          </div>

          {cases.length === 0 ? (
            <div className="investigation-card">
              <p className="text-xs text-investigation-muted">
                No case files available at this time.
              </p>
            </div>
          ) : (
            <div className="space-y-1">
              {cases
                .filter((c) => c.is_active)
                .map((caseItem) => {
                  const caseProgress = progress[caseItem.id];
                  const progressPercent = caseProgress
                    ? Math.round((caseProgress.points_earned / caseProgress.total_points) * 100)
                    : 0;

                  return (
                    <Link
                      key={caseItem.id}
                      href={`/cases/${caseItem.id}`}
                      className="block"
                    >
                      <div className="investigation-card hover:bg-investigation-accent cursor-pointer">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-baseline gap-3 mb-2">
                              <h3 className="investigation-heading text-base">
                                {caseItem.title}
                              </h3>
                              <span className="text-xs text-investigation-muted">
                                {'★'.repeat(caseItem.difficulty)}
                              </span>
                            </div>
                            <p className="text-xs text-investigation-muted mb-4 leading-relaxed">
                              {caseItem.description}
                            </p>
                            <div className="flex items-center gap-6 text-xs">
                              <span className="text-investigation-muted">
                                TOTAL POINTS: {caseItem.total_points}
                              </span>
                              {caseProgress && (
                                <>
                                  <span className="text-investigation-muted">
                                    PROGRESS: {caseProgress.solved_challenges}/{caseProgress.total_challenges} challenges
                                  </span>
                                  <span className="text-investigation-muted">
                                    EARNED: {caseProgress.points_earned} pts ({progressPercent}%)
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                          <div className="ml-6 text-investigation-muted text-xs">
                            →
                          </div>
                        </div>
                      </div>
                    </Link>
                  );
                })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
