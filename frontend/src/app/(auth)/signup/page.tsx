'use client';

import { useState, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api, ApiException } from '@/lib/api-client';
import { DEFAULT_AUTH_REDIRECT, resolveSafeRedirect } from '@/lib/auth-redirect';
import { getPasswordStrength } from '@/lib/password-strength';

function SignupPageInner() {
  const { push } = useRouter();
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);
  const hydrate = useAuthStore((s) => s.hydrate);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [agencyName, setAgencyName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showAgency, setShowAgency] = useState(false);
  const redirectPath = resolveSafeRedirect(
    getSearchParam('redirect') || getSearchParam('next'),
    DEFAULT_AUTH_REDIRECT,
  );
  const passwordStrength = getPasswordStrength(password);
  const passwordsMatch = confirmPassword.length > 0 && password === confirmPassword;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const body: Record<string, string> = { email, password };
      if (name) body.name = name;
      if (agencyName) body.agency_name = agencyName;

      const data = await api.post<{
        ok: boolean;
        user: { id: string; email: string; name?: string };
        agency: { id: string; name: string; slug: string; logo_url?: string };
        membership: { role: string; is_primary: boolean };
      }>('/api/auth/signup', body);

      if (!data.ok) {
        setError('Signup failed');
        return;
      }

      // Rehydrate auth state from the httpOnly cookies via /api/auth/me
      await hydrate();
      push(redirectPath);
    } catch (err) {
      if (err instanceof ApiException) {
        setError(err.message || 'Signup failed');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className='auth-card'>
      <h1 className='auth-title'>Create your workspace</h1>
      <p className='auth-subtitle'>
        Set up your agency in seconds
      </p>

      <form onSubmit={handleSubmit}>
        {error && <div className='auth-error'>{error}</div>}

        <div className='auth-field'>
          <label htmlFor='name'>Full name</label>
          <input
            id='name'
            type='text'
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder='Jane Smith'
            autoComplete='name'
          />
        </div>

        <div className='auth-field'>
          <label htmlFor='email'>Work email</label>
          <input
            id='email'
            type='email'
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder='you@agency.com'
            required
            autoComplete='email'
          />
        </div>

        <div className='auth-field'>
          <label htmlFor='password'>Password</label>
          <div className='auth-password-wrap'>
            <input
              id='password'
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder='Minimum 8 characters'
              required
              minLength={8}
              autoComplete='new-password'
            />
            <button
              type='button'
              className='auth-password-toggle'
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={showPassword}
            >
              {showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
          <div className='auth-password-meta'>
            <div className='auth-strength-track' aria-hidden='true'>
              <span
                className={`auth-strength-fill auth-strength-fill--${passwordStrength.label.toLowerCase()}`}
                style={{ width: `${Math.max(10, (passwordStrength.score / 5) * 100)}%` }}
              />
            </div>
            <span className='auth-strength-label'>Strength: {passwordStrength.label}</span>
          </div>
        </div>

        <div className='auth-field'>
          <label htmlFor='confirm-password'>Confirm password</label>
          <div className='auth-password-wrap'>
            <input
              id='confirm-password'
              type={showConfirmPassword ? 'text' : 'password'}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder='Re-enter password'
              required
              minLength={8}
              autoComplete='new-password'
            />
            <button
              type='button'
              className='auth-password-toggle'
              onClick={() => setShowConfirmPassword((prev) => !prev)}
              aria-label={showConfirmPassword ? 'Hide password confirmation' : 'Show password confirmation'}
              aria-pressed={showConfirmPassword}
            >
              {showConfirmPassword ? 'Hide' : 'Show'}
            </button>
          </div>
          {confirmPassword.length > 0 && (
            <div className={`auth-match-label ${passwordsMatch ? 'auth-match-label--ok' : 'auth-match-label--error'}`}>
              {passwordsMatch ? 'Passwords match' : 'Passwords do not match'}
            </div>
          )}
        </div>

        {!showAgency ? (
          <button
            type='button'
            className='auth-button'
            style={{ background: '#1c2128', color: '#8b949e' }}
            onClick={() => setShowAgency(true)}
          >
            Customize agency name (optional)
          </button>
        ) : (
          <div className='auth-field'>
            <label htmlFor='agency'>Agency name</label>
            <input
              id='agency'
              type='text'
              value={agencyName}
              onChange={(e) => setAgencyName(e.target.value)}
              placeholder='My Travel Agency'
              autoFocus
            />
          </div>
        )}

        <button className='auth-button' type='submit' disabled={loading}>
          {loading ? 'Creating workspace…' : 'Create workspace'}
        </button>
      </form>

      <div className='auth-footer'>
        Already have an account?{' '}
        <Link href='/login'>Sign in</Link>
      </div>
    </div>
  );
}

export default function SignupPage() {
  return (
    <Suspense fallback={<div className="auth-card"><p className="auth-subtitle">Loading…</p></div>}>
      <SignupPageInner />
    </Suspense>
  );
}
