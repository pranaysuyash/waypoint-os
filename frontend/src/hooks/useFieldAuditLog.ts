/**
 * Hook for tracking and managing field change audit logs.
 * Changes are stored in localStorage for persistence across sessions.
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import type { FieldChange, AuditLog, TripFieldType, FieldChangeType } from '@/types/audit';

const STORAGE_PREFIX = 'trip_audit_';

interface UseFieldAuditLogOptions {
  tripId: string;
  userId?: string;
  userName?: string;
}

/**
 * Hook for managing field change audit logs.
 *
 * @example
 * const { logChange, getChanges, getAuditLog } = useFieldAuditLog({
 *   tripId: 'trip-123',
 *   userId: 'user-1',
 *   userName: 'John Doe'
 * });
 *
 * // Log a change
 * logChange('destination', 'update', 'Paris', 'London', 'Customer changed destination');
 */
export function useFieldAuditLog({
  tripId,
  userId = 'current-user',
  userName = 'Current User',
}: UseFieldAuditLogOptions) {
  const [auditLog, setAuditLog] = useState<AuditLog | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load audit log from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem(`${STORAGE_PREFIX}${tripId}`);
      if (stored) {
        const parsed = JSON.parse(stored) as AuditLog;
        // Validate basic structure
        if (parsed.tripId === tripId && Array.isArray(parsed.changes)) {
          setAuditLog(parsed);
        }
      } else {
        // Initialize new audit log
        setAuditLog({
          tripId,
          changes: [],
          lastModified: new Date().toISOString(),
          version: 0,
        });
      }
    } catch (error) {
      console.error('Failed to load audit log:', error);
      // Initialize empty log on error
      setAuditLog({
        tripId,
        changes: [],
        lastModified: new Date().toISOString(),
        version: 0,
      });
    } finally {
      setIsLoading(false);
    }
  }, [tripId]);

  // Save audit log to localStorage
  const saveAuditLog = useCallback((log: AuditLog) => {
    try {
      localStorage.setItem(`${STORAGE_PREFIX}${tripId}`, JSON.stringify(log));
    } catch (error) {
      console.error('Failed to save audit log:', error);
    }
  }, [tripId]);

  /**
   * Log a field change to the audit trail.
   */
  const logChange = useCallback((
    field: TripFieldType,
    changeType: FieldChangeType,
    previousValue: string | number | null,
    newValue: string | number | null,
    reason?: string
  ) => {
    if (!auditLog) return;

    const change: FieldChange = {
      id: `change_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      tripId,
      field,
      changeType,
      previousValue,
      newValue,
      changedBy: userId,
      changedByName: userName,
      timestamp: new Date().toISOString(),
      reason,
    };

    const updatedLog: AuditLog = {
      ...auditLog,
      changes: [...auditLog.changes, change],
      lastModified: change.timestamp,
      version: auditLog.version + 1,
    };

    setAuditLog(updatedLog);
    saveAuditLog(updatedLog);

    return change;
  }, [auditLog, tripId, userId, userName, saveAuditLog]);

  /**
   * Get all changes for this trip.
   */
  const getChanges = useCallback((): FieldChange[] => {
    return auditLog?.changes ?? [];
  }, [auditLog]);

  /**
   * Get changes for a specific field.
   */
  const getChangesForField = useCallback((field: TripFieldType): FieldChange[] => {
    return auditLog?.changes.filter(c => c.field === field) ?? [];
  }, [auditLog]);

  /**
   * Get the most recent change for a field.
   */
  const getLatestChangeForField = useCallback((field: TripFieldType): FieldChange | null => {
    const fieldChanges = getChangesForField(field);
    if (fieldChanges.length === 0) return null;
    // Sort by timestamp descending and return first
    return fieldChanges.toSorted((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    )[0];
  }, [getChangesForField]);

  /**
   * Get the complete audit log.
   */
  const getAuditLog = useCallback((): AuditLog | null => {
    return auditLog;
  }, [auditLog]);

  /**
   * Clear all changes for this trip (use with caution).
   */
  const clearChanges = useCallback(() => {
    if (!confirm('Are you sure you want to clear all change history for this trip?')) {
      return;
    }

    const clearedLog: AuditLog = {
      tripId,
      changes: [],
      lastModified: new Date().toISOString(),
      version: 0,
    };

    setAuditLog(clearedLog);
    saveAuditLog(clearedLog);
  }, [tripId, saveAuditLog]);

  /**
   * Export changes as JSON.
   */
  const exportChanges = useCallback((): string => {
    if (!auditLog) return '{}';
    return JSON.stringify(auditLog, null, 2);
  }, [auditLog]);

  return {
    auditLog,
    isLoading,
    logChange,
    getChanges,
    getChangesForField,
    getLatestChangeForField,
    getAuditLog,
    clearChanges,
    exportChanges,
  };
}

/**
 * Hook for accessing all audit logs across trips (admin function).
 */
export function useAllAuditLogs() {
  const [logs, setLogs] = useState<Record<string, AuditLog>>({});
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    try {
      const allLogs: Record<string, AuditLog> = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.startsWith(STORAGE_PREFIX)) {
          const tripId = key.substring(STORAGE_PREFIX.length);
          const value = localStorage.getItem(key);
          if (value) {
            const parsed = JSON.parse(value) as AuditLog;
            allLogs[tripId] = parsed;
          }
        }
      }
      setLogs(allLogs);
    } catch (error) {
      console.error('Failed to load audit logs:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { logs, isLoading };
}
