'use client';

import { use, useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function ShortLinkRedirectPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = use(params);
  const router = useRouter();

  useEffect(() => {
    if (token) {
      router.replace(`/proposals/${token}`);
    }
  }, [token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0d1117] text-[#e6edf3]">
      <p className="text-sm text-[#8b949e]">Redirecting to proposal…</p>
    </div>
  );
}
