'use client';

import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { withInertSiblings, surfaceIds, trapFocus, lockBodyScroll } from '@/lib/accessibility';

export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  closeOnOverlay?: boolean;
}

const sizeClasses = {
  sm: 'max-w-sm',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
};

export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  size = 'md',
  closeOnOverlay = true,
}: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);
  const [host, setHost] = useState<HTMLElement | null>(null);
  const ids = surfaceIds('modal');
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
      hostNode.setAttribute('data-ui-layer', 'modal');
      hostNode.setAttribute('role', 'presentation');
      document.body.appendChild(hostNode);
      setHost(hostNode);
      return;
    }

    previousActiveElement.current = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;

    const unlockBody = lockBodyScroll();
    const restoreInert = withInertSiblings(host, true);
    const cleanupFocusTrap = panelRef.current
      ? trapFocus(panelRef.current, { initialFocus: panelRef.current.querySelector<HTMLElement>(FOCUSABLE_MODAL_SELECTOR) })
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

      const shouldRestoreFocus =
        previousActiveElement.current instanceof HTMLElement &&
      previousActiveElement.current.isConnected;

      if (shouldRestoreFocus) {
        previousActiveElement.current?.focus();
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

  const handleOverlayClick = (event: React.MouseEvent) => {
    if (closeOnOverlay && event.target === event.currentTarget) {
      onClose();
    }
  };

  const modal = (
    <div
      className='fixed inset-0 z-50 flex items-center justify-center'
      role='presentation'
    >
      <div
        className='absolute inset-0 bg-black/55 transition-opacity duration-150'
        onMouseDown={handleOverlayClick}
        aria-hidden='true'
      />
      <div
        ref={panelRef}
        id={ids.panel}
        role='dialog'
        aria-modal='true'
        aria-labelledby={title ? ids.title : undefined}
        aria-describedby={description ? ids.description : undefined}
        aria-label={title ? undefined : 'Dialog'}
        className={cn(
          'relative w-full mx-4 bg-[#0d1117] border border-[#30363d] rounded-2xl shadow-2xl flex flex-col max-h-[85vh] overflow-hidden',
          sizeClasses[size]
        )}
      >
        {title && (
          <div className='flex items-center justify-between p-6 border-b border-[#30363d] shrink-0'>
            <div className='min-w-0'>
              <h2
                id={ids.title}
                className='text-ui-lg font-semibold text-[#e6edf3] truncate'
              >
                {title}
              </h2>
              {description && (
                <p id={ids.description} className='text-ui-sm text-[#8b949e] mt-1'>
                  {description}
                </p>
              )}
            </div>
            <button
              onClick={onClose}
              className='p-2 hover:bg-[#161b22] rounded-lg transition-colors ml-4 shrink-0'
              aria-label='Close modal'
            >
              <X className='size-5 text-[#8b949e]' />
            </button>
          </div>
        )}

        <div className='p-6 overflow-y-auto'>
          {children}
        </div>

        {footer && (
          <div className='p-6 pt-0 shrink-0'>
            {footer}
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modal, host);
}

const FOCUSABLE_MODAL_SELECTOR = 'button, input, select, textarea, [tabindex]:not([tabindex="-1"])';
