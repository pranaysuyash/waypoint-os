'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api } from '@/lib/api-client';
import { ChevronDown, LogOut, Settings, Building2 } from 'lucide-react';

function getInitials(name?: string | null, email?: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  }
  return email ? email.slice(0, 2).toUpperCase() : 'U';
}

const ROLE_LABELS: Record<string, string> = {
  owner: 'Owner',
  admin: 'Admin',
  senior_agent: 'Senior Agent',
  junior_agent: 'Junior Agent',
  viewer: 'Viewer',
};

export function UserMenu() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const agency = useAuthStore((s) => s.agency);
  const membership = useAuthStore((s) => s.membership);
  const logout = useAuthStore((s) => s.logout);
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  async function handleLogout() {
    try {
      await api.post('/api/auth/logout');
    } catch {
      // ignore
    }
    logout();
    router.push('/login');
  }

  const initials = getInitials(user?.name, user?.email);
  const roleLabel = membership?.role ? ROLE_LABELS[membership.role] || membership.role : '';

  return (
    <div className='relative' ref={menuRef}>
      <button
        onClick={() => setOpen(!open)}
        className='flex items-center gap-1.5 px-1.5 py-0.5 rounded-md hover:bg-[#161b22] transition-colors'
        aria-expanded={open}
        aria-haspopup='true'
        aria-label='User menu'
      >
        <div className='h-6 w-6 rounded-md bg-gradient-to-br from-[#2563eb] to-[#39d0d8] flex items-center justify-center text-white text-xs font-semibold shrink-0'>
          {initials}
        </div>
        <ChevronDown
          className={`h-3 w-3 text-[#8b949e] transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden='true'
        />
      </button>

      {open && (
        <div
          className='absolute right-0 top-full mt-1 w-56 bg-[#0d1117] border border-[#1c2128] rounded-lg shadow-xl py-1 z-50'
          role='menu'
        >
          <div className='px-3 py-2 border-b border-[#1c2128]'>
            <div className='text-sm font-medium text-[#e6edf3] truncate'>
              {user?.name || user?.email || 'User'}
            </div>
            <div className='text-xs text-[#8b949e] truncate mt-0.5'>
              {user?.email}
            </div>
          </div>

          {agency && (
            <div className='px-3 py-2 border-b border-[#1c2128]'>
              <div className='flex items-center gap-1.5'>
                <Building2 className='h-3 w-3 text-[#8b949e]' aria-hidden='true' />
                <span className='text-xs text-[#8b949e] truncate'>
                  {agency.name}
                </span>
              </div>
              {roleLabel && (
                <div className='text-xs text-[#484f58] mt-0.5 ml-[1.125rem]'>
                  {roleLabel}
                </div>
              )}
            </div>
          )}

          <button
            onClick={() => {
              setOpen(false);
              router.push('/settings');
            }}
            className='w-full flex items-center gap-2 px-3 py-1.5 text-sm text-[#8b949e] hover:text-[#e6edf3] hover:bg-[#161b22] transition-colors'
            role='menuitem'
          >
            <Settings className='h-3.5 w-3.5' aria-hidden='true' />
            Settings
          </button>

          <button
            onClick={handleLogout}
            className='w-full flex items-center gap-2 px-3 py-1.5 text-sm text-[#f85149] hover:bg-[#161b22] transition-colors'
            role='menuitem'
          >
            <LogOut className='h-3.5 w-3.5' aria-hidden='true' />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
