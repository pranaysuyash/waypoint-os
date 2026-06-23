'use client';

import Link from 'next/link';
import { LockKeyhole, ArrowRight } from 'lucide-react';

export function ProtectedSurfaceNotice({
  surfaceName,
  redirectTarget,
  description,
}: {
  surfaceName: string;
  redirectTarget: string;
  description: string;
}) {
  const loginHref = `/login?redirect=${encodeURIComponent(redirectTarget)}`;

  return (
    <div className='min-h-screen bg-[#080a0c] text-[#e6edf3] flex items-center justify-center p-6'>
      <div className='w-full max-w-lg rounded-2xl border border-[#30363d] bg-[#0d1117] p-6 shadow-2xl'>
        <div className='flex items-start gap-4'>
          <div className='flex size-11 shrink-0 items-center justify-center rounded-xl border border-[#30363d] bg-[#161b22]'>
            <LockKeyhole className='size-5 text-[#58a6ff]' aria-hidden='true' />
          </div>
          <div className='min-w-0'>
            <p className='text-xs font-semibold uppercase tracking-[0.16em] text-[#8b949e]'>Protected surface</p>
            <h1 className='mt-1 text-2xl font-semibold'>{surfaceName}</h1>
            <p className='mt-2 text-sm leading-6 text-[#c9d1d9]'>{description}</p>
          </div>
        </div>

        <div className='mt-6 flex flex-col gap-3 sm:flex-row'>
          <Link
            href={loginHref}
            className='inline-flex items-center justify-center gap-2 rounded-lg bg-[#58a6ff] px-4 py-2.5 text-sm font-semibold text-[#0d1117] transition-colors hover:bg-[#79b8ff]'
          >
            Sign in to continue
            <ArrowRight className='size-4' aria-hidden='true' />
          </Link>
          <Link
            href={loginHref}
            className='inline-flex items-center justify-center rounded-lg border border-[#30363d] px-4 py-2.5 text-sm font-medium text-[#e6edf3] transition-colors hover:bg-[#161b22]'
          >
            Open full sign-in page
          </Link>
        </div>
      </div>
    </div>
  );
}
