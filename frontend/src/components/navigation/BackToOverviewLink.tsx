'use client';

import Link from 'next/link';
import { ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

type BackToOverviewLinkProps = {
  className?: string;
  label?: string;
};

export function BackToOverviewLink({
  className,
  label = 'Back to Overview',
}: BackToOverviewLinkProps) {
  return (
    <Link
      href='/overview'
      className={cn(
        'inline-flex items-center gap-1.5 text-ui-sm font-medium text-[#58a6ff] hover:text-[#79b8ff] transition-colors',
        className,
      )}
    >
      <ChevronLeft className='h-4 w-4' aria-hidden='true' />
      <span>{label}</span>
    </Link>
  );
}

export default BackToOverviewLink;
