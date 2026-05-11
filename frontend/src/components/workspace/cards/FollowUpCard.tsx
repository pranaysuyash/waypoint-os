'use client';

import { memo, useState, useTransition } from 'react';
import { Calendar, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Modal } from '@/components/ui/modal';


// ============================================================================
// FOLLOW-UP STATUS STYLES
// ============================================================================

const STATUS_STYLES = {
  pending: { color: 'var(--accent-amber)', bg: 'rgba(var(--accent-amber-rgb), 0.1)', label: 'Pending' },
  completed: { color: 'var(--accent-green)', bg: 'rgba(var(--accent-green-rgb), 0.1)', label: 'Completed' },
  snoozed: { color: 'var(--accent-blue)', bg: 'rgba(var(--accent-blue-rgb), 0.1)', label: 'Snoozed' },
} as const;

const URGENCY_STYLES = (daysUntilDue: number) => {
  if (daysUntilDue < 0) {
    return { color: 'var(--accent-red)', bg: 'rgba(var(--accent-red-rgb), 0.1)', label: 'OVERDUE' };
  } else if (daysUntilDue === 0) {
    return { color: 'var(--accent-orange)', bg: 'rgba(var(--accent-amber-rgb), 0.1)', label: 'TODAY' };
  } else if (daysUntilDue <= 3) {
    return { color: 'var(--accent-amber)', bg: 'rgba(var(--accent-amber-rgb), 0.1)', label: 'SOON' };
  }
  return { color: 'var(--text-secondary)', bg: 'rgba(var(--color-neutral-rgb), 0.1)', label: 'UPCOMING' };
};

// ============================================================================
// MODALS
// ============================================================================

const SnoozeModal = memo(function SnoozeModal({
  isOpen,
  onClose,
  onSnooze,
  isLoading,
}: {
  isOpen: boolean;
  onClose: () => void;
  onSnooze: (days: number) => void;
  isLoading: boolean;
}) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Snooze Follow-up" size="sm">
      <div className="space-y-2">
        {[1, 3, 7].map((days) => (
          <button
            key={days}
            onClick={() => onSnooze(days)}
            disabled={isLoading}
            className="w-full px-4 py-2 rounded border transition-colors disabled:opacity-50"
            style={{
              color: 'var(--text-primary)',
              borderColor: 'var(--border-default)',
            }}
          >
            {days} day{days > 1 ? 's' : ''}
          </button>
        ))}
      </div>
    </Modal>
  );
});

const RescheduleModal = memo(function RescheduleModal({
  isOpen,
  onClose,
  onReschedule,
  isLoading,
}: {
  isOpen: boolean;
  onClose: () => void;
  onReschedule: (date: string) => void;
  isLoading: boolean;
}) {
  const [date, setDate] = useState('');

  const handleSubmit = () => {
    if (date) {
      onReschedule(new Date(date).toISOString());
      setDate('');
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Reschedule Follow-up"
      size="sm"
      footer={
        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={isLoading || !date}
            className="flex-1 px-4 py-2 rounded transition-colors disabled:opacity-50"
            style={{
              background: 'var(--accent-blue)',
              color: '#fff',
            }}
          >
            Reschedule
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 rounded border transition-colors"
            style={{
              color: 'var(--text-secondary)',
              borderColor: 'var(--border-default)',
            }}
          >
            Cancel
          </button>
        </div>
      }
    >
      <input
        type="datetime-local"
        value={date}
        onChange={(e) => setDate(e.target.value)}
        className="w-full px-4 py-2 rounded border bg-surface"
        style={{
          color: 'var(--text-primary)',
          borderColor: 'var(--border-default)',
        }}
      />
    </Modal>
  );
});

// ============================================================================
// MAIN CARD
// ============================================================================

export interface FollowUpCardProps {
  tripId: string;
  travelerName: string;
  agentName: string;
  dueDate: string;
  status: 'pending' | 'completed' | 'snoozed';
  daysUntilDue: number;
  onComplete?: (tripId: string) => void;
  onSnooze?: (tripId: string, days: number) => void;
  onReschedule?: (tripId: string, date: string) => void;
}

export const FollowUpCard = memo(function FollowUpCard({
  tripId,
  travelerName,
  agentName,
  dueDate,
  status,
  daysUntilDue,
  onComplete,
  onSnooze,
  onReschedule,
}: FollowUpCardProps) {
  const [isSnoozing, setIsSnoozing] = useState(false);
  const [isRescheduling, setIsRescheduling] = useState(false);
  const [isPending, startTransition] = useTransition();

  const statusStyle = STATUS_STYLES[status];
  const urgencyStyle = URGENCY_STYLES(daysUntilDue);
  
  const dueDateObj = new Date(dueDate);
  const formattedDate = dueDateObj.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const handleComplete = () => {
    if (onComplete) {
      startTransition(async () => {
        await onComplete(tripId);
      });
    }
  };

  const handleSnooze = async (days: number) => {
    if (onSnooze) {
      startTransition(async () => {
        await onSnooze(tripId, days);
        setIsSnoozing(false);
      });
    }
  };

  const handleReschedule = async (date: string) => {
    if (onReschedule) {
      startTransition(async () => {
        await onReschedule(tripId, date);
        setIsRescheduling(false);
      });
    }
  };

  const handleCloseSnooze = () => setIsSnoozing(false);
  const handleCloseReschedule = () => setIsRescheduling(false);

  return (
    <>
      <Card
        variant="bordered"
        className="p-4 flex flex-col"
        style={{
          borderColor:
            daysUntilDue < 0
              ? 'rgba(248,81,73,0.4)'
              : daysUntilDue === 0
              ? 'rgba(229,171,1,0.4)'
              : 'var(--border-default)',
        }}
      >
        {/* Header: Trip ID + Status Badge */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <span
              className="text-ui-xs font-mono uppercase tracking-wide"
              style={{ color: 'var(--text-muted)' }}
            >
              {tripId}
            </span>
            <p
              className="text-ui-sm font-semibold mt-0.5 truncate"
              style={{ color: 'var(--text-primary)' }}
            >
              {travelerName}
            </p>
          </div>
          <span
            className="inline-flex items-center gap-1 text-ui-xs font-medium px-2 py-1 rounded"
            style={{ color: statusStyle.color, background: statusStyle.bg }}
          >
            {statusStyle.label}
          </span>
        </div>

        {/* Agent Name */}
        <p
          className="text-ui-xs mb-3"
          style={{ color: 'var(--text-secondary)' }}
        >
          Agent: <span style={{ color: 'var(--text-primary)' }}>{agentName}</span>
        </p>

        {/* Due Date + Urgency */}
        <div className="flex items-center gap-3 mb-4 pb-4 border-b" style={{ borderColor: 'var(--border-default)' }}>
          <div className="flex items-center gap-1">
            <Calendar className="size-3" style={{ color: 'var(--text-muted)' }} />
            <span className="text-ui-xs" style={{ color: 'var(--text-secondary)' }}>
              {formattedDate}
            </span>
          </div>
          <div className="ml-auto">
            <span
              className="inline-flex items-center gap-1 text-ui-xs font-bold px-2 py-1 rounded"
              style={{ color: urgencyStyle.color, background: urgencyStyle.bg }}
            >
              {daysUntilDue < 0 ? `${Math.abs(daysUntilDue)}d OVERDUE` : `${daysUntilDue}d`}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          {status === 'pending' && (
            <>
              <button
                onClick={handleComplete}
                disabled={isPending}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 rounded text-ui-xs font-medium transition-colors disabled:opacity-50"
                style={{
                  background: 'var(--accent-green)',
                  color: '#fff',
                }}
              >
                <CheckCircle className="size-3" />
                Complete
              </button>
              <button
                onClick={() => setIsSnoozing(true)}
                disabled={isPending}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 rounded text-ui-xs font-medium transition-colors border disabled:opacity-50"
                style={{
                  color: 'var(--text-secondary)',
                  borderColor: 'var(--border-default)',
                }}
              >
                <Clock className="size-3" />
                Snooze
              </button>
              <button
                onClick={() => setIsRescheduling(true)}
                disabled={isPending}
                className="flex-1 px-3 py-2 rounded text-ui-xs font-medium transition-colors border disabled:opacity-50"
                style={{
                  color: 'var(--text-secondary)',
                  borderColor: 'var(--border-default)',
                }}
              >
                Reschedule
              </button>
            </>
          )}
          {status === 'completed' && (
            <div className="w-full flex items-center justify-center gap-2">
              <CheckCircle className="size-4" style={{ color: 'var(--accent-green)' }} />
              <span className="text-ui-xs" style={{ color: 'var(--text-secondary)' }}>
                Follow-up completed
              </span>
            </div>
          )}
        </div>
      </Card>

      <SnoozeModal
        isOpen={isSnoozing}
        onClose={handleCloseSnooze}
        onSnooze={handleSnooze}
        isLoading={isPending}
      />

      <RescheduleModal
        isOpen={isRescheduling}
        onClose={handleCloseReschedule}
        onReschedule={handleReschedule}
        isLoading={isPending}
      />
    </>
  );
});

