'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api, ApiException } from '@/lib/api-client';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await api.post<{ ok: boolean; message: string; reset_token?: string }>(
        '/api/auth/request-password-reset',
        { email }
      );
      setSuccess(true);
      // In development, show the reset token link
      if (data.reset_token) {
        console.log(`Reset link: ${window.location.origin}/reset-password?token=${data.reset_token}`);
      }
    } catch (err) {
      if (err instanceof ApiException) {
        setError(err.message || 'Something went wrong');
      } else {
        setError('Network error. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  }

  return success ? (
      <div className='auth-card'>
        <h1 className='auth-title'>Check your email</h1>
        <p className='auth-subtitle'>
          If an account with that email exists, we've sent password reset instructions.
        </p>
        <Link href='/login' className='auth-button auth-button--outline'>
          Back to sign in
        </Link>
      </div>
  ) : (
    <div className='auth-card'>
      <h1 className='auth-title'>Reset your password</h1>
      <p className='auth-subtitle'>Enter your email and we'll send you a reset link.</p>

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

        <button className='auth-button' type='submit' disabled={loading}>
          {loading ? 'Sending…' : 'Send reset link'}
        </button>
      </form>

      <div className='auth-footer'>
        <Link href='/login'>Back to sign in</Link>
      </div>
    </div>
  );
}
