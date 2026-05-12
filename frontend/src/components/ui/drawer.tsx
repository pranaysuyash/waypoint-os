'use client';

import { useEffect, useRef, useEffectEvent } from 'react';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';

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

  const onCloseEvent = useEffectEvent(() => onClose());

  useEffect(() => {
    if (!isOpen) return;

    previousActiveElement.current = document.activeElement;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
        onCloseEvent();
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (previousActiveElement.current instanceof HTMLElement) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen]);

  if (!isOpen) return null;

  const positionClasses = position === 'right' ? 'right-0 border-l' : 'left-0 border-r';
  const animName = position === 'right' ? 'drawer-slide-in-right' : 'drawer-slide-in-left';

  return (
    <div className="fixed inset-0 z-50" role="presentation">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={closeOnOverlay ? onClose : undefined}
        aria-hidden="true"
      />
      <div
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label={title || 'Drawer'}
        className={cn(
          'absolute top-0 h-full bg-[#0d1117] border-[#30363d] shadow-lg flex flex-col',
          positionClasses,
          width
        )}
        style={{ animation: `${animName} 0.2s ease-out` }}
      >
        {(title || showCloseButton) && (
          <div className="flex items-center justify-between p-6 border-b border-[#30363d] shrink-0">
            <div className="min-w-0">
              {title && (
                <h2 className="text-ui-lg font-semibold text-[#e6edf3] truncate">
                  {title}
                </h2>
              )}
              {description && (
                <p className="text-ui-sm text-[#8b949e] mt-1">{description}</p>
              )}
            </div>
            {showCloseButton && (
              <button
                onClick={onClose}
                className="p-2 hover:bg-[#161b22] rounded-lg transition-colors ml-4 shrink-0"
                aria-label="Close"
              >
                <X className="size-5 text-[#8b949e]" />
              </button>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
