/**
 * SuitabilityPanel — Display suitability assessment flags for a trip.
 *
 * Renders activity suitability concerns with color-coding by severity:
 * - CRITICAL (red): Mandatory acknowledgment required
 * - HIGH (orange): Operator warning
 * - MEDIUM/LOW (gray): Informational
 * 
 * Includes override controls for CRITICAL/HIGH flags to suppress, downgrade, or acknowledge.
 */

'use client';

import React, { useState, useCallback } from 'react';
import { AlertTriangle, AlertCircle } from 'lucide-react';
import { OverrideModal, OverrideRequest } from '../modals/OverrideModal';
import { submitOverride } from '@/lib/api-client';
import { toast } from '@/lib/toast-store';

export interface SuitabilityFlag {
  flag: string;
  flag_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  reason: string;
  confidence: number;
  details?: Record<string, any>;
  affected_travelers?: string[];
}

export interface SuitabilityPanelProps {
  flags: SuitabilityFlag[];
  tripId?: string;
  userId?: string;
  onAcknowledge?: (flagIds: string[]) => void;
}

export const SuitabilityPanel: React.FC<SuitabilityPanelProps> = ({
  flags,
  tripId,
  userId = 'agent_system',
  onAcknowledge,
}) => {
  const [acknowledgedFlags, setAcknowledgedFlags] = useState<Set<string>>(new Set());
  const [overrideModal, setOverrideModal] = useState<{
    isOpen: boolean;
    flag?: SuitabilityFlag;
  }>({ isOpen: false });
  const [pendingOverride, setPendingOverride] = useState<string | null>(null);

  if (flags.length === 0) {
    return (
      <div className="p-4 text-ui-sm text-gray-600">
        No suitability concerns detected. Trip is suitable for these travelers.
      </div>
    );
  }

  const criticalFlags = flags.filter((f) => f.severity === 'critical');
  const highFlags = flags.filter((f) => f.severity === 'high');
  const otherFlags = flags.filter((f) => f.severity !== 'critical' && f.severity !== 'high');

  const handleAcknowledge = (flagType: string) => {
    const newAcknowledged = new Set(acknowledgedFlags);
    if (newAcknowledged.has(flagType)) {
      newAcknowledged.delete(flagType);
    } else {
      newAcknowledged.add(flagType);
    }
    setAcknowledgedFlags(newAcknowledged);
  };

  const handleOpenOverrideModal = (flag: SuitabilityFlag) => {
    setOverrideModal({ isOpen: true, flag });
  };

  const handleCloseOverrideModal = () => {
    setOverrideModal({ isOpen: false, flag: undefined });
  };

  const handleSubmitOverride = useCallback(
    async (request: OverrideRequest) => {
      if (!tripId) {
        toast('Trip ID required for override', 'error');
        return;
      }

      try {
        setPendingOverride(request.flag);
        const response = await submitOverride(tripId, request);
        
        if (response.ok) {
          toast('Override recorded successfully', 'success');
          setAcknowledgedFlags((prev) => new Set(prev).add(request.flag));
        } else {
          toast('Failed to record override', 'error');
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to record override';
        toast(message, 'error');
        throw error;
      } finally {
        setPendingOverride(null);
      }
    },
    [tripId]
  );

  const handleContinue = () => {
    if (onAcknowledge && criticalFlags.length > 0) {
      const allCriticalAcknowledged = criticalFlags.every((f) =>
        acknowledgedFlags.has(f.flag_type)
      );
      if (allCriticalAcknowledged) {
        onAcknowledge(Array.from(acknowledgedFlags));
      }
    }
  };

  const allCriticalAcknowledged =
    criticalFlags.length === 0 ||
    criticalFlags.every((f) => acknowledgedFlags.has(f.flag_type));

  const getFlagKey = (flag: SuitabilityFlag) => flag.flag || flag.flag_type;

  return (
    <div className="space-y-4 p-4">
      <div className="mb-4">
        <h3 className="text-ui-lg font-semibold text-gray-900">Suitability Assessment</h3>
        <p className="text-ui-sm text-gray-600 mt-1">
          {criticalFlags.length > 0
            ? 'Operator review required before sending to customer'
            : 'Some concerns detected. Please review before proceeding.'}
        </p>
      </div>

      {/* CRITICAL FLAGS */}
      {criticalFlags.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold text-red-900 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Critical Concerns
          </h4>
          {criticalFlags.map((flag) => (
            <div
              key={getFlagKey(flag)}
              className="bg-red-50 border border-red-200 rounded-lg p-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <p className="font-medium text-red-900">{flag.reason}</p>
                  <p className="text-ui-sm text-red-700 mt-1">
                    Confidence: {(flag.confidence * 100).toFixed(0)}%
                  </p>
                  {flag.details?.activity_name && (
                    <p className="text-ui-sm text-red-700">
                      Activity: {flag.details.activity_name}
                    </p>
                  )}
                </div>
                <div className="flex flex-col gap-2">
                  {tripId && (
                    <button
                      onClick={() => handleOpenOverrideModal(flag)}
                      disabled={pendingOverride === getFlagKey(flag)}
                      className="px-3 py-1 text-ui-sm bg-red-200 hover:bg-red-300 text-red-900 rounded font-medium disabled:opacity-50 transition-colors whitespace-nowrap"
                    >
                      {pendingOverride === getFlagKey(flag) ? "Submitting..." : "Override"}
                    </button>
                  )}
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={acknowledgedFlags.has(getFlagKey(flag))}
                      onChange={() => handleAcknowledge(getFlagKey(flag))}
                      className="w-4 h-4"
                    />
                    <span className="text-ui-sm text-red-900">Acknowledge</span>
                  </label>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* HIGH FLAGS */}
      {highFlags.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold text-orange-900 flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Important Warnings
          </h4>
          {highFlags.map((flag) => (
            <div
              key={getFlagKey(flag)}
              className="bg-orange-50 border border-orange-200 rounded-lg p-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <p className="font-medium text-orange-900">{flag.reason}</p>
                  <p className="text-ui-sm text-orange-700 mt-1">
                    Confidence: {(flag.confidence * 100).toFixed(0)}%
                  </p>
                  {flag.details?.activity_name && (
                    <p className="text-ui-sm text-orange-700">
                      Activity: {flag.details.activity_name}
                    </p>
                  )}
                </div>
                {tripId && (
                  <button
                    onClick={() => handleOpenOverrideModal(flag)}
                    disabled={pendingOverride === getFlagKey(flag)}
                    className="px-3 py-1 text-ui-sm bg-orange-200 hover:bg-orange-300 text-orange-900 rounded font-medium disabled:opacity-50 transition-colors whitespace-nowrap"
                  >
                    {pendingOverride === getFlagKey(flag) ? "Submitting..." : "Override"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* OTHER FLAGS */}
      {otherFlags.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold text-gray-700">Additional Information</h4>
          {otherFlags.map((flag) => (
            <div
              key={getFlagKey(flag)}
              className="bg-gray-50 border border-gray-200 rounded-lg p-4"
            >
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{flag.reason}</p>
                  <p className="text-ui-sm text-gray-600 mt-1">
                    Confidence: {(flag.confidence * 100).toFixed(0)}%
                  </p>
                  {flag.details?.activity_name && (
                    <p className="text-ui-sm text-gray-600">
                      Activity: {flag.details.activity_name}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ACTION BUTTONS */}
      {criticalFlags.length > 0 && (
        <div className="flex gap-3 mt-6 pt-4 border-t border-gray-200">
          <button
            onClick={handleContinue}
            disabled={!allCriticalAcknowledged}
            className={`px-4 py-2 rounded-lg font-medium ${
              allCriticalAcknowledged
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-200 text-gray-500 cursor-not-allowed'
            }`}
          >
            Continue to Send
          </button>
        </div>
      )}

      {/* Override Modal */}
      {overrideModal.flag && (
        <OverrideModal
          isOpen={overrideModal.isOpen}
          flag={{
            flag: overrideModal.flag.flag || overrideModal.flag.flag_type,
            severity: overrideModal.flag.severity,
            reason: overrideModal.flag.reason,
          }}
          tripId={tripId || ''}
          userId={userId}
          onClose={handleCloseOverrideModal}
          onSubmit={handleSubmitOverride}
        />
      )}
    </div>
  );
};

export default SuitabilityPanel;
