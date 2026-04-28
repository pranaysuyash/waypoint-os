'use client';

import { memo, useState } from 'react';
import { Calendar, Clock, CheckCircle, XCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { COLORS, STATE_COLORS } from '@/lib/tokens';

// ============================================================================
// FOLLOW-UP STATUS STYLES
// ============================================================================

const STATUS_STYLES = {
  pending: { color: COLORS.accentAmber, bg: STATE_COLORS.amber.bg, label: 'Pending' },
  completed: { color: COLORS.accentGreen, bg: STATE_COLORS.green.bg, label: 'Completed' },
  snoozed: { color: COLORS.accentBlue, bg: STATE_COLORS.blue.bg, label: 'Snoozed' },
} as const;

const URGENCY_STYLES = (daysUntilDue: number) => {
  if (daysUntilDue < 0) {
    return { color: COLORS.accentRed, bg: STATE_COLORS.red.bg, label: 'OVERDUE' };
  } else if (daysUntilDue === 0) {
    return { color: COLORS.accentOrange, bg: STATE_COLORS.amber.bg, label: 'TODAY' };
  } else if (daysUntilDue <= 3) {
    return { color: COLORS.accentAmber, bg: STATE_COLORS.amber.bg, label: 'SOON' };
  }
  return { color: COLORS.textSecondary, bg: STATE_COLORS.neutral.bg, label: 'UPCOMING' };
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
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-sm w-full mx-4">
        <h3 className="text-lg font-semibold mb-4" style={{ color: COLORS.textPrimary }}>
          Snooze Follow-up
        </h3>
        <div className="space-y-2 mb-6">
          {[1, 3, 7].map((days) => (
            <button
              key={days}
              onClick={() => onSnooze(days)}
              disabled={isLoading}
              className="w-full px-4 py-2 rounded border transition-colors disabled:opacity-50"
              style={{
                color: COLORS.textPrimary,
                borderColor: COLORS.borderDefault,
              }}
            >
              {days} day{days > 1 ? 's' : ''}
            </button>
          ))}
        </div>
        <button
          onClick={onClose}
          className="w-full px-4 py-2 rounded border transition-colors"
          style={{
            color: COLORS.textSecondary,
            borderColor: COLORS.borderDefault,
          }}
        >
          Cancel
        </button>
      </div>
    </div>
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

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 rounded-lg p-6 max-w-sm w-full mx-4">
        <h3 className="text-lg font-semibold mb-4" style={{ color: COLORS.textPrimary }}>
          Reschedule Follow-up
        </h3>
        <input
          type="datetime-local"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="w-full px-4 py-2 rounded border mb-6 bg-gray-800"
          style={{
            color: COLORS.textPrimary,
            borderColor: COLORS.borderDefault,
          }}
        />
        <div className="flex gap-2">
          <button
            onClick={handleSubmit}
            disabled={isLoading || !date}
            className="flex-1 px-4 py-2 rounded transition-colors disabled:opacity-50"
            style={{
              background: COLORS.accentBlue,
              color: '#fff',
            }}
          >
            Reschedule
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 rounded border transition-colors"
            style={{
              color: COLORS.textSecondary,
              borderColor: COLORS.borderDefault,
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
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
  const [isLoading, setIsLoading] = useState(false);

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

  const handleComplete = async () => {
    if (onComplete) {
      setIsLoading(true);
      try {
        await onComplete(tripId);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleSnooze = async (days: number) => {
    if (onSnooze) {
      setIsLoading(true);
      try {
        await onSnooze(tripId, days);
        setIsSnoozing(false);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleReschedule = async (date: string) => {
    if (onReschedule) {
      setIsLoading(true);
      try {
        await onReschedule(tripId, date);
        setIsRescheduling(false);
      } finally {
        setIsLoading(false);
      }
    }
  };

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
              : COLORS.borderDefault,
        }}
      >
        {/* Header: Trip ID + Status Badge */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <span
              className="text-xs font-mono uppercase tracking-wide"
              style={{ color: COLORS.textMuted }}
            >
              {tripId}
            </span>
            <p
              className="text-sm font-semibold mt-0.5 truncate"
              style={{ color: COLORS.textPrimary }}
            >
              {travelerName}
            </p>
          </div>
          <span
            className="inline-flex items-center gap-1 text-xs font-medium px-2 py-1 rounded"
            style={{ color: statusStyle.color, background: statusStyle.bg }}
          >
            {statusStyle.label}
          </span>
        </div>

        {/* Agent Name */}
        <p
          className="text-xs mb-3"
          style={{ color: COLORS.textSecondary }}
        >
          Agent: <span style={{ color: COLORS.textPrimary }}>{agentName}</span>
        </p>

        {/* Due Date + Urgency */}
        <div className="flex items-center gap-3 mb-4 pb-4 border-b" style={{ borderColor: COLORS.borderDefault }}>
          <div className="flex items-center gap-1">
            <Calendar className="w-3 h-3" style={{ color: COLORS.textMuted }} />
            <span className="text-xs" style={{ color: COLORS.textSecondary }}>
              {formattedDate}
            </span>
          </div>
          <div className="ml-auto">
            <span
              className="inline-flex items-center gap-1 text-xs font-bold px-2 py-1 rounded"
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
                disabled={isLoading}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 rounded text-xs font-medium transition-colors disabled:opacity-50"
                style={{
                  background: COLORS.accentGreen,
                  color: '#fff',
                }}
              >
                <CheckCircle className="w-3 h-3" />
                Complete
              </button>
              <button
                onClick={() => setIsSnoozing(true)}
                disabled={isLoading}
                className="flex-1 flex items-center justify-center gap-1 px-3 py-2 rounded text-xs font-medium transition-colors border disabled:opacity-50"
                style={{
                  color: COLORS.textSecondary,
                  borderColor: COLORS.borderDefault,
                }}
              >
                <Clock className="w-3 h-3" />
                Snooze
              </button>
              <button
                onClick={() => setIsRescheduling(true)}
                disabled={isLoading}
                className="flex-1 px-3 py-2 rounded text-xs font-medium transition-colors border disabled:opacity-50"
                style={{
                  color: COLORS.textSecondary,
                  borderColor: COLORS.borderDefault,
                }}
              >
                Reschedule
              </button>
            </>
          )}
          {status === 'completed' && (
            <div className="w-full flex items-center justify-center gap-2">
              <CheckCircle className="w-4 h-4" style={{ color: COLORS.accentGreen }} />
              <span className="text-xs" style={{ color: COLORS.textSecondary }}>
                Follow-up completed
              </span>
            </div>
          )}
        </div>
      </Card>

      <SnoozeModal
        isOpen={isSnoozing}
        onClose={() => setIsSnoozing(false)}
        onSnooze={handleSnooze}
        isLoading={isLoading}
      />

      <RescheduleModal
        isOpen={isRescheduling}
        onClose={() => setIsRescheduling(false)}
        onReschedule={handleReschedule}
        isLoading={isLoading}
      />
    </>
  );
});

export default FollowUpCard;
