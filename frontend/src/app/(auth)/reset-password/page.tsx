'use client';

import { useState, useReducer, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { api, ApiException } from '@/lib/api-client';

type ResetFormState = { password: string; confirmPassword: string; showPassword: boolean; showConfirmPassword: boolean };
type ResetFormAction = { type: 'SET_FIELD'; field: keyof ResetFormState; value: string | boolean };
function resetFormReducer(state: ResetFormState, action: ResetFormAction): ResetFormState {
  switch (action.type) {
    case 'SET_FIELD': return { ...state, [action.field]: action.value };
    default: return state;
  }
}

function ResetPasswordPageInner() {
  const searchParams = useSearchParams();
  const getSearchParam = searchParams.get.bind(searchParams);
  const token = getSearchParam('token') || '';

  const [formState, dispatch] = useReducer(resetFormReducer, { password: '', confirmPassword: '', showPassword: false, showConfirmPassword: false });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');

    if (formState.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    if (formState.password !== formState.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const data = await api.post<{ ok: boolean; message: string }>(
        '/api/auth/confirm-password-reset',
        { token, new_password: formState.password }
      );
      setSuccess(true);
    } catch (err) {
      if (err instanceof ApiException) {
        setError(err.message || 'Invalid or expired reset token');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    return (
      <div className='auth-card'>
        <h1 className='auth-title'>Invalid reset link</h1>
        <p className='auth-subtitle'>This password reset link is missing a token.</p>
        <Link href='/forgot-password' className='auth-button auth-button--outline'>
          Request a new link
        </Link>
      </div>
    );
  }

  return success ? (
      <div className='auth-card'>
        <h1 className='auth-title'>Password updated</h1>
        <p className='auth-subtitle'>
          Your password has been reset successfully. You can now sign in with your new password.
        </p>
        <Link href='/login' className='auth-button'>
          Sign in
        </Link>
      </div>
  ) : (
    <div className='auth-card'>
      <h1 className='auth-title'>Set new password</h1>
      <p className='auth-subtitle'>Enter your new password below.</p>

      <form onSubmit={handleSubmit}>
        {error && <div className='auth-error'>{error}</div>}

        <div className='auth-field'>
          <label htmlFor='password'>New password</label>
          <div className='auth-password-wrap'>
            <input
              id='password'
              type={formState.showPassword ? 'text' : 'password'}
              value={formState.password}
              onChange={(e) => dispatch({ type: 'SET_FIELD', field: 'password', value: e.target.value })}
              placeholder='At least 8 characters'
              required
              autoComplete='new-password'
              minLength={8}
            />
            <button
              type='button'
              className='auth-password-toggle'
              onClick={() => dispatch({ type: 'SET_FIELD', field: 'showPassword', value: !formState.showPassword })}
              aria-label={formState.showPassword ? 'Hide new password' : 'Show new password'}
              aria-pressed={formState.showPassword}
            >
              {formState.showPassword ? 'Hide' : 'Show'}
            </button>
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
              placeholder='Re-enter your password'
              required
              autoComplete='new-password'
            />
            <button
              type='button'
              className='auth-password-toggle'
              onClick={() => dispatch({ type: 'SET_FIELD', field: 'showConfirmPassword', value: !formState.showConfirmPassword })}
              aria-label={formState.showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
              aria-pressed={formState.showConfirmPassword}
            >
              {formState.showConfirmPassword ? 'Hide' : 'Show'}
            </button>
          </div>
        </div>

        <button className='auth-button' type='submit' disabled={loading}>
          {loading ? 'Updating…' : 'Reset password'}
        </button>
      </form>

      <div className='auth-footer'>
        <Link href='/login'>Back to sign in</Link>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="auth-card"><p className="auth-subtitle">Loading…</p></div>}>
      <ResetPasswordPageInner />
    </Suspense>
  );
}
