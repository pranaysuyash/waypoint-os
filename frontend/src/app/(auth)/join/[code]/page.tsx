'use client';

/**
 * Agent join page - /join/[code]
 *
 * Allows an agent to create an account and join an existing agency via a
 * workspace invitation code shared by the agency owner or admin.
 *
 * Flow:
 *   1. On mount: validate the code via GET /api/auth/validate-code/[code]
 *      - Shows agency name on success, error state on failure
 *   2. User fills in name, email, password
 *   3. On submit: POST /api/auth/join with { workspace_code, email, password, name }
 *   4. On success: hydrate auth store (cookies set by backend) → redirect to /overview
 *
 * Design decisions:
 *   - Code is multi-use (invitation link, not one-time token). Owner revokes to stop joins.
 *   - Role defaults to junior_agent regardless of code_type. Promoted by owner post-onboarding.
 *   - Validation uses 404 for any invalid code to avoid leaking whether a code exists.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { ApiException } from '@/lib/api-client';

interface ValidateCodeResponse {
  valid: boolean;
  agency_name: string;
  agency_id: string;
  code_type: string;
}

type PageState =
  | { phase: 'loading' }
  | { phase: 'invalid'; reason: string }
  | { phase: 'ready'; agency: ValidateCodeResponse }
  | { phase: 'submitting'; agency: ValidateCodeResponse }
  | { phase: 'error'; agency: ValidateCodeResponse; error: string };

export default function JoinPage() {
  const params = useParams<{ code: string }>();
  const code = params.code;
  const { replace } = useRouter();
  const hydrate = useAuthStore((s) => s.hydrate);

  const [state, setState] = useState<PageState>({ phase: 'loading' });
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Step 1: validate code on mount
// react-doctor-disable-next-line react-doctor/no-fetch-in-effect, react-doctor/no-cascading-set-state, react-doctor/nextjs-no-client-fetch-for-server-data — dynamic code param + auth via credentials:include; server component can't handle
  useEffect(() => {
    if (!code) {
      setState({ phase: 'invalid', reason: 'No invitation code provided.' });
      return;
    }

    let cancelled = false;

    async function validate() {
      try {
        const res = await fetch(`/api/auth/validate-code/${encodeURIComponent(code)}`, {
          cache: 'no-store',
          credentials: 'include',
        });

        if (cancelled) return;

        if (res.status === 404) {
          setState({ phase: 'invalid', reason: 'This invitation link is invalid or has been revoked.' });
          return;
        }

        if (!res.ok) {
          setState({ phase: 'invalid', reason: 'Unable to validate invitation. Please try again.' });
          return;
        }

        const data: ValidateCodeResponse = await res.json();
        setState({ phase: 'ready', agency: data });
      } catch {
        if (!cancelled) {
          setState({ phase: 'invalid', reason: 'Network error. Please check your connection.' });
        }
      }
    }

    validate();
    return () => { cancelled = true; };
  }, [code]);

  // Step 2: submit join form
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (state.phase !== 'ready' && state.phase !== 'error') return;

    const agency = state.phase === 'ready' ? state.agency : (state as Extract<PageState, { phase: 'error' }>).agency;
    setState({ phase: 'submitting', agency });

    try {
      const res = await fetch('/api/auth/join', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_code: code,
          email,
          password,
          name: name || undefined,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({ error: 'Join failed' }));
        setState({ phase: 'error', agency, error: data.error || 'Join failed' });
        return;
      }

      // Backend set auth cookies - rehydrate store then navigate
      await hydrate();
      replace('/overview');
    } catch (err) {
      const message = err instanceof ApiException ? err.message : 'Network error. Please try again.';
      setState({ phase: 'error', agency, error: message });
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  if (state.phase === 'loading') {
    return (
      <div className="auth-card">
        <div className="flex flex-col items-center gap-3 py-8">
          <div className="size-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          <p className="text-sm text-foreground">Checking invitation…</p>
        </div>
      </div>
    );
  }

  if (state.phase === 'invalid') {
    return (
      <div className="auth-card">
        <h1 className="auth-title">Invalid invitation</h1>
        <p className="auth-subtitle" style={{ color: '#f85149' }}>{state.reason}</p>
        <div className="auth-footer" style={{ marginTop: '1.5rem' }}>
          <Link href="/login">Sign in to an existing account</Link>
        </div>
      </div>
    );
  }

  const agency = state.phase === 'error' ? state.agency : state.agency;
  const isSubmitting = state.phase === 'submitting';
  const submitError = state.phase === 'error' ? state.error : null;

  return (
    <div className="auth-card">
      <h1 className="auth-title">Join {agency.agency_name}</h1>
      <p className="auth-subtitle">
        You&apos;ve been invited to join this workspace. Create your account to get started.
      </p>

      <form onSubmit={handleSubmit}>
        {submitError && <div className="auth-error">{submitError}</div>}

        <div className="auth-field">
          <label htmlFor="name">Full name</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Jane Smith"
            autoComplete="name"
            disabled={isSubmitting}
          />
        </div>

        <div className="auth-field">
          <label htmlFor="email">Work email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@agency.com"
            required
            autoComplete="email"
            disabled={isSubmitting}
          />
        </div>

        <div className="auth-field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Minimum 8 characters"
            required
            minLength={8}
            autoComplete="new-password"
            disabled={isSubmitting}
          />
        </div>

        <button
          className="auth-button"
          type="submit"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Joining workspace…' : `Join ${agency.agency_name}`}
        </button>
      </form>

      <div className="auth-footer">
        Already have an account?{' '}
        <Link href="/login">Sign in</Link>
      </div>
    </div>
  );
}
