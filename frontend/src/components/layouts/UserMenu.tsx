'use client';

import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/auth';
import { api } from '@/lib/api-client';
import { ChevronDown, LogOut, Settings, Building2 } from 'lucide-react';
import { focusNextOutside } from '@/lib/accessibility';

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
  const { push } = useRouter();
  const user = useAuthStore((s) => s.user);
  const agency = useAuthStore((s) => s.agency);
  const membership = useAuthStore((s) => s.membership);
  const logout = useAuthStore((s) => s.logout);
  const [open, setOpen] = useState(false);
  const [activeItemIndex, setActiveItemIndex] = useState(0);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuItemRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const menuId = useId();
  const triggerId = useId();

  async function handleLogout() {
    try {
      await api.post('/api/auth/logout');
    } catch {
      // ignore
    }
    logout();
    push('/login');
  }

  const initials = getInitials(user?.name, user?.email);
  const roleLabel = membership?.role ? ROLE_LABELS[membership.role] || membership.role : '';

  const menuItems = [
    {
      id: 'settings',
      label: 'Settings',
      icon: <Settings className='size-3.5' aria-hidden='true' />,
      action: () => {
        setOpen(false);
        push('/settings');
      },
    },
    {
      id: 'sign-out',
      label: 'Sign out',
      icon: <LogOut className='size-3.5' aria-hidden='true' />,
      action: handleLogout,
      className: 'text-[var(--accent-red)] hover:bg-[var(--bg-surface-hover)]',
    },
  ];

  const moveActiveItem = (nextIndex: number) => {
    if (menuItems.length === 0) return;

    const clampedIndex = ((nextIndex % menuItems.length) + menuItems.length) % menuItems.length;
    setActiveItemIndex(clampedIndex);
    menuItemRefs.current[clampedIndex]?.focus();
  };

  const closeMenu = (restoreFocus = true) => {
    setOpen(false);
    if (restoreFocus) {
      triggerRef.current?.focus();
    }
  };

  const focusNextOutsideMenu = useCallback(() => {
    if (!menuRef.current) return;

    focusNextOutside(menuRef.current, {
      from: document.activeElement instanceof HTMLElement ? document.activeElement : null,
      fallbackFrom: triggerRef.current,
    });
  }, []);

  const openMenu = () => {
    setOpen(true);
    setActiveItemIndex(0);
  };

  const toggleMenu = () => {
    setOpen((previous) => {
      const nextOpen = !previous;
      if (nextOpen) {
        setActiveItemIndex(0);
      }
      return nextOpen;
    });
  };

  const handleTriggerKeyDown = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (!open) {
        openMenu();
      } else {
        closeMenu();
      }
      return;
    }

    if (event.key === 'Escape') {
      closeMenu();
    }
  };

  const handleMenuKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!open) return;

    switch (event.key) {
      case 'Escape':
        event.preventDefault();
        closeMenu();
        break;
      case 'Home':
        event.preventDefault();
        moveActiveItem(0);
        break;
      case 'End':
        event.preventDefault();
        moveActiveItem(menuItems.length - 1);
        break;
      case 'ArrowDown':
        event.preventDefault();
        moveActiveItem(activeItemIndex + 1);
        break;
      case 'ArrowUp':
        event.preventDefault();
        moveActiveItem(activeItemIndex - 1);
        break;
      case 'Tab':
        closeMenu(false);
        event.preventDefault();
        focusNextOutsideMenu();
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    if (open) {
      const focusTimer = window.setTimeout(() => {
        menuItemRefs.current[activeItemIndex]?.focus();
      }, 0);

      return () => window.clearTimeout(focusTimer);
    }
    return undefined;
  }, [open, activeItemIndex]);

  useEffect(() => {
    function handleDocumentClick(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    if (!open) return;

    document.addEventListener('mousedown', handleDocumentClick);
    return () => document.removeEventListener('mousedown', handleDocumentClick);
  }, [open]);

  return (
    <div className='relative' ref={menuRef}>
        <button
        ref={triggerRef}
        type='button'
        id={triggerId}
        onClick={toggleMenu}
        onKeyDown={handleTriggerKeyDown}
        className='flex items-center gap-1.5 px-1.5 py-0.5 rounded-md hover:bg-[var(--bg-surface-hover)] transition-colors'
        aria-expanded={open}
        aria-haspopup='menu'
        aria-controls={menuId}
        aria-label='User menu'
      >
        <div className='size-6 rounded-md bg-gradient-to-br from-[var(--accent-blue)] to-[var(--accent-cyan)] flex items-center justify-center text-white text-[var(--ui-text-xs)] font-semibold shrink-0'>
          {initials}
        </div>
        <ChevronDown
          className={`size-3 text-[var(--text-secondary)] transition-transform ${open ? 'rotate-180' : ''}`}
          aria-hidden='true'
        />
      </button>

      {open && (
        <div
          id={menuId}
          className='absolute right-0 top-full mt-1 w-56 bg-[var(--text-on-accent)] border border-[var(--border-default)] rounded-lg shadow-xl py-1 z-50'
          role='menu'
          onKeyDown={handleMenuKeyDown}
          aria-labelledby={triggerId}
        >
          <div className='px-3 py-2 border-b border-[var(--border-default)]'>
            <div className='text-[var(--ui-text-sm)] font-medium text-[var(--text-primary)] truncate'>
              {user?.name || user?.email || 'User'}
            </div>
            <div className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] truncate mt-0.5'>
              {user?.email}
            </div>
          </div>

          {agency && (
            <div className='px-3 py-2 border-b border-[var(--border-default)]'>
              <div className='flex items-center gap-1.5'>
                <Building2 className='size-3 text-[var(--text-secondary)]' aria-hidden='true' />
                <span className='text-[var(--ui-text-xs)] text-[var(--text-secondary)] truncate'>
                  {agency.name}
                </span>
              </div>
              {roleLabel && (
                <div className='text-[var(--ui-text-xs)] text-[var(--text-placeholder)] mt-0.5 ml-[1.125rem]'>
                  {roleLabel}
                </div>
              )}
            </div>
          )}

          <div role='group' aria-label='User menu actions'>
            {menuItems.map((item, itemIndex) => (
              <button
                key={item.id}
                type='button'
                role='menuitem'
                ref={(element) => {
                  menuItemRefs.current[itemIndex] = element;
                }}
                onClick={item.action}
                onMouseEnter={() => setActiveItemIndex(itemIndex)}
                onFocus={() => setActiveItemIndex(itemIndex)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    item.action();
                  }
                }}
                onMouseDown={(event) => event.preventDefault()}
                className={`w-full flex items-center gap-2 px-3 py-1.5 text-[var(--ui-text-sm)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface-hover)] transition-colors ${
                  activeItemIndex === itemIndex ? 'bg-[var(--bg-surface-hover)]' : ''
                } ${item.className ?? ''}`}
                tabIndex={activeItemIndex === itemIndex ? 0 : -1}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
