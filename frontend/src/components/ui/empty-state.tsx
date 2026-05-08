import { type LucideIcon } from 'lucide-react';

export interface EmptyStateAction {
  label: string;
  href?: string;
  onClick?: () => void;
}

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: EmptyStateAction;
  secondaryAction?: EmptyStateAction;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div className={`col-span-full py-16 text-center ${className || ''}`}>
      {Icon && (
        <div
          className="inline-flex items-center justify-center w-12 h-12 rounded-full mb-4"
          style={{ background: 'rgba(139, 148, 158, 0.08)' }}
        >
          <Icon className="w-6 h-6" style={{ color: 'var(--text-muted)' }} />
        </div>
      )}

      <p
        className="text-[var(--ui-text-sm)] font-medium"
        style={{ color: 'var(--text-secondary)' }}
      >
        {title}
      </p>

      {description && (
        <p
          className="text-[var(--ui-text-xs)] mt-1 max-w-[400px] mx-auto"
          style={{ color: 'var(--text-muted)' }}
        >
          {description}
        </p>
      )}

      {(action || secondaryAction) && (
        <div className="flex items-center justify-center gap-3 mt-4">
          {action &&
            (action.href ? (
              <a
                href={action.href}
                className="inline-flex items-center gap-2 px-5 py-2.5 bg-[var(--accent-blue)] text-[var(--text-on-accent)] rounded-lg text-[var(--ui-text-sm)] font-semibold hover:bg-[var(--accent-blue-hover)] transition-colors"
              >
                {action.label}
              </a>
            ) : (
              <button
                onClick={action.onClick}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[var(--ui-text-xs)] font-medium transition-colors"
                style={{
                  color: 'var(--accent-blue)',
                  background: 'rgba(var(--accent-blue-rgb), 0.1)',
                }}
              >
                {action.label}
              </button>
            ))}
          {secondaryAction &&
            (secondaryAction.href ? (
              <a
                href={secondaryAction.href}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[var(--ui-text-xs)] font-medium transition-colors"
                style={{
                  color: 'var(--text-secondary)',
                  background: 'rgba(var(--text-muted-rgb), 0.08)',
                }}
              >
                {secondaryAction.label}
              </a>
            ) : (
              <button
                onClick={secondaryAction.onClick}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[var(--ui-text-xs)] font-medium transition-colors"
                style={{
                  color: 'var(--text-secondary)',
                  background: 'rgba(var(--text-muted-rgb), 0.08)',
                }}
              >
                {secondaryAction.label}
              </button>
            ))}
        </div>
      )}
    </div>
  );
}
