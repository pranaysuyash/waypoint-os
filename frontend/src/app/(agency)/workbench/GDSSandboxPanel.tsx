'use client';

import React, { useState } from 'react';
import { Plane, Ticket } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: this panel renders offers fabricated by the deterministic
 * Amadeus/Sabre sandbox simulators (no live GDS connectivity exists). Every
 * "Live" claim has been replaced with explicit simulated language.
 */

export default function GDSSandboxPanel() {
  const [provider, setProvider] = useState<'amadeus' | 'sabre'>('amadeus');
  const [origin, setOrigin] = useState('JFK');
  const [destination, setDestination] = useState('LHR');
  const [isSearching, setIsSearching] = useState(false);
  const [offers, setOffers] = useState<Array<{
    offer_id: string;
    provider: string;
    carrier_code: string;
    flight_number: string;
    origin_iata: string;
    destination_iata: string;
    departure_time: string;
    arrival_time: string;
    cabin_class: string;
    total_price_usd: number;
    fare_basis_code: string;
    seats_available: number;
  }>>([]);
  const [bookingResult, setBookingResult] = useState<{
    booking_reference: string | null;
    provider: string;
    pnr_locator: string | null;
    e_ticket_number: string | null;
    total_charged_usd: number | null;
    status: string;
  } | null>(null);

  const handleSearch = async () => {
    setIsSearching(true);
    setBookingResult(null);
    try {
      const res = await fetch('/api/v1/gds-sandbox/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          origin_iata: origin,
          destination_iata: destination,
          departure_date: '2026-10-15',
          cabin_class: 'BUSINESS',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setOffers(data.flight_offers);
      }
    } catch {
      // Fallback local preview
      setOffers([
        {
          offer_id: provider === 'amadeus' ? 'AMD-OFF-91A23C' : 'SBR-BFM-88214D',
          provider,
          carrier_code: provider === 'amadeus' ? 'BA' : 'AA',
          flight_number: provider === 'amadeus' ? 'BA178' : 'AA100',
          origin_iata: origin,
          destination_iata: destination,
          departure_time: '2026-10-15T11:40:00Z',
          arrival_time: '2026-10-15T14:25:00Z',
          cabin_class: 'BUSINESS',
          total_price_usd: provider === 'amadeus' ? 3620.0 : 3490.0,
          fare_basis_code: 'JFFLEX26',
          seats_available: 4,
        },
      ]);
    } finally {
      setIsSearching(false);
    }
  };

  const handleBook = async (offerId: string) => {
    try {
      const res = await fetch('/api/v1/gds-sandbox/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          provider,
          offer_id: offerId,
          traveler_name: 'Sample Traveler',
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setBookingResult(data.booking_result);
      }
    } catch {
      setBookingResult({
        booking_reference: null,
        provider,
        pnr_locator: null,
        e_ticket_number: null,
        total_charged_usd: null,
        status: 'PREVIEW_ONLY',
      });
    }
  };

  return (
    <div className="p-4 rounded-xl border border-border bg-card space-y-4">
      <div className="flex items-center justify-between gap-3">
        <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Plane className="h-4 w-4 text-sky-400" />
          Dual-Stack Simulated GDS Sandbox (Amadeus & Sabre Deterministic Simulators)
        </h4>
        <div className="flex items-center gap-2 shrink-0">
          <SimulatedBadge label="Simulated sandbox" />
          <span className="text-[10px] font-mono bg-sky-500/10 text-sky-400 px-2 py-0.5 rounded">MILESTONE 3 · SANDBOX SIMULATORS (NO LIVE GDS)</span>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-3">
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">GDS Sandbox Provider</label>
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value as any)}
            className="w-full p-2 text-xs font-semibold rounded border border-border bg-background text-foreground"
          >
            <option value="amadeus">Amadeus Travel Innovation (1A)</option>
            <option value="sabre">Sabre Dev Studio BFM (1S)</option>
          </select>
        </div>
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">Origin (IATA)</label>
          <input
            value={origin}
            onChange={(e) => setOrigin(e.target.value.toUpperCase())}
            className="w-full p-2 text-xs font-mono font-bold rounded border border-border bg-background text-foreground"
          />
        </div>
        <div>
          <label className="text-[10px] font-mono text-muted-foreground block mb-1">Destination (IATA)</label>
          <input
            value={destination}
            onChange={(e) => setDestination(e.target.value.toUpperCase())}
            className="w-full p-2 text-xs font-mono font-bold rounded border border-border bg-background text-foreground"
          />
        </div>
        <div className="flex items-end">
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="w-full py-2 px-3 rounded-lg bg-sky-500 text-white text-xs font-semibold hover:bg-sky-600 flex items-center justify-center gap-1.5"
          >
            <Plane className={`h-3.5 w-3.5 ${isSearching ? 'animate-pulse' : ''}`} />
            {isSearching ? 'Computing local preview...' : 'Compute flight preview'}
          </button>
        </div>
      </div>

      {bookingResult && (
        <div className="p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-semibold flex items-center justify-between gap-2">
          <span className="flex items-center gap-2">
            <Ticket className="h-4 w-4" />
            Booking preview generated for {bookingResult.provider.toUpperCase()} — no PNR, ticket, charge, or provider confirmation was created
          </span>
          <span className="font-mono">PREVIEW ONLY</span>
        </div>
      )}

      {offers.length > 0 && (
        <div className="space-y-2 pt-1">
          <span className="text-[11px] font-mono text-muted-foreground block">
            {offers.length} Simulated Sandbox Flight Offers Returned (deterministic fixtures, not a live GDS):
          </span>
          <div className="grid grid-cols-2 gap-3">
            {offers.map((off) => (
              <div key={off.offer_id} className="p-3 rounded-lg border border-border bg-background space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-foreground">{off.carrier_code} #{off.flight_number} ({off.origin_iata} → {off.destination_iata})</span>
                  <span className="font-mono font-bold text-foreground">${off.total_price_usd}</span>
                </div>
                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>Fare Basis: <strong className="text-foreground">{off.fare_basis_code}</strong></span>
                  <span>{off.seats_available} Seats Left</span>
                </div>
                <button
                  onClick={() => handleBook(off.offer_id)}
                  className="w-full py-1.5 px-2 bg-primary text-primary-foreground rounded text-xs font-semibold hover:bg-primary/90 flex items-center justify-center gap-1"
                >
                  <Ticket className="h-3.5 w-3.5" />
                  Preview booking (no ticketing)
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
