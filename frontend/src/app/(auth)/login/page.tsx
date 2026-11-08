'use client';

import { useState, useReducer, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api, ApiException } from '@/lib/api-client';
import { DEFAULT_AUTH_REDIRECT, formatAuthRedirectLabel, resolveSafeRedirect } from '@/lib/auth-redirect';
import { clearDepartureBoardHandoff, readDepartureBoardHandoff, type DepartureBoardHandoff } from '@/lib/departure-board-handoff';

type LoginFormState = { email: string; password: string; showPassword: boolean };
type LoginFormAction = { type: 'SET_FIELD'; field: keyof LoginFormState; value: string | boolean };
function loginFormReducer(state: LoginFormState, action: LoginFormAction): LoginFormState {
  switch (action.type) {
    case 'SET_FIELD': return { ...state, [action.field]: action.value };
    default: return state;
  }
}

function LoginPageInner() {
  const { push } = useRouter();
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);
  const hydrate = useAuthStore((s) => s.hydrate);
  const [formState, dispatch] = useReducer(loginFormReducer, { email: '', password: '', showPassword: false });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionHandoff] = useState<DepartureBoardHandoff | null>(() => readDepartureBoardHandoff());

  const sourceParam = getSearchParam('source');
  const caseParam = getSearchParam('case');
  const iataParam = getSearchParam('iata');
  const formattedCaseName = caseParam
    ? caseParam
        .split('-')
        .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : ''))
        .join(' ')
    : sessionHandoff?.caseTitle ?? null;
  const resolvedIataCode = iataParam ?? sessionHandoff?.iataCode ?? null;
  const showHandoffBanner =
    (sourceParam === 'departure-board' || Boolean(sessionHandoff)) &&
    Boolean(formattedCaseName);

  const handoffRedirect =
    showHandoffBanner && formattedCaseName
      ? `/workbench?source=departure-board&case=${encodeURIComponent(caseParam || sessionHandoff?.caseSlug || '')}&iata=${encodeURIComponent(resolvedIataCode || '')}${sessionHandoff?.prefill ? `&prefill=${encodeURIComponent(sessionHandoff.prefill)}` : ''}`
      : DEFAULT_AUTH_REDIRECT;

  const redirectPath = resolveSafeRedirect(
    getSearchParam('redirect') || getSearchParam('next'),
    handoffRedirect,
  );
  const redirectLabel = formatAuthRedirectLabel(redirectPath);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Login sets httpOnly cookies (access_token, refresh_token).
      // No tokens are returned in the response body - they are cookie-only.
      const data = await api.post<{
        ok: boolean;
        user: { id: string; email: string; name?: string };
        agency: { id: string; name: string; slug: string; logo_url?: string };
        membership: { role: string; is_primary: boolean };
      }>('/api/auth/login', { email: formState.email, password: formState.password });

      if (!data.ok) {
        setError('Login failed');
        return;
      }

      // Rehydrate auth state from the httpOnly cookies via /api/auth/me
      await hydrate();
      // The handoff is now consumed into the redirect URL — clear it so a
      // claimed case never resurfaces as a stale banner on a future visit.
      clearDepartureBoardHandoff();
      push(redirectPath);
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
      {showHandoffBanner && formattedCaseName ? (
        <div className='auth-handoff-banner'>
          <div className='auth-handoff-left'>
            <span className='auth-handoff-beacon' aria-hidden='true' />
            <div className='auth-handoff-text-group'>
              <span className='auth-handoff-kicker'>Case Queue</span>
              <span className='auth-handoff-title'>
                {formattedCaseName} Inquiry will open in Workbench
              </span>
            </div>
          </div>
          {resolvedIataCode ? (
            <span className='auth-handoff-badge'>
              <span className='auth-handoff-flight-icon' aria-hidden='true'>✈</span>
              {resolvedIataCode}
            </span>
          ) : null}
        </div>
      ) : null}
      <h1 className='auth-title'>Sign in</h1>
      <p className='auth-subtitle'>
        Welcome back. Continue to <span className='auth-subtle-strong'>{redirectLabel}</span>.
      </p>

      <form onSubmit={handleSubmit}>
        {error && <div className='auth-error'>{error}</div>}

        <div className='auth-field'>
          <label htmlFor='email'>Work email</label>
          <input
            id='email'
            type='email'
            value={formState.email}
            onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'email', value: e.target.value })}
            placeholder='advisor@agency.com'
            required
            autoComplete='email'
          />
        </div>

        <div className='auth-field'>
          <div className='auth-field-header'>
            <label htmlFor='password'>Password</label>
            <Link href='/forgot-password' className='auth-field-aux-link'>
              Forgot password?
            </Link>
          </div>
          <div className='auth-password-wrap'>
            <input
              id='password'
              type={formState.showPassword ? 'text' : 'password'}
              value={formState.password}
              onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'password', value: e.target.value })}
              placeholder='Enter your password'
              required
              autoComplete='current-password'
            />
            <button
              type='button'
              className='auth-password-toggle'
              onClick={() => dispatch({ type: 'SET_FIELD', field: 'showPassword', value: !formState.showPassword })}
              aria-label={formState.showPassword ? 'Hide password' : 'Show password'}
              aria-pressed={formState.showPassword}
            >
              {formState.showPassword ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        <button className='auth-button' type='submit' disabled={loading}>
          <span className='auth-button-inner'>
            {loading ? (
              <>
                <span className='auth-spinner-telemetry' aria-hidden='true' />
                <span>Signing in…</span>
              </>
            ) : (
              <>
                <span>Sign in</span>
                <span className='auth-button-arrow' aria-hidden='true'>→</span>
              </>
            )}
          </span>
        </button>
      </form>

      <div className='auth-footer'>
        Don&apos;t have an account?{' '}
        <Link href='/signup'>Create one</Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="auth-card"><p className="auth-subtitle">Loading…</p></div>}>
      <LoginPageInner />
    </Suspense>
  );
}
