'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { getCurrentUser, type User } from '@/lib/auth';

interface Case {
  id: string;
  title: string;
  description: string;
  difficulty: number;
  total_points: number;
  is_active: boolean;
  created_at: string;
}

export default function AdminPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    narrative: '',
    difficulty: 3,
    total_points: 0,
    is_active: true,
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      router.push('/login');
      return;
    }

    if (!currentUser.is_admin) {
      router.push('/dashboard');
      return;
    }

    setUser(currentUser);

    const response = await api.getCases();
    if (response.status === 200 && response.data) {
      setCases(response.data as Case[]);
    }

    setLoading(false);
  };

  const handleCreateCase = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setCreating(true);

    const response = await api.createCase(formData);

    if (response.status === 201) {
      setShowCreateForm(false);
      setFormData({
        title: '',
        description: '',
        narrative: '',
        difficulty: 3,
        total_points: 0,
        is_active: true,
      });
      await loadData();
    } else {
      setError(response.error || 'Failed to create case');
    }

    setCreating(false);
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
        <div className="mb-12 pb-6 border-b border-investigation-border">
          <Link
            href="/dashboard"
            className="text-xs text-investigation-muted hover:text-investigation-text mb-4 inline-block"
          >
            ← Return to Dashboard
          </Link>
          <h1 className="investigation-heading text-2xl mb-2">Admin Panel</h1>
          <p className="text-xs text-investigation-muted">
            Case management and system administration
          </p>
        </div>

        {/* Create Case Section */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-4">
            <h2 className="investigation-heading text-sm">Case Management</h2>
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="investigation-button text-xs"
            >
              {showCreateForm ? 'Cancel' : 'Create New Case'}
            </button>
          </div>

          {showCreateForm && (
            <div className="investigation-card mb-6">
              <form onSubmit={handleCreateCase} className="space-y-4">
                <div>
                  <label className="block text-xs mb-2 uppercase tracking-wider">
                    Case Title
                  </label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="investigation-input text-xs"
                    required
                    disabled={creating}
                  />
                </div>

                <div>
                  <label className="block text-xs mb-2 uppercase tracking-wider">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) =>
                      setFormData({ ...formData, description: e.target.value })
                    }
                    className="investigation-input text-xs"
                    rows={3}
                    required
                    disabled={creating}
                  />
                </div>

                <div>
                  <label className="block text-xs mb-2 uppercase tracking-wider">
                    Narrative
                  </label>
                  <textarea
                    value={formData.narrative}
                    onChange={(e) =>
                      setFormData({ ...formData, narrative: e.target.value })
                    }
                    className="investigation-input text-xs"
                    rows={6}
                    required
                    disabled={creating}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs mb-2 uppercase tracking-wider">
                      Difficulty (1-5)
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="5"
                      value={formData.difficulty}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          difficulty: parseInt(e.target.value),
                        })
                      }
                      className="investigation-input text-xs"
                      required
                      disabled={creating}
                    />
                  </div>

                  <div>
                    <label className="block text-xs mb-2 uppercase tracking-wider">
                      Total Points
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={formData.total_points}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          total_points: parseInt(e.target.value),
                        })
                      }
                      className="investigation-input text-xs"
                      required
                      disabled={creating}
                    />
                  </div>
                </div>

                <div>
                  <label className="flex items-center gap-2 text-xs">
                    <input
                      type="checkbox"
                      checked={formData.is_active}
                      onChange={(e) =>
                        setFormData({ ...formData, is_active: e.target.checked })
                      }
                      disabled={creating}
                    />
                    <span className="uppercase tracking-wider">Active</span>
                  </label>
                </div>

                {error && (
                  <div className="text-xs text-investigation-error border border-investigation-error p-3">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={creating}
                  className="investigation-button text-xs"
                >
                  {creating ? 'Creating...' : 'Create Case'}
                </button>
              </form>
            </div>
          )}
        </div>

        {/* Cases List */}
        <div>
          <h2 className="investigation-heading text-sm mb-4">All Cases</h2>
          {cases.length === 0 ? (
            <div className="investigation-card">
              <p className="text-xs text-investigation-muted">No cases found.</p>
            </div>
          ) : (
            <div className="space-y-1">
              {cases.map((caseItem) => (
                <div key={caseItem.id} className="investigation-card">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-baseline gap-3 mb-2">
                        <h3 className="investigation-heading text-sm">
                          {caseItem.title}
                        </h3>
                        <span className="text-xs text-investigation-muted">
                          {'★'.repeat(caseItem.difficulty)}
                        </span>
                        {caseItem.is_active ? (
                          <span className="text-xs text-investigation-success">ACTIVE</span>
                        ) : (
                          <span className="text-xs text-investigation-muted">INACTIVE</span>
                        )}
                      </div>
                      <p className="text-xs text-investigation-muted mb-2">
                        {caseItem.description}
                      </p>
                      <div className="flex items-center gap-6 text-xs text-investigation-muted">
                        <span>ID: {caseItem.id}</span>
                        <span>POINTS: {caseItem.total_points}</span>
                        <span>
                          CREATED: {new Date(caseItem.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                    <Link
                      href={`/cases/${caseItem.id}`}
                      className="investigation-button text-xs ml-6"
                    >
                      View
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
