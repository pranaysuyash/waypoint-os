'use client';

import { memo, useCallback } from 'react';
import { cn } from '@/lib/utils';
import type { ViewProfile } from '@/lib/inbox-helpers';
import { VIEW_PROFILES, VIEW_PROFILE_LABELS, saveViewProfile } from '@/lib/inbox-helpers';

export interface ViewProfileToggleProps {
  current: ViewProfile;
  onChange: (profile: ViewProfile) => void;
  className?: string;
}

export const ViewProfileToggle = memo(function ViewProfileToggle({
  current,
  onChange,
  className,
}: ViewProfileToggleProps) {
  const handleClick = useCallback(
    (profile: ViewProfile) => {
      saveViewProfile(profile);
      onChange(profile);
    },
    [onChange],
  );

  return (
    <div
      className={cn('flex items-center rounded-lg border border-[#30363d] overflow-hidden', className)}
      role="radiogroup"
      aria-label="Card view profile"
    >
      {VIEW_PROFILES.map((profile) => {
        const active = current === profile;
        return (
          <button
            key={profile}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => handleClick(profile)}
            className={cn(
              'px-2.5 py-1.5 text-[11px] font-medium transition-colors',
              active
                ? 'bg-[#1c2128] text-[#e6edf3]'
                : 'text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22]',
            )}
          >
            {VIEW_PROFILE_LABELS[profile]}
          </button>
        );
      })}
    </div>
  );
});

export default ViewProfileToggle;
