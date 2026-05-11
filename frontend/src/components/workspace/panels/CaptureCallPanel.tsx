"use client";

import React, { useState, useEffect } from "react";
import { AlertCircle, Loader2 } from "lucide-react";
import { Trip, createTrip } from "@/lib/api-client";

export interface CaptureCallPanelProps {
  onSave: (trip: Trip) => void;
  onCancel: () => void;
  defaultFollowUpHours?: number;
}

export default function CaptureCallPanel({
  onSave,
  onCancel,
  defaultFollowUpHours = 48,
}: CaptureCallPanelProps) {
  const [rawNote, setRawNote] = useState("");
  const [ownerNote, setOwnerNote] = useState("");
  const [followUpDueDate, setFollowUpDueDate] = useState("");
  const [partyComposition, setPartyComposition] = useState("");
  const [pacePreference, setPacePreference] = useState("");
  const [dateYearConfidence, setDateYearConfidence] = useState("");
  const [leadSource, setLeadSource] = useState("");
  const [activityProvenance, setActivityProvenance] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    // Compute default follow-up date (now + defaultFollowUpHours)
    // Format as YYYY-MM-DDTHH:mm for datetime-local input (local time, not UTC)
    const now = new Date();
    now.setHours(now.getHours() + defaultFollowUpHours);
    
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");
    const hours = String(now.getHours()).padStart(2, "0");
    const minutes = String(now.getMinutes()).padStart(2, "0");
    
    const localIso = `${year}-${month}-${day}T${hours}:${minutes}`;
    setFollowUpDueDate(localIso);
  }, [defaultFollowUpHours]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!rawNote.trim()) {
      newErrors.rawNote = "What did the customer tell you? This is required.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validate()) {
      return;
    }

    setIsLoading(true);

    try {
      const trip = await createTrip({
        raw_note: rawNote.trim(),
        owner_note: ownerNote.trim() || undefined,
        follow_up_due_date: followUpDueDate || undefined,
        party_composition: partyComposition.trim() || undefined,
        pace_preference: pacePreference || undefined,
        date_year_confidence: dateYearConfidence || undefined,
        lead_source: leadSource || undefined,
        activity_provenance: activityProvenance.trim() || undefined,
      });

      setRawNote("");
      setOwnerNote("");
      setFollowUpDueDate("");
      setPartyComposition("");
      setPacePreference("");
      setDateYearConfidence("");
      setLeadSource("");
      setActivityProvenance("");
      setErrors({});
      onSave(trip);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to save call";
      setApiError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setRawNote("");
    setOwnerNote("");
    setFollowUpDueDate("");
    setPartyComposition("");
    setPacePreference("");
    setDateYearConfidence("");
    setLeadSource("");
    setActivityProvenance("");
    setErrors({});
    setApiError(null);
    onCancel();
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-canvas border-l border-border-default dark:border-border-default">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border-default dark:border-border-default">
        <h2 className="text-ui-lg font-semibold text-text-primary dark:text-text-primary">
          Capture Call
        </h2>
        <p className="text-ui-sm text-text-secondary dark:text-text-muted mt-1">
          Record the customer's travel intent and next steps
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {/* API Error Alert */}
        {apiError && (
          <div className="p-3 bg-[rgba(var(--accent-red-rgb)/0.08)] dark:bg-[rgba(var(--accent-red-rgb)/0.18)] border border-[rgba(var(--accent-red-rgb)/0.25)] dark:border-[rgba(var(--accent-red-rgb)/0.40)] rounded-lg flex items-start gap-3">
            <AlertCircle className="size-5 text-accent-red dark:text-accent-red flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-ui-sm font-medium text-accent-red dark:text-accent-red">
                Error saving call
              </p>
              <p className="text-ui-xs text-accent-red dark:text-accent-red mt-0.5">{apiError}</p>
            </div>
          </div>
        )}

        {/* Raw Note Field */}
        <div>
          <label
            htmlFor="rawNote"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            What did the customer tell you?
          </label>
          <textarea
            id="rawNote"
            value={rawNote}
            onChange={(e) => {
              setRawNote(e.target.value);
              if (errors.rawNote) {
                setErrors((prev) => ({ ...prev, rawNote: "" }));
              }
            }}
            placeholder="e.g., Family of 4 wants to explore Japan, late November…"
            rows={4}
            className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors ${
              errors.rawNote
                ? "border-[rgba(var(--accent-red-rgb)/0.3)] dark:border-[rgba(var(--accent-red-rgb)/0.35)]"
                : "border-border-default dark:border-border-default"
            }`}
          />
          {errors.rawNote && (
            <p className="text-ui-xs text-accent-red dark:text-accent-red mt-1">{errors.rawNote}</p>
          )}
        </div>

        {/* Owner Note Field */}
        <div>
          <label
            htmlFor="ownerNote"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            Any notes for yourself?
          </label>
          <textarea
            id="ownerNote"
            value={ownerNote}
            onChange={(e) => setOwnerNote(e.target.value)}
            placeholder="e.g., Mentioned budget concerns, needs early morning flights…"
            rows={3}
            className="w-full px-3 py-2 border border-border-default dark:border-border-default rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors"
          />
        </div>

        {/* Follow-up Due Date Field */}
        <div>
          <label
            htmlFor="followUpDueDate"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            Promise to follow up by:
          </label>
          <input
            id="followUpDueDate"
            type="datetime-local"
            value={followUpDueDate}
            onChange={(e) => setFollowUpDueDate(e.target.value)}
            className="w-full px-3 py-2 border border-border-default dark:border-border-default rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors"
          />
          <p className="text-ui-xs text-text-muted dark:text-text-muted mt-1">
            Leave blank if no promise was made
          </p>
        </div>

        {/* Party Composition Field */}
        <div>
          <label
            htmlFor="partyComposition"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            Who's traveling?
          </label>
          <textarea
            id="partyComposition"
            value={partyComposition}
            onChange={(e) => setPartyComposition(e.target.value)}
            placeholder="e.g., 2 adults, 1 toddler (age 3), 1 infant"
            rows={2}
            className="w-full px-3 py-2 border border-border-default dark:border-border-default rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors"
          />
          <p className="text-ui-xs text-text-muted dark:text-text-muted mt-1">
            Helps us plan family-friendly itineraries
          </p>
        </div>

        {/* Pace Preference Field */}
        <div>
          <label
            htmlFor="pacePreference"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            Travel pace preference?
          </label>
          <select
            id="pacePreference"
            value={pacePreference}
            onChange={(e) => setPacePreference(e.target.value)}
            className="w-full px-3 py-2 border border-border-default dark:border-border-default rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors"
          >
            <option value="">Select pace preference…</option>
            <option value="rushed">Rushed</option>
            <option value="normal">Normal</option>
            <option value="relaxed">Relaxed</option>
          </select>
          <p className="text-ui-xs text-text-muted dark:text-text-muted mt-1">
            How much do they want to move around?
          </p>
        </div>

        {/* Date Confidence Field */}
        <div>
          <label
            htmlFor="dateYearConfidence"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            How certain about the dates?
          </label>
          <select
            id="dateYearConfidence"
            value={dateYearConfidence}
            onChange={(e) => setDateYearConfidence(e.target.value)}
            className="w-full px-3 py-2 border border-border-default dark:border-border-default rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors"
          >
            <option value="">Select confidence level…</option>
            <option value="certain">Certain</option>
            <option value="likely">Likely</option>
            <option value="unsure">Unsure</option>
          </select>
          <p className="text-ui-xs text-text-muted dark:text-text-muted mt-1">
            Helps with scheduling and itinerary building
          </p>
        </div>

        {/* Lead Source Field */}
        <div>
          <label
            htmlFor="leadSource"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            How did they find us?
          </label>
          <select
            id="leadSource"
            value={leadSource}
            onChange={(e) => setLeadSource(e.target.value)}
            className="w-full px-3 py-2 border border-border-default dark:border-border-default rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors"
          >
            <option value="">Select lead source…</option>
            <option value="referral">Referral</option>
            <option value="web">Web Search</option>
            <option value="social">Social Media</option>
            <option value="other">Other</option>
          </select>
          <p className="text-ui-xs text-text-muted dark:text-text-muted mt-1">
            Helps us understand marketing effectiveness
          </p>
        </div>

        {/* Activity Interests Field */}
        <div>
          <label
            htmlFor="activityProvenance"
            className="block text-ui-sm font-medium text-text-primary dark:text-text-primary mb-2"
          >
            What activities interest them?
          </label>
          <textarea
            id="activityProvenance"
            value={activityProvenance}
            onChange={(e) => setActivityProvenance(e.target.value)}
            placeholder="e.g., hiking, museums, fine dining, adventure sports"
            rows={2}
            className="w-full px-3 py-2 border border-border-default dark:border-border-default rounded-lg bg-white dark:bg-canvas text-text-primary dark:text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-blue dark:focus:ring-accent-blue transition-colors"
          />
          <p className="text-ui-xs text-text-muted dark:text-text-muted mt-1">
            Guide interests, not limitations
          </p>
        </div>
      </form>

      {/* Footer with Buttons */}
      <div className="px-6 py-4 border-t border-border-default dark:border-border-default flex gap-3">
        <button
          onClick={handleCancel}
          disabled={isLoading}
          className="flex-1 px-4 py-2 text-ui-sm font-medium text-text-secondary dark:text-text-secondary bg-elevated dark:bg-surface hover:bg-elevated dark:hover:bg-elevated rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={isLoading || !rawNote.trim()}
          className="flex-1 px-4 py-2 text-ui-sm font-medium text-white bg-[rgba(var(--accent-blue-rgb)/0.30)] hover:bg-[rgba(var(--accent-blue-rgb)/0.26)] rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading && <Loader2 className="size-4 animate-spin" />}
          {isLoading ? "Saving…" : "Save"}
        </button>
      </div>
    </div>
  );
}
