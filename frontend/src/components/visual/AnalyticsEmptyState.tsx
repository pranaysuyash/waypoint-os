import { BarChart3 } from 'lucide-react';
import { EmptyState } from '@/components/ui/empty-state';

export function AnalyticsEmptyState({
  title = 'Not enough trip data yet',
  body = 'Insights will appear after trips move through inquiry, quote, and booking stages.',
  showCta = true,
}: {
  title?: string;
  body?: string;
  showCta?: boolean;
}) {
  return (
    <div
      className='rounded-xl border p-8 text-center flex flex-col items-center'
      style={{
        background: 'var(--bg-surface)',
        borderColor: 'var(--border-default)',
      }}
    >
      <EmptyState
        icon={BarChart3}
        title={title}
        description={body}
        action={
          showCta
            ? { label: 'Start a new inquiry', href: '/workbench?tab=intake' }
            : undefined
        }
      />
    </div>
  );
}
