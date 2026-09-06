'use client';

import { startTransition, useEffect, useState, useRef, useCallback } from 'react';

export interface TripStreamEvent {
  event_id?: string;
  trip_id?: string;
  action?: string;
  timestamp?: string;
  details?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface UseTripStreamOptions {
  enabled?: boolean;
  onEvent?: (event: TripStreamEvent) => void;
}

export function useTripStream(tripId: string | null | undefined, options: UseTripStreamOptions = {}) {
  const { enabled = true, onEvent } = options;
  const [events, setEvents] = useState<TripStreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  useEffect(() => {
    if (!tripId || !enabled || typeof window === 'undefined') {
      startTransition(() => setIsConnected(false));
      return;
    }

    let isUnmounted = false;
    const sseUrl = `/api/trips/${encodeURIComponent(tripId)}/events/stream`;

    try {
      const eventSource = new EventSource(sseUrl, { withCredentials: true });
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        if (!isUnmounted) {
          setIsConnected(true);
          setError(null);
        }
      };

      eventSource.addEventListener('agent_event', (event: MessageEvent) => {
        try {
          const parsed = JSON.parse(event.data) as TripStreamEvent;
          if (!isUnmounted) {
            setEvents((prev) => [...prev, parsed]);
            if (onEventRef.current) {
              onEventRef.current(parsed);
            }
          }
        } catch {
          // Ignore JSON parse errors on malformed heartbeat
        }
      });

      eventSource.onerror = () => {
        if (!isUnmounted) {
          setIsConnected(false);
          setError(new Error('Event stream connection interrupted'));
        }
      };
    } catch (err) {
      if (!isUnmounted) {
        startTransition(() => {
          setIsConnected(false);
          setError(err instanceof Error ? err : new Error('Failed to create EventSource'));
        });
      }
    }

    return () => {
      isUnmounted = true;
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      startTransition(() => setIsConnected(false));
    };
  }, [tripId, enabled]);

  return {
    events,
    isConnected,
    error,
    clearEvents,
  };
}
