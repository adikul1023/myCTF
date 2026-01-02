'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { login } from '@/lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await login(email, password);

    if (result.success) {
      router.push('/dashboard');
    } else {
      setError(result.error || 'Authentication failed');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="investigation-card max-w-md w-full">
        <div className="mb-8">
          <h1 className="investigation-heading text-xl mb-2">
            Investigation Portal
          </h1>
          <p className="text-investigation-muted text-xs">
            Authorized Personnel Only
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-xs mb-2 uppercase tracking-wider">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="investigation-input"
              placeholder="analyst@agency.gov"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs mb-2 uppercase tracking-wider">
              Passphrase
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="investigation-input"
              placeholder="••••••••••••"
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className="border border-investigation-error bg-investigation-surface p-3 text-xs">
              <span className="text-investigation-muted">ERROR: </span>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="investigation-button w-full"
          >
            {loading ? 'Authenticating...' : 'Authenticate'}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-investigation-border">
          <p className="text-xs text-investigation-muted">
            Request access:{' '}
            <Link href="/register" className="text-investigation-text hover:underline">
              Submit credentials
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
