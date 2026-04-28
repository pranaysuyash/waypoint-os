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
      });

      setRawNote("");
      setOwnerNote("");
      setFollowUpDueDate("");
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
    setErrors({});
    setApiError(null);
    onCancel();
  };

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-950 border-l border-gray-200 dark:border-gray-800">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Capture Call
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          Record the customer's travel intent and next steps
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {/* API Error Alert */}
        {apiError && (
          <div className="p-3 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-red-900 dark:text-red-100">
                Error saving call
              </p>
              <p className="text-xs text-red-800 dark:text-red-200 mt-0.5">{apiError}</p>
            </div>
          </div>
        )}

        {/* Raw Note Field */}
        <div>
          <label
            htmlFor="rawNote"
            className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2"
          >
            What did the customer tell you?
          </label>
          <textarea
            id="rawNote"
            value={rawNote}
            onChange={(e) => {
              setRawNote(e.target.value);
              if (errors.rawNote) {
                setErrors({ ...errors, rawNote: "" });
              }
            }}
            placeholder="e.g., Family of 4 wants to explore Japan, late November..."
            rows={4}
            className={`w-full px-3 py-2 border rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors ${
              errors.rawNote
                ? "border-red-300 dark:border-red-700"
                : "border-gray-300 dark:border-gray-700"
            }`}
          />
          {errors.rawNote && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">{errors.rawNote}</p>
          )}
        </div>

        {/* Owner Note Field */}
        <div>
          <label
            htmlFor="ownerNote"
            className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2"
          >
            Any notes for yourself?
          </label>
          <textarea
            id="ownerNote"
            value={ownerNote}
            onChange={(e) => setOwnerNote(e.target.value)}
            placeholder="e.g., Mentioned budget concerns, needs early morning flights..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
          />
        </div>

        {/* Follow-up Due Date Field */}
        <div>
          <label
            htmlFor="followUpDueDate"
            className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-2"
          >
            Promise to follow up by:
          </label>
          <input
            id="followUpDueDate"
            type="datetime-local"
            value={followUpDueDate}
            onChange={(e) => setFollowUpDueDate(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 transition-colors"
          />
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Leave blank if no promise was made
          </p>
        </div>
      </form>

      {/* Footer with Buttons */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-800 flex gap-3">
        <button
          onClick={handleCancel}
          disabled={isLoading}
          className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={isLoading || !rawNote.trim()}
          className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          {isLoading ? "Saving..." : "Save"}
        </button>
      </div>
    </div>
  );
}
