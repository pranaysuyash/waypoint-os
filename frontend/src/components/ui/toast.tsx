'use client';

import { useEffect, useCallback } from 'react';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { useToastStore, type Toast, type ToastType } from '@/lib/toast-store';

const ICONS: Record<ToastType, LucideIcon> = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const COLORS: Record<ToastType, string> = {
  success: 'var(--accent-green)',
  error: 'var(--accent-red)',
  info: 'var(--accent-blue)',
  warning: 'var(--accent-amber)',
};

function ToastItem({ toast }: { toast: Toast }) {
  const remove = useToastStore((s) => s.remove);
  const Icon = ICONS[toast.type];
  const color = COLORS[toast.type];

  useEffect(() => {
    const timer = setTimeout(() => remove(toast.id), 5000);
    return () => clearTimeout(timer);
  }, [toast.id, remove]);

  const dismiss = useCallback(() => remove(toast.id), [toast.id, remove]);

  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-lg border p-4 shadow-lg animate-fade-in pointer-events-auto max-w-sm"
      style={{
        background: 'var(--bg-surface)',
        borderColor: 'var(--border-default)',
      }}
    >
      <Icon className="h-4 w-4 mt-0.5 shrink-0" style={{ color }} />
      <p className="text-ui-sm flex-1" style={{ color: 'var(--text-primary)' }}>
        {toast.message}
      </p>
      <button
        onClick={dismiss}
        className="p-0.5 hover:bg-[var(--bg-elevated)] rounded transition-colors shrink-0"
        aria-label="Dismiss notification"
      >
        <X className="h-3.5 w-3.5" style={{ color: 'var(--text-muted)' }} />
      </button>
    </div>
  );
}

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);

  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      aria-relevant="additions"
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 pointer-events-none"
    >
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} />
      ))}
    </div>
  );
}
