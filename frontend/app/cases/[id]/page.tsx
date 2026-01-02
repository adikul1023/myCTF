'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';

interface CaseData {
  id: string;
  title: string;
  slug: string;
  description: string;
  story_background: string;
  investigation_objectives: string;
  difficulty: string;
  points: number;
  is_active: boolean;
  extra_metadata?: {
    subtitle?: string;
    estimated_time_minutes?: number;
    skills_tested?: string[];
    tools_recommended?: string[];
  };
}

interface Artifact {
  id: string;
  name: string;
  description: string;
  artifact_type: string;
  file_size: number;
  mime_type: string;
}

interface CaseStatus {
  is_solved: boolean;
  points_earned: number;
  total_attempts: number;
  last_attempt_at: string | null;
}

export default function CasePage() {
  const params = useParams();
  const caseId = params.id as string;

  const [caseData, setCaseData] = useState<CaseData | null>(null);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [challenges, setChallenges] = useState<any[]>([]);
  const [status, setStatus] = useState<CaseStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({});
  const [submitResults, setSubmitResults] = useState<Record<string, { success: boolean; message: string }>>({});

  useEffect(() => {
    loadCase();
  }, [caseId]);

  const loadCase = async () => {
    const [caseResponse, artifactsResponse, challengesResponse, statusResponse] = await Promise.all([
      api.getCase(caseId),
      api.getCaseArtifacts(caseId),
      api.getChallenges(caseId),
      api.getCaseStatus(caseId),
    ]);

    if (caseResponse.status === 200 && caseResponse.data) {
      setCaseData(caseResponse.data as CaseData);
    }

    if (artifactsResponse.status === 200 && artifactsResponse.data) {
      const data = artifactsResponse.data as any;
      setArtifacts(data.artifacts || data || []);
    }

    if (challengesResponse.status === 200 && challengesResponse.data) {
      setChallenges((challengesResponse.data as any).challenges || []);
    }

    if (statusResponse.status === 200 && statusResponse.data) {
      setStatus(statusResponse.data as CaseStatus);
    }

    setLoading(false);
  };

  const handleSubmit = async (challengeId: string, e: React.FormEvent) => {
    e.preventDefault();
    const answer = answers[challengeId];
    if (!answer || !answer.trim()) return;

    setSubmitting({ ...submitting, [challengeId]: true });
    const newResults = { ...submitResults };
    delete newResults[challengeId];
    setSubmitResults(newResults);

    const response = await api.submitChallengeAnswer(challengeId, answer.trim());

    if (response.status === 200 || response.status === 201) {
      const result = response.data as any;
      if (result.is_correct) {
        setSubmitResults({ ...submitResults, [challengeId]: { success: true, message: `Correct! You earned ${result.points_earned} points.` }});
        setAnswers({ ...answers, [challengeId]: '' });
        loadCase();
      } else {
        setSubmitResults({ ...submitResults, [challengeId]: { success: false, message: 'Incorrect. Try again.' }});
      }
    } else {
      setSubmitResults({ ...submitResults, [challengeId]: { success: false, message: response.error || 'Submission failed' }});
    }
    setSubmitting({ ...submitting, [challengeId]: false });
  };


  const handleDownload = async (artifactId: string, filename: string) => {
    try {
      const response = await api.downloadArtifact(caseId, artifactId);
      if (!response.ok) {
        alert('Failed to download artifact');
        return;
      }
      // Backend streams the file directly
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      // Create safe filename
      const safeName = filename.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_.-]/g, '');
      a.download = safeName.endsWith('.zip') ? safeName : `${safeName}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch {
      alert('Failed to download artifact');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getDifficultyStars = (difficulty: string): string => {
    const map: Record<string, number> = {
      beginner: 1,
      easy: 2,
      intermediate: 3,
      advanced: 4,
      expert: 5,
    };
    return '★'.repeat(map[difficulty?.toLowerCase()] || 3);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-investigation-muted text-xs">Loading case file...</p>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="investigation-card">
          <p className="text-xs text-investigation-muted mb-4">Case file not found</p>
          <Link href="/dashboard" className="investigation-button text-xs">
            Return to dashboard
          </Link>
        </div>
      </div>
    );
  }

  const isSolved = status?.is_solved || false;

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-12 pb-6 border-b border-investigation-border">
          <Link href="/dashboard" className="text-xs text-investigation-muted hover:text-investigation-text mb-4 inline-block">
            ← Return to Dashboard
          </Link>
          <h1 className="investigation-heading text-2xl mb-2">{caseData.title}</h1>
          {caseData.extra_metadata?.subtitle && (
            <p className="text-xs text-investigation-muted mb-4">{caseData.extra_metadata.subtitle}</p>
          )}
          <div className="flex items-center gap-6 text-xs text-investigation-muted">
            <span>DIFFICULTY: {getDifficultyStars(caseData.difficulty)}</span>
            <span>POINTS: {caseData.points}</span>
            {caseData.extra_metadata?.estimated_time_minutes && (
              <span>EST. TIME: {caseData.extra_metadata.estimated_time_minutes} min</span>
            )}
            {isSolved && <span className="text-green-500">✓ SOLVED</span>}
          </div>
        </div>

        <div className="mb-12">
          <h2 className="investigation-heading text-sm mb-4">Case Brief</h2>
          <div className="investigation-card">
            <p className="text-xs leading-relaxed whitespace-pre-wrap text-investigation-muted">
              {caseData.description}
            </p>
          </div>
        </div>

        <div className="mb-12">
          <h2 className="investigation-heading text-sm mb-4">Background</h2>
          <div className="investigation-card">
            <p className="text-xs leading-relaxed whitespace-pre-wrap text-investigation-muted">
              {caseData.story_background}
            </p>
          </div>
        </div>

        <div className="mb-12">
          <h2 className="investigation-heading text-sm mb-4">Investigation Objectives</h2>
          <div className="investigation-card">
            <p className="text-xs leading-relaxed whitespace-pre-wrap text-investigation-muted">
              {caseData.investigation_objectives}
            </p>
          </div>
        </div>

        {artifacts.length > 0 && (
        <div className="mb-12">
          <h2 className="investigation-heading text-sm mb-4">Evidence Files</h2>
          <div className="space-y-1">
            {artifacts.map((artifact) => (
                <div key={artifact.id} className="investigation-card">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="text-xs font-medium mb-1">{artifact.name}</h3>
                      <p className="text-xs text-investigation-muted mb-2">
                        {artifact.description}
                      </p>
                      <p className="text-xs text-investigation-muted">
                        TYPE: {artifact.artifact_type} | SIZE: {formatFileSize(artifact.file_size)}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDownload(artifact.id, artifact.name)}
                      className="investigation-button text-xs ml-6"
                    >
                      Download
                    </button>
                  </div>
                </div>
              ))}
            </div>
        </div>
        )}

        {/* Submit Answer */}
        <div className="mb-12">
          <h2 className="investigation-heading text-sm mb-4">Submit Your Finding</h2>
          {challenges.length > 0 ? (
            <div className="space-y-6">
              {challenges.map((challenge) => (
                <div key={challenge.id} className="investigation-card">
                  <div className="mb-3">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-xs font-medium">{challenge.title}</h3>
                      <span className="text-xs text-investigation-muted">{challenge.points} pts</span>
                    </div>
                    <p className="text-xs text-investigation-muted mb-4">{challenge.question}</p>
                  </div>
                  {challenge.is_solved ? (
                    <div className="text-center py-4 border border-green-500">
                      <div className="text-green-500 text-2xl mb-2">✓</div>
                      <p className="text-xs text-green-500">SOLVED</p>
                    </div>
                  ) : (
                    <form onSubmit={(e) => { e.preventDefault(); }} className="space-y-3">
                      <input
                        type="text"
                        value={answers[challenge.id] || ''}
                        onChange={(e) => setAnswers({ ...answers, [challenge.id]: e.target.value })}
                        className="investigation-input text-sm"
                        placeholder="Enter your answer..."
                        disabled={submitting[challenge.id]}
                      />
                      {submitResults[challenge.id] && (
                        <div className={`text-xs p-2 border ${
                          submitResults[challenge.id].success 
                            ? 'border-green-500 text-green-500' 
                            : 'border-investigation-error text-investigation-error'
                        }`}>
                          {submitResults[challenge.id].message}
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={(e) => handleSubmit(challenge.id, e)}
                        disabled={submitting[challenge.id] || !(answers[challenge.id] || '').trim()}
                        className="investigation-button text-xs"
                      >
                        {submitting[challenge.id] ? 'Verifying...' : 'Submit Answer'}
                      </button>
                      {challenge.user_attempts > 0 && (
                        <p className="text-xs text-investigation-muted">
                          Attempts: {challenge.user_attempts}
                        </p>
                      )}
                    </form>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="investigation-card">
              <p className="text-xs text-investigation-muted">Loading challenges...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
