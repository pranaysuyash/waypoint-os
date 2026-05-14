'use client';

import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import Link from 'next/link';
import { useTripContext } from '@/contexts/TripContext';
import OpsPanel from '@/app/(agency)/workbench/OpsPanel';
import { getTripRoute } from '@/lib/routes';

const MIGRATION_BANNER_KEY = 'waypoint:ops-migration-banner-dismissed:v1';

function OpsMigrationBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    try {
      const dismissed = localStorage.getItem(MIGRATION_BANNER_KEY);
      if (!dismissed) setVisible(true);
    } catch {
      // localStorage unavailable (SSR guard)
    }
  }, []);

  if (!visible) return null;

  function dismiss() {
    try {
      localStorage.setItem(MIGRATION_BANNER_KEY, '1');
    } catch {
      // ignore
    }
    setVisible(false);
  }

  return (
    <div className="mb-4 flex items-start justify-between gap-3 rounded-lg border border-[rgba(88,166,255,0.25)] bg-[rgba(88,166,255,0.07)] px-4 py-3">
      <p className="text-[13px] text-[#c9d1d9]">
        <span className="font-semibold text-[#58a6ff]">Booking operations have moved here from Workbench.</span>
        {' '}This trip page is now the durable home for booking tasks, documents, payments, and readiness.
      </p>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Dismiss"
        className="shrink-0 mt-0.5 text-[var(--text-tertiary)] hover:text-[#e6edf3] transition-colors"
      >
        <X className="size-4" aria-hidden="true" />
      </button>
    </div>
  );
}

export default function OpsPageClient() {
  const { tripId, trip } = useTripContext();

  if (!tripId || !trip) return null;

  const canAccessOps = trip.stage === 'proposal' || trip.stage === 'booking';

  if (!canAccessOps) {
    return (
      <div className="p-6">
        <div data-testid="ops-stage-gate" className="rounded-xl border border-[#30363d] bg-[#0f1115] p-5 space-y-3">
          <h2 className="text-sm font-semibold text-[#e6edf3]">Ops not available yet</h2>
          <p className="text-sm text-[#8b949e]">
            Booking operations unlock when this trip reaches proposal or booking stage.
          </p>
          <Link
            href={getTripRoute(tripId, 'intake')}
            className="inline-block text-sm text-[#58a6ff] hover:underline"
          >
            Return to Intake
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <OpsMigrationBanner />
      <OpsPanel trip={trip} mode="full" />
    </div>
  );
}
