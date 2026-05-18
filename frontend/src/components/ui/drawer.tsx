'use client';

import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { lockBodyScroll, surfaceIds, trapFocus, withInertSiblings } from '@/lib/accessibility';

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  position?: 'left' | 'right';
  width?: string;
  showCloseButton?: boolean;
  closeOnOverlay?: boolean;
}

export function Drawer({
  isOpen,
  onClose,
  title,
  description,
  children,
  position = 'right',
  width = 'w-full max-w-2xl',
  showCloseButton = true,
  closeOnOverlay = true,
}: DrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<Element | null>(null);
  const [host, setHost] = useState<HTMLElement | null>(null);
  const ids = surfaceIds('drawer');
  const onCloseEvent = useEffectEvent(() => onClose());

  useEffect(() => {
    if (!isOpen) {
      if (host) {
        host.remove();
        setHost(null);
      }
      return;
    }

    if (!host) {
      const hostNode = document.createElement('div');
      hostNode.setAttribute('data-ui-layer', 'drawer');
      hostNode.setAttribute('role', 'presentation');
      document.body.appendChild(hostNode);
      setHost(hostNode);
      return;
    }

    previousActiveElement.current = document.activeElement;

    const unlockBody = lockBodyScroll();
    const restoreInert = withInertSiblings(host, true);
    const cleanupFocusTrap = drawerRef.current
      ? trapFocus(drawerRef.current)
      : () => {};

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        onCloseEvent();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      cleanupFocusTrap();
      restoreInert();
      unlockBody();

      if (previousActiveElement.current instanceof HTMLElement) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen, host, onCloseEvent]);

  useEffect(() => () => {
    if (host && host.isConnected) {
      host.remove();
    }
  }, [host]);

  if (!isOpen || !host) {
    return null;
  }

  const positionClasses = position === 'right' ? 'right-0 border-l' : 'left-0 border-r';
  const animName = position === 'right' ? 'drawer-slide-in-right' : 'drawer-slide-in-left';

  const handleOverlayClick = (event: React.MouseEvent) => {
    if (closeOnOverlay && event.target === event.currentTarget) {
      onClose();
    }
  };

  const drawer = (
    <div className='fixed inset-0 z-50' role='presentation'>
      <div
        className='absolute inset-0 bg-black/50'
        onMouseDown={handleOverlayClick}
        aria-hidden='true'
      />
      <div
        ref={drawerRef}
        role='dialog'
        id={ids.panel}
        aria-modal='true'
        aria-labelledby={title ? ids.title : undefined}
        aria-describedby={description ? ids.description : undefined}
        aria-label={title ? undefined : 'Drawer'}
        className={cn(
          'absolute top-0 h-full bg-[#0d1117] border-[#30363d] shadow-lg flex flex-col',
          positionClasses,
          width
        )}
        style={{ animation: `${animName} 0.2s ease-out` }}
      >
        {(title || showCloseButton) && (
          <div className='flex items-center justify-between p-6 border-b border-[#30363d] shrink-0'>
            <div className='min-w-0'>
              {title && (
                <h2
                  id={ids.title}
                  className='text-ui-lg font-semibold text-[#e6edf3] truncate'
                >
                  {title}
                </h2>
              )}
              {description && (
                <p
                  id={ids.description}
                  className='text-ui-sm text-[#8b949e] mt-1'
                >
                  {description}
                </p>
              )}
            </div>
            {showCloseButton && (
              <button
                onClick={onClose}
                className='p-2 hover:bg-[#161b22] rounded-lg transition-colors ml-4 shrink-0'
                aria-label='Close drawer'
              >
                <X className='size-5 text-[#8b949e]' />
              </button>
            )}
          </div>
        )}

        <div className='flex-1 overflow-y-auto'>{children}</div>
      </div>
    </div>
  );

  return createPortal(drawer, host);
}
