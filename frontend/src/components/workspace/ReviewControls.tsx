"use client";

import React, { useState } from "react";
import { submitTripReviewAction } from "@/lib/api-client";
import { useWorkbenchStore } from "@/stores/workbench";
import type { ReviewActionRequest, ReviewStatus } from "@/types/governance";
import type { Trip } from "@/lib/api-client";
import type { SuitabilityFlagData } from "@/types/spine";
import { REVIEW_STATUS_LABELS } from "@/lib/label-maps";
import styles from "@/app/workbench/workbench.module.css";

interface ReviewControlsProps {
  trip: Trip;
  onActionComplete?: (updatedTrip: Trip) => void;
}

/**
 * ReviewControls Workflow (Wave 8)
 * 
 * Provides interactive review actions for travel owners.
 * Supports Approve, Request Changes (reassigns to agent), Reject, and Escalate.
 * Utilizes the existing governance-api logic to persist review decisions.
 */
export function ReviewControls({ trip, onActionComplete }: ReviewControlsProps) {
  const [notes, setNotes] = useState("");
  const [errorCategory, setErrorCategory] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { acknowledged_suitability_flags } = useWorkbenchStore();

  const suitabilityFlags: SuitabilityFlagData[] = (trip.decision as any)?.suitability_flags ?? [];
  const criticalFlags = suitabilityFlags.filter((f) => f.severity === "critical");
  const unacknowledgedCritical = criticalFlags.filter((f) => !acknowledged_suitability_flags.has(f.flag_type));
  const suitabilityBlocked =
    (trip.decision as any)?.decision_state === "suitability_review_required" &&
    unacknowledgedCritical.length > 0;

  const ERROR_CATEGORIES = [
    { id: "safety_too_strict", label: "Safety: Too Strict (False Positive)" },
    { id: "safety_too_lenient", label: "Safety: Too Lenient (Missed Leakage)" },
    { id: "logic_calculation", label: "Logic: Calculation Error" },
    { id: "logic_itinerary", label: "Logic: Poor Itinerary Quality" },
    { id: "logic_cohort", label: "Logic: Wrong Cohort Mapping" },
    { id: "formatting_broken", label: "Formatting: Broken UI/Markdown" },
    { id: "other", label: "Other (describe in notes)" },
  ];

  const currentStatus = trip.review_status || "pending";
  const metadata = trip; // The trip object itself contains review metadata

  const handleAction = async (action: ReviewActionRequest["action"]) => {
    // Validation: Notes and Error Category mandatory for non-approval actions
    if (action !== "approve") {
      if (!notes.trim()) {
        setError("Please provide notes explaining the reason for this action.");
        return;
      }
      if (!errorCategory) {
        setError("Please select an error category for systemic feedback.");
        return;
      }
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Use trip-specific review API
      const response = await submitTripReviewAction(trip.id, action, notes, errorCategory);

      if (response.success) {
        if (onActionComplete) {
          // Construct updated trip object for optimistic/immediate UI feedback
          const updatedTrip: Trip = {
            ...trip,
            review_status: response.review.status as ReviewStatus,
            // Note: Other review metadata would be updated via API refresh
          };
          onActionComplete(updatedTrip);
        }
        setNotes("");
      }
    } catch (err: any) {
      setError(err.message || "Failed to submit review action.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // If already approved/rejected, show read-only status banner
  if (currentStatus !== "pending" && currentStatus !== "revision_needed") {
    return (
      <div className={styles.reviewStatusBanner}>
        <div className={styles.reviewInfo}>
          <strong>Status: {REVIEW_STATUS_LABELS[currentStatus] || currentStatus}</strong>
          {trip?.reviewedBy && <span> by {trip.reviewedBy}</span>}
          {trip?.reviewedAt && <span> on {new Date(trip.reviewedAt).toLocaleDateString()}</span>}
        </div>
        {trip?.reviewNotes && (
          <div className={styles.reviewNotes}>
            <em>"{trip.reviewNotes}"</em>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={styles.reviewSection}>
      <h3 className={styles.sectionTitle}>Operator Review</h3>
      <div className={styles.card}>
        <div className={styles.formGroup}>
          <label className={styles.label}>Reviewer Feedback (required for changes/rejection)</label>
          <textarea
            className={styles.textarea}
            placeholder="Explain your decision or list required changes..."
            value={notes}
            onChange={(e) => {
              setNotes(e.target.value);
              if (error) setError(null);
            }}
            disabled={isSubmitting}
          />
          {error && <p className={styles.errorText}>{error}</p>}
        </div>

        <div className={styles.formGroup}>
          <label className={styles.label}>Systemic Error Category (Mandatory for Overrides)</label>
          <select 
            className={styles.select}
            value={errorCategory}
            onChange={(e) => setErrorCategory(e.target.value)}
            disabled={isSubmitting}
          >
            <option value="">-- Select Error Category --</option>
            {ERROR_CATEGORIES.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.label}</option>
            ))}
          </select>
          <p className={styles.helpText} style={{ fontSize: '11px', marginTop: '4px', opacity: 0.7 }}>
            This feedback helps improve future trip recommendations.
          </p>
        </div>

        {suitabilityBlocked && (
          <div className={styles.errorText} style={{ marginBottom: "12px", padding: "8px 12px", borderRadius: "6px", background: "var(--color-danger-bg, #fef2f2)", border: "1px solid var(--color-danger-border, #fca5a5)", fontSize: "13px" }}>
            <strong>Approval blocked:</strong> {unacknowledgedCritical.length} critical suitability flag{unacknowledgedCritical.length !== 1 ? "s" : ""} must be acknowledged in the Decision tab before approving.
          </div>
        )}

        <div className={styles.reviewActions}>
          <button
            className={styles.approveButton}
            onClick={() => handleAction("approve")}
            disabled={isSubmitting || suitabilityBlocked}
            title={suitabilityBlocked ? "Acknowledge all critical suitability flags before approving" : undefined}
            data-testid="approve-button"
          >
            {isSubmitting ? "Processing..." : "Approve & Ready"}
          </button>
          
          <button
            className={styles.revisionButton}
            onClick={() => handleAction("request_changes")}
            disabled={isSubmitting}
          >
            Request Changes
          </button>

          <div className={styles.actionDivider} />

          <button
            className={styles.rejectButton}
            onClick={() => handleAction("reject")}
            disabled={isSubmitting}
          >
            Reject
          </button>
          
          <button
            className={styles.buttonSecondary}
            style={{ fontSize: '12px', padding: '6px 12px' }}
            onClick={() => handleAction("escalate")}
            disabled={isSubmitting}
          >
            Escalate
          </button>
        </div>
        <p className={styles.helpText} style={{ fontSize: '11px', marginTop: '6px', opacity: 0.8 }}>
          Approval completes the review step. Sending to the customer still follows your send policy.
        </p>
      </div>
    </div>
  );
}
