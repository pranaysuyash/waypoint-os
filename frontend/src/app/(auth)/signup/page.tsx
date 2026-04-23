'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api, ApiException } from '@/lib/api-client';

export default function SignupPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useAuthStore((s) => s.login);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [agencyName, setAgencyName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showAgency, setShowAgency] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const body: Record<string, string> = { email, password };
      if (name) body.name = name;
      if (agencyName) body.agency_name = agencyName;

      const data = await api.post<{
        ok: boolean;
        access_token: string;
        user: { id: string; email: string; name?: string };
        agency: { id: string; name: string; slug: string; logo_url?: string };
        membership: { role: string; is_primary: boolean };
      }>('/api/auth/signup', body);

      // Store in Zustand for client-side state
      login(data.access_token, data.user, data.agency, {
        role: data.membership.role,
        isPrimary: data.membership.is_primary,
      });
      router.push(searchParams.get('redirect') || '/overview');
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
          <input
            id='password'
            type='password'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder='Minimum 8 characters'
            required
            minLength={8}
            autoComplete='new-password'
          />
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
          {loading ? 'Creating workspace...' : 'Create workspace'}
        </button>
      </form>

      <div className='auth-footer'>
        Already have an account?{' '}
        <Link href='/login'>Sign in</Link>
      </div>
    </div>
  );
}
