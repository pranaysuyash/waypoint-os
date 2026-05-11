'use client';

import { useReducer, useEffect, useCallback } from 'react';
import { ChevronRight, Loader, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { Drawer } from '@/components/ui/drawer';
import { ClientDate } from '@/hooks/useClientDate';
import type { DrillDownMetric } from '@/components/visual/TeamPerformanceChart';

interface Trip {
  tripId: string;
  destinationName?: string;
  status: 'approved' | 'rejected' | 'pending';
  approvalRate?: number;
  responseTime?: number;
  suitabilityScore?: number;
  decisionReason?: string;
  createdAt?: string;
}

type DrawerState =
  | { status: 'idle'; trips: Trip[]; error: null }
  | { status: 'loading'; trips: Trip[]; error: null }
  | { status: 'success'; trips: Trip[]; error: null }
  | { status: 'error'; trips: Trip[]; error: string };

type DrawerAction =
  | { type: 'reset' }
  | { type: 'loading' }
  | { type: 'success'; trips: Trip[] }
  | { type: 'error'; message: string };

const initialDrawerState: DrawerState = {
  status: 'idle',
  trips: [],
  error: null,
};

function drawerReducer(_state: DrawerState, action: DrawerAction): DrawerState {
  switch (action.type) {
    case 'reset':
      return initialDrawerState;
    case 'loading':
      return { status: 'loading', trips: [], error: null };
    case 'success':
      return { status: 'success', trips: action.trips, error: null };
    case 'error':
      return { status: 'error', trips: [], error: action.message };
    default:
      return _state;
  }
}

interface MetricDrillDownDrawerProps {
  isOpen: boolean;
  agentId: string;
  agentName: string;
  metric: DrillDownMetric;
  onClose: () => void;
  onTripSelect: (tripId: string) => void;
}

export function MetricDrillDownDrawer({
  isOpen,
  agentId,
  agentName,
  metric,
  onClose,
  onTripSelect,
}: MetricDrillDownDrawerProps) {
  const [state, dispatch] = useReducer(drawerReducer, initialDrawerState);
  const trips = state.trips;
  const error = state.error;
  const isLoading = state.status === 'loading';

  const fetchTripData = useCallback(() => {
    let ignore = false;

    async function loadTrips() {
      dispatch({ type: 'loading' });
      try {
        const response = await fetch(`/api/insights/agent-trips?agentId=${agentId}&metric=${metric.type}`, {
          credentials: "include",
          cache: "no-store",
        });
        if (!response.ok) throw new Error('Failed to fetch trip data');
        const data = await response.json();
        if (!ignore) {
          dispatch({ type: 'success', trips: data.trips || [] });
        }
      } catch (err) {
        if (!ignore) {
          dispatch({
            type: 'error',
            message: err instanceof Error ? err.message : 'Failed to load trip data',
          });
        }
      }
    }

    loadTrips();

    return () => {
      ignore = true;
    };
  }, [agentId, metric.type]);

  useEffect(() => {
    if (isOpen && agentId) {
      return fetchTripData();
    }
    dispatch({ type: 'reset' });
    return undefined;
  }, [isOpen, agentId, fetchTripData]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className='size-4 text-accent-green' />;
      case 'rejected':
        return <AlertCircle className='size-4 text-accent-red' />;
      default:
        return <Clock className='size-4 text-accent-amber' />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-[rgba(var(--accent-green-rgb),0.15)] text-accent-green';
      case 'rejected':
        return 'bg-[rgba(var(--accent-red-rgb),0.15)] text-accent-red';
      default:
        return 'bg-[rgba(var(--accent-amber-rgb),0.15)] text-accent-amber';
    }
  };

  return (
    <Drawer
      isOpen={isOpen}
      onClose={onClose}
      title={`${metric.label} Details`}
      description={`${agentName} • ${trips.length} trips`}
    >
      {isLoading && (
        <div className='flex items-center justify-center h-full'>
          <div className='flex flex-col items-center gap-2'>
            <Loader className='size-8 text-accent-blue animate-spin' />
            <p className='text-ui-sm text-text-muted'>Loading trip data…</p>
          </div>
        </div>
      )}

      {error && (
        <div className='p-6'>
          <div className='flex items-center gap-3 p-4 rounded-lg bg-[rgba(var(--accent-red-rgb),0.15)] text-accent-red border border-[#da3633]'>
            <AlertCircle className='size-5 flex-shrink-0' />
            <p className='text-ui-sm'>{error}</p>
          </div>
        </div>
      )}

      {!isLoading && !error && trips.length === 0 && (
        <div className='flex items-center justify-center h-full'>
          <div className='text-center'>
            <p className='text-text-muted mb-2'>No trips found for this metric</p>
            <p className='text-ui-xs text-text-tertiary'>
              Try adjusting the time range or metric filters
            </p>
          </div>
        </div>
      )}

      {!isLoading && !error && trips.length > 0 && (
        <div className='space-y-3 p-6'>
          {trips.map((trip) => (
            <button
              key={trip.tripId}
              onClick={() => {
                onTripSelect(trip.tripId);
                onClose();
              }}
              className='w-full text-left p-4 rounded-lg border border-[#30363d] bg-elevated hover:border-[#58a6ff] hover:bg-[#0f1115] transition-all'
            >
              <div className='flex items-start justify-between mb-2'>
                <div className='flex-1'>
                  <p className='font-medium text-text-primary mb-1'>
                    {trip.destinationName || 'Trip ' + trip.tripId.substring(0, 8)}
                  </p>
                  <p className='text-ui-xs text-text-muted'>ID: {trip.tripId}</p>
                </div>
                <div className='flex items-center gap-2 ml-4'>
                  {getStatusIcon(trip.status)}
                  <span
                    className={`px-2 py-1 rounded text-ui-xs font-medium ${getStatusColor(
                      trip.status
                    )}`}
                  >
                    {trip.status}
                  </span>
                </div>
              </div>

              <div className='grid grid-cols-3 gap-3 mb-3 text-ui-xs'>
                {trip.responseTime !== undefined && (
                  <div>
                    <span className='text-text-muted block mb-1'>Response</span>
                    <span className='text-text-primary font-medium'>
                      {trip.responseTime}h
                    </span>
                  </div>
                )}
                {trip.suitabilityScore !== undefined && (
                  <div>
                    <span className='text-text-muted block mb-1'>Suitability</span>
                    <span className='text-text-primary font-medium'>
                      {trip.suitabilityScore}%
                    </span>
                  </div>
                )}
                {trip.createdAt && (
                  <div>
                    <span className='text-text-muted block mb-1'>Date</span>
                    <span className='text-text-primary font-medium'>
                      <ClientDate value={trip.createdAt} />
                    </span>
                  </div>
                )}
              </div>

              {trip.decisionReason && (
                <p className='text-ui-xs text-text-muted mb-3 p-2 rounded bg-[#0f1115]'>
                  <span className='font-medium'>Reason:</span> {trip.decisionReason}
                </p>
              )}

              <div className='flex items-center justify-between text-ui-xs text-accent-blue'>
                <span>View timeline</span>
                <ChevronRight className='size-4' />
              </div>
            </button>
          ))}
        </div>
      )}
    </Drawer>
  );
}
