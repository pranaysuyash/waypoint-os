'use client';

import { useState, useReducer, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api, ApiException } from '@/lib/api-client';
import { DEFAULT_AUTH_REDIRECT, resolveSafeRedirect } from '@/lib/auth-redirect';
import { getPasswordStrength } from '@/lib/password-strength';
import { clearDepartureBoardHandoff, readDepartureBoardHandoff, type DepartureBoardHandoff } from '@/lib/departure-board-handoff';

type SignupFormState = { name: string; email: string; password: string; confirmPassword: string; showPassword: boolean; showConfirmPassword: boolean; agencyName: string; showAgency: boolean; termsAccepted: boolean };
type SignupFormAction = { type: 'SET_FIELD'; field: keyof SignupFormState; value: string | boolean };
function signupFormReducer(state: SignupFormState, action: SignupFormAction): SignupFormState {
  switch (action.type) {
    case 'SET_FIELD': return { ...state, [action.field]: action.value };
    default: return state;
  }
}

function SignupPageInner() {
  const { push } = useRouter();
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);
  const sourceParam = getSearchParam('source');
  const caseParam = getSearchParam('case');
  const iataParam = getSearchParam('iata');
  const hydrate = useAuthStore((s) => s.hydrate);
  const [formState, dispatch] = useReducer(signupFormReducer, { name: '', email: '', password: '', confirmPassword: '', showPassword: false, showConfirmPassword: false, agencyName: '', showAgency: false, termsAccepted: false });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionHandoff] = useState<DepartureBoardHandoff | null>(() => readDepartureBoardHandoff());
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
  const passwordStrength = getPasswordStrength(formState.password);
  const passwordsMatch = formState.confirmPassword.length > 0 && formState.password === formState.confirmPassword;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (formState.password !== formState.confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }

    try {
      const body: Record<string, string | boolean> = { email: formState.email, password: formState.password, terms_accepted: formState.termsAccepted };
      if (formState.name) body.name = formState.name;
      if (formState.agencyName) body.agency_name = formState.agencyName;

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
      // The handoff is now consumed into the redirect URL — clear it so a
      // claimed case never resurfaces as a stale banner on a future visit.
      clearDepartureBoardHandoff();
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
      {showHandoffBanner && formattedCaseName ? (
        <div
          data-testid='signup-departure-board-context'
          className='auth-handoff-banner'
        >
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
      <h1 className='auth-title'>Create your workspace</h1>
      <p className='auth-subtitle'>
        Set up your agency workspace and client departure desk
      </p>

      <form onSubmit={handleSubmit}>
        {error && <div className='auth-error'>{error}</div>}

        <div className='auth-field'>
          <label htmlFor='name'>Full name</label>
          <input
            id='name'
            type='text'
            value={formState.name}
            onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'name', value: e.target.value })}
            placeholder='e.g. Alex Rivera'
            autoComplete='name'
          />
        </div>

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
          <label htmlFor='password'>Password</label>
          <div className='auth-password-wrap'>
            <input
              id='password'
              type={formState.showPassword ? 'text' : 'password'}
              value={formState.password}
              onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'password', value: e.target.value })}
              placeholder='Minimum 8 characters'
              required
              minLength={8}
              autoComplete='new-password'
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
          <div className='auth-password-meta'>
            <div className='auth-strength-segments' aria-hidden='true'>
              {[1, 2, 3, 4].map((seg) => {
                const activeCount = !formState.password
                  ? 0
                  : passwordStrength.label === 'Strong'
                  ? 4
                  : passwordStrength.label === 'Good'
                  ? 3
                  : passwordStrength.label === 'Fair'
                  ? 2
                  : 1;
                const tierClass = `auth-strength-segment--active-${passwordStrength.label.toLowerCase()}`;
                return (
                  <span
                    key={seg}
                    className={`auth-strength-segment ${seg <= activeCount ? tierClass : ''}`}
                  />
                );
              })}
            </div>
            <span className='auth-strength-label'>
              {formState.password ? `Level: ${passwordStrength.label}` : 'Min. 8 chars'}
            </span>
          </div>
        </div>

        <div className='auth-field'>
          <label htmlFor='confirm-password'>Confirm password</label>
          <div className='auth-password-wrap'>
            <input
              id='confirm-password'
              type={formState.showConfirmPassword ? 'text' : 'password'}
              value={formState.confirmPassword}
              onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'confirmPassword', value: e.target.value })}
              placeholder='Re-enter password'
              required
              minLength={8}
              autoComplete='new-password'
            />
            <button
              type='button'
              className='auth-password-toggle'
              onClick={() => dispatch({ type: 'SET_FIELD', field: 'showConfirmPassword', value: !formState.showConfirmPassword })}
              aria-label={formState.showConfirmPassword ? 'Hide password confirmation' : 'Show password confirmation'}
              aria-pressed={formState.showConfirmPassword}
            >
              {formState.showConfirmPassword ? 'Hide' : 'Show'}
            </button>
          </div>
          {formState.confirmPassword.length > 0 && (
            <div className={`auth-match-label ${passwordsMatch ? 'auth-match-label--ok' : 'auth-match-label--error'}`}>
              {passwordsMatch ? 'Passwords match' : 'Passwords do not match'}
            </div>
          )}
        </div>

        {!formState.showAgency ? (
          <button
            type='button'
            className='auth-button--ghost'
            onClick={() => dispatch({ type: 'SET_FIELD', field: 'showAgency', value: true })}
          >
            + Customize agency name (optional)
          </button>
        ) : null}

        <div className={`auth-expandable-drawer ${formState.showAgency ? 'auth-expandable-drawer--open' : ''}`}>
          <div className='auth-expandable-content'>
            <div className='auth-field'>
              <label htmlFor='agency'>Agency name</label>
              <input
                id='agency'
                type='text'
                value={formState.agencyName}
                onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'agencyName', value: e.target.value })}
                placeholder='e.g. Meridian Travel Co.'
                autoFocus={formState.showAgency}
              />
            </div>
          </div>
        </div>

        <div className='auth-field-checkbox'>
          <div className='auth-checkbox-custom'>
            <input
              id='terms'
              type='checkbox'
              checked={formState.termsAccepted}
              onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'termsAccepted', value: e.target.checked })}
              required
            />
            <div className='auth-checkbox-box' aria-hidden='true'>
              <svg className='auth-checkbox-icon' viewBox='0 0 12 12' fill='none'>
                <path d='M2 6L4.8 9L10 3' />
              </svg>
            </div>
          </div>
          <label htmlFor='terms'>
            I agree to the{' '}
            <Link href='/terms'>Terms of Service</Link>{' '}
            and{' '}
            <Link href='/privacy'>Privacy Policy</Link>
          </label>
        </div>

        <button className='auth-button' type='submit' disabled={loading || !formState.termsAccepted}>
          <span className='auth-button-inner'>
            {loading ? (
              <>
                <span className='auth-spinner-telemetry' aria-hidden='true' />
                <span>Preparing agency desk…</span>
              </>
            ) : (
              <>
                <span>Create workspace</span>
                <span className='auth-button-arrow' aria-hidden='true'>→</span>
              </>
            )}
          </span>
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
