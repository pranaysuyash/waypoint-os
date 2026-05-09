'use client';

import { useCallback } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Modal } from '@/components/ui/modal';

export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: 'danger' | 'default';
  isLoading?: boolean;
}

export function ConfirmDialog({
  isOpen,
  onClose,
  onConfirm,
  title = 'Are you sure?',
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  variant = 'default',
  isLoading = false,
}: ConfirmDialogProps) {
  const handleConfirm = useCallback(() => {
    onConfirm();
    onClose();
  }, [onConfirm, onClose]);

  const isDanger = variant === 'danger';

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title} size="sm">
      <div className="flex items-start gap-3">
        {isDanger && (
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
            style={{ background: 'rgba(var(--accent-red-rgb), 0.1)' }}
          >
            <AlertTriangle
              className="h-5 w-5"
              style={{ color: 'var(--accent-red)' }}
            />
          </div>
        )}
        <p className="text-ui-sm" style={{ color: 'var(--text-secondary)' }}>
          {message}
        </p>
      </div>

      <div className="flex gap-3 mt-6">
        <button
          onClick={onClose}
          disabled={isLoading}
          className="flex-1 px-4 py-2.5 border rounded-lg font-medium transition-colors disabled:opacity-50"
          style={{
            borderColor: 'var(--border-default)',
            color: 'var(--text-primary)',
          }}
        >
          {cancelLabel}
        </button>
        <button
          onClick={handleConfirm}
          disabled={isLoading}
          className="flex-1 px-4 py-2.5 rounded-lg font-medium transition-colors disabled:opacity-50 text-white"
          style={{
            background: isDanger
              ? 'var(--accent-red)'
              : 'var(--accent-blue)',
          }}
        >
          {isLoading ? 'Please wait...' : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
