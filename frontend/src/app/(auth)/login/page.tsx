'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api, ApiException } from '@/lib/api-client';

export default function LoginPage() {
  const router = useRouter();
  const { login, hydrate } = useAuthStore((s) => ({ login: s.login, hydrate: s.hydrate }));
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await api.post<{
        ok: boolean;
        access_token: string;
        user: { id: string; email: string; name?: string };
        agency: { id: string; name: string; slug: string; logo_url?: string };
        membership: { role: string; is_primary: boolean };
      }>('/api/auth/login', { email, password });

      // Store in Zustand for client-side state
      login(data.access_token, data.user, data.agency, {
        role: data.membership.role,
        isPrimary: data.membership.is_primary,
      });
      router.push('/');
    } catch (err) {
      if (err instanceof ApiException) {
        setError(err.message || 'Invalid email or password');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className='auth-card'>
      <h1 className='auth-title'>Sign in</h1>
      <p className='auth-subtitle'>Welcome back to your workspace</p>

      <form onSubmit={handleSubmit}>
        {error && <div className='auth-error'>{error}</div>}

        <div className='auth-field'>
          <label htmlFor='email'>Email</label>
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
          <input
            id='password'
            type='password'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder='Enter your password'
            required
            autoComplete='current-password'
          />
        </div>

        <div className='auth-footer' style={{ marginBottom: '1rem', textAlign: 'right' }}>
          <Link href='/forgot-password' style={{ fontSize: '0.875rem' }}>
            Forgot password?
          </Link>
        </div>

        <button className='auth-button' type='submit' disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in'}
        </button>
      </form>

      <div className='auth-footer'>
        Don&apos;t have an account?{' '}
        <Link href='/signup'>Create one</Link>
      </div>
    </div>
  );
}
