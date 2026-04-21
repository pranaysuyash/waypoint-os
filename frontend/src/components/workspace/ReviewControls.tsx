"use client";

import React, { useState } from "react";
import { submitReviewAction } from "@/lib/governance-api";
import type { ReviewActionRequest } from "@/types/governance";
import type { Trip } from "@/lib/api-client";
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currentStatus = trip.review_status || "pending";
  const metadata = trip.review_metadata;

  const handleAction = async (action: ReviewActionRequest["action"]) => {
    // Validation: Notes mandatory for non-approval actions
    if ((action === "request_changes" || action === "reject") && !notes.trim()) {
      setError("Please provide notes explaining the reason for this action.");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Use existing governance API
      const response = await submitReviewAction({
        reviewId: trip.id,
        action,
        notes,
        // Backend handles default reassignment to original assignee per Wave 8 requirement
      });

      if (response.success) {
        if (onActionComplete) {
          // Construct updated trip object for optimistic/immediate UI feedback
          const updatedTrip: Trip = {
            ...trip,
            review_status: response.review.status,
            review_metadata: {
              reviewedAt: response.review.reviewedAt,
              reviewedBy: response.review.reviewedBy,
              notes: response.review.ownerNotes,
              assignee: response.review.agentId,
            }
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
          <strong>Status: {currentStatus.toUpperCase()}</strong>
          {metadata?.reviewedBy && <span> by {metadata.reviewedBy}</span>}
          {metadata?.reviewedAt && <span> on {new Date(metadata.reviewedAt).toLocaleDateString()}</span>}
        </div>
        {metadata?.notes && (
          <div className={styles.reviewNotes}>
            <em>"{metadata.notes}"</em>
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

        <div className={styles.reviewActions}>
          <button
            className={styles.approveButton}
            onClick={() => handleAction("approve")}
            disabled={isSubmitting}
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
      </div>
    </div>
  );
}
