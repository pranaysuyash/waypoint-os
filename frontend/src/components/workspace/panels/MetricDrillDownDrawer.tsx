'use client';

import { useState, useEffect, useCallback } from 'react';
import { X, ChevronRight, Loader, AlertCircle, CheckCircle, Clock } from 'lucide-react';
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
  const [trips, setTrips] = useState<Trip[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTripData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/insights/agent-trips?agentId=${agentId}&metric=${metric.type}`);
      if (!response.ok) throw new Error('Failed to fetch trip data');
      const data = await response.json();
      setTrips(data.trips || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load trip data');
      setTrips([]);
    } finally {
      setIsLoading(false);
    }
  }, [agentId, metric.type]);

  useEffect(() => {
    if (isOpen && agentId) {
      fetchTripData();
    }
  }, [isOpen, agentId, fetchTripData]);

  if (!isOpen) return null;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className='h-4 w-4 text-[#3fb950]' />;
      case 'rejected':
        return <AlertCircle className='h-4 w-4 text-[#f85149]' />;
      default:
        return <Clock className='h-4 w-4 text-[#d29922]' />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'bg-[#0f3819] text-[#3fb950]';
      case 'rejected':
        return 'bg-[#3d0a0a] text-[#f85149]';
      default:
        return 'bg-[#3d2f0a] text-[#d29922]';
    }
  };

  return (
    <div className='fixed inset-0 z-50'>
      {/* Overlay */}
      <div
        className='absolute inset-0 bg-black/50'
        onClick={onClose}
      />

      {/* Drawer */}
      <div className='absolute right-0 top-0 h-full w-full max-w-2xl bg-[#0d1117] border-l border-[#30363d] shadow-lg flex flex-col'>
        {/* Header */}
        <div className='border-b border-[#30363d] p-6'>
          <div className='flex items-center justify-between mb-2'>
            <h2 className='text-lg font-semibold text-[#e6edf3]'>
              {metric.label} Details
            </h2>
            <button
              onClick={onClose}
              className='p-2 hover:bg-[#161b22] rounded-lg transition-colors'
            >
              <X className='h-5 w-5 text-[#8b949e]' />
            </button>
          </div>
          <p className='text-sm text-[#8b949e]'>
            {agentName} • {trips.length} trips
          </p>
        </div>

        {/* Content */}
        <div className='flex-1 overflow-y-auto'>
          {isLoading && (
            <div className='flex items-center justify-center h-full'>
              <div className='flex flex-col items-center gap-2'>
                <Loader className='h-8 w-8 text-[#58a6ff] animate-spin' />
                <p className='text-sm text-[#8b949e]'>Loading trip data...</p>
              </div>
            </div>
          )}

          {error && (
            <div className='p-6'>
              <div className='flex items-center gap-3 p-4 rounded-lg bg-[#3d0a0a] text-[#f85149] border border-[#da3633]'>
                <AlertCircle className='h-5 w-5 flex-shrink-0' />
                <p className='text-sm'>{error}</p>
              </div>
            </div>
          )}

          {!isLoading && !error && trips.length === 0 && (
            <div className='flex items-center justify-center h-full'>
              <div className='text-center'>
                <p className='text-[#8b949e] mb-2'>No trips found for this metric</p>
                <p className='text-xs text-[#6e7681]'>
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
                  className='w-full text-left p-4 rounded-lg border border-[#30363d] bg-[#161b22] hover:border-[#58a6ff] hover:bg-[#0f1115] transition-all'
                >
                  <div className='flex items-start justify-between mb-2'>
                    <div className='flex-1'>
                      <p className='font-medium text-[#e6edf3] mb-1'>
                        {trip.destinationName || 'Trip ' + trip.tripId.substring(0, 8)}
                      </p>
                      <p className='text-xs text-[#8b949e]'>ID: {trip.tripId}</p>
                    </div>
                    <div className='flex items-center gap-2 ml-4'>
                      {getStatusIcon(trip.status)}
                      <span
                        className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(
                          trip.status
                        )}`}
                      >
                        {trip.status}
                      </span>
                    </div>
                  </div>

                  <div className='grid grid-cols-3 gap-3 mb-3 text-xs'>
                    {trip.responseTime !== undefined && (
                      <div>
                        <span className='text-[#8b949e] block mb-1'>Response</span>
                        <span className='text-[#e6edf3] font-medium'>
                          {trip.responseTime}h
                        </span>
                      </div>
                    )}
                    {trip.suitabilityScore !== undefined && (
                      <div>
                        <span className='text-[#8b949e] block mb-1'>Suitability</span>
                        <span className='text-[#e6edf3] font-medium'>
                          {trip.suitabilityScore}%
                        </span>
                      </div>
                    )}
                    {trip.createdAt && (
                      <div>
                        <span className='text-[#8b949e] block mb-1'>Date</span>
                        <span className='text-[#e6edf3] font-medium'>
                          {new Date(trip.createdAt).toLocaleDateString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {trip.decisionReason && (
                    <p className='text-xs text-[#8b949e] mb-3 p-2 rounded bg-[#0f1115]'>
                      <span className='font-medium'>Reason:</span> {trip.decisionReason}
                    </p>
                  )}

                  <div className='flex items-center justify-between text-xs text-[#58a6ff]'>
                    <span>View timeline</span>
                    <ChevronRight className='h-4 w-4' />
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
