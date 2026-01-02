'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { register } from '@/lib/auth';

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [inviteCode, setInviteCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passphrases do not match');
      return;
    }

    if (password.length < 12) {
      setError('Passphrase must be at least 12 characters');
      return;
    }

    if (!inviteCode) {
      setError('Invite code is required');
      return;
    }

    if (username.length < 3) {
      setError('Username must be at least 3 characters');
      return;
    }

    setLoading(true);

    const result = await register(email, username, password, inviteCode);

    if (result.success) {
      router.push('/login');
    } else {
      setError(result.error || 'Registration failed');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="investigation-card max-w-md w-full">
        <div className="mb-8">
          <h1 className="investigation-heading text-xl mb-2">
            Access Request
          </h1>
          <p className="text-investigation-muted text-xs">
            Submit credentials for authorization review
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="inviteCode" className="block text-xs mb-2 uppercase tracking-wider">
              Invite Code <span className="text-investigation-error">*</span>
            </label>
            <input
              id="inviteCode"
              type="text"
              value={inviteCode}
              onChange={(e) => setInviteCode(e.target.value)}
              className="investigation-input"
              placeholder="XXXX-XXXX-XXXX-XXXX"
              required
              disabled={loading}
            />
          </div>

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
            <label htmlFor="username" className="block text-xs mb-2 uppercase tracking-wider">
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="investigation-input"
              placeholder="analyst_smith"
              required
              disabled={loading}
            />
            <p className="text-xs text-investigation-muted mt-1">
              Alphanumeric and underscores only
            </p>
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
            <p className="text-xs text-investigation-muted mt-1">
              Minimum 12 characters
            </p>
          </div>

          <div>
            <label htmlFor="confirmPassword" className="block text-xs mb-2 uppercase tracking-wider">
              Confirm Passphrase
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
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
            {loading ? 'Submitting...' : 'Submit Request'}
          </button>
        </form>

        <div className="mt-6 pt-6 border-t border-investigation-border">
          <p className="text-xs text-investigation-muted">
            Already authorized?{' '}
            <Link href="/login" className="text-investigation-text hover:underline">
              Authenticate here
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
