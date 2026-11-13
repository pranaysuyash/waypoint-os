'use client';

import { Suspense, useCallback, useId, useMemo, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
  AlertCircle,
  Building2,
  CalendarClock,
  CheckCircle2,
  FileSpreadsheet,
  Info,
  Layers,
  Plus,
  Search,
  ShieldAlert,
  Trash2,
  X,
} from 'lucide-react';
import { SimulatedBadge } from '@/components/ui/SimulatedBadge';
import { ScopedTripPickerBar } from '@/components/workspace/ScopedTripPickerBar';
import { useSupplierLedger } from '@/hooks/useSuppliers';
import { useTrip } from '@/hooks/useTrips';
import type {
  SupplierContractRecord,
  SupplierRateTableItem,
  Trip,
} from '@/lib/api-client';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';

export type SupplierCategoryKey =
  | 'dmc'
  | 'hotel'
  | 'airline'
  | 'rail_charter'
  | 'transfer'
  | 'safari'
  | 'insurance';

export const SUPPLIER_CATEGORY_LABELS: Record<SupplierCategoryKey, string> = {
  dmc: 'DMCs & Inbound',
  hotel: 'Hotels & Resorts',
  airline: 'Airlines',
  rail_charter: 'Rail & Charter',
  transfer: 'Transfers',
  safari: 'Safari & Camps',
  insurance: 'Insurance',
};

const SUPPLIER_CATEGORY_FILTERS: Array<{ id: 'all' | SupplierCategoryKey; label: string }> = [
  { id: 'all', label: 'All Categories' },
  { id: 'dmc', label: 'DMCs & Inbound' },
  { id: 'hotel', label: 'Hotels & Resorts' },
  { id: 'airline', label: 'Airlines' },
  { id: 'rail_charter', label: 'Rail & Charter' },
  { id: 'transfer', label: 'Transfers' },
  { id: 'safari', label: 'Safari & Camps' },
  { id: 'insurance', label: 'Insurance' },
];

interface SampleSupplierFixture {
  id: string;
  name: string;
  category: SupplierCategoryKey;
  region: string;
  settlementTerms: string;
  responseSla: string;
  notes: string;
}

const SAMPLE_SUPPLIERS: SampleSupplierFixture[] = [
  {
    id: 'fx-dmc-japan',
    name: 'Kyoto Heritage DMC (illustrative)',
    category: 'dmc',
    region: 'Japan & East Asia',
    settlementTerms: '20% deposit · 21d pre-arrival balance (illustrative)',
    responseSla: 'Sample SLA: 4h',
    notes: 'Placeholder boutique ground-handling record — not an active contract.',
  },
  {
    id: 'fx-resort-amalfi',
    name: 'Amalfi Cliffside Collection (illustrative)',
    category: 'hotel',
    region: 'Mediterranean Europe',
    settlementTerms: 'Net 30 · 14d release (illustrative)',
    responseSla: 'Sample SLA: Same day',
    notes: 'Illustrative villa & sea-view room inventory placeholder.',
  },
  {
    id: 'fx-airline-gds',
    name: 'Global Premium Carrier Desk (illustrative)',
    category: 'airline',
    region: 'International Long-Haul',
    settlementTerms: 'BSP / ARC 24h ticketing window (illustrative)',
    responseSla: 'Sample SLA: 2h',
    notes: 'Illustrative private fare & group block desk — not an active GDS feed.',
  },
  {
    id: 'fx-safari-serengeti',
    name: 'Serengeti Canvas Camps (illustrative)',
    category: 'safari',
    region: 'East Africa',
    settlementTerms: '30% deposit · 45d final (illustrative)',
    responseSla: 'Sample SLA: 6h',
    notes: 'Sample fly-in circuit fixture — verify real allotment before quoting.',
  },
  {
    id: 'fx-rail-alpine',
    name: 'Swiss Scenic Rail Desk (illustrative)',
    category: 'rail_charter',
    region: 'Central Europe',
    settlementTerms: 'Instant ticket issue (illustrative)',
    responseSla: 'Sample SLA: 2h',
    notes: 'Illustrative panoramic train charter reference entry.',
  },
  {
    id: 'fx-transfer-chauffeured',
    name: 'European Chauffeur & VIP Meet (illustrative)',
    category: 'transfer',
    region: 'Western Europe & UK',
    settlementTerms: 'Net 15 · 48h free amend (illustrative)',
    responseSla: 'Sample SLA: 2h',
    notes: 'Placeholder airport tarmac & private sedan transfer partner.',
  },
  {
    id: 'fx-dmc-dubai',
    name: 'Arabian Sands Concierge (illustrative)',
    category: 'dmc',
    region: 'Middle East',
    settlementTerms: 'Net 15 · 7d cut-off (illustrative)',
    responseSla: 'Sample SLA: 3h',
    notes: 'Placeholder desert transfer & yacht charter partner.',
  },
  {
    id: 'fx-resort-maldives',
    name: 'Baa Atoll Overwater Sanctuary (illustrative)',
    category: 'hotel',
    region: 'Indian Ocean',
    settlementTerms: '50% deposit · 30d balance (illustrative)',
    responseSla: 'Sample SLA: 5h',
    notes: 'Sample honeymoon seaplane package fixture.',
  },
  {
    id: 'fx-insurance-global',
    name: 'Expedition & Cancel-For-Any-Reason Cover (illustrative)',
    category: 'insurance',
    region: 'Worldwide Coverage',
    settlementTerms: 'Per-policy instant issue (illustrative)',
    responseSla: 'Sample SLA: Same day',
    notes: 'Illustrative high-value trip protection underwriter placeholder.',
  },
];

function fmtSupplierMoney(amount: number, currency: string): string {
  const code = (currency || 'USD').toUpperCase();
  try {
    if (code === 'INR') {
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0,
      }).format(amount);
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: code,
      maximumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${code} ${amount.toFixed(0)}`;
  }
}

function fmtShortDateTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

export default function SuppliersPage() {
  return (
    <Suspense fallback={<div className='p-6 text-[#8b949e]'>Loading suppliers workspace…</div>}>
      <SuppliersContent />
    </Suspense>
  );
}

function SuppliersContent() {
  const searchParams = useSearchParams();
  const urlTripId = searchParams.get('tripId') || searchParams.get('trip') || '';
  const baseId = useId();

  const [selectedTripId, setSelectedTripId] = useState<string>(urlTripId);
  const [selectedTrip, setSelectedTrip] = useState<Trip | undefined>(undefined);
  const { data: selectedTripDetail } = useTrip(selectedTripId || null);

  const activeTripDetail = selectedTripDetail ?? selectedTrip;
  const supplierRiskLevel = activeTripDetail?.agentOperations?.supplierRiskLevel ?? null;
  const supplierSnapshot = activeTripDetail?.agentOperations?.supplierIntelligenceSnapshot ?? null;

  const handleSelectTrip = useCallback((tripId: string, trip: Trip | undefined) => {
    setSelectedTripId(tripId);
    setSelectedTrip(trip);
  }, []);

  const {
    contracts,
    holds,
    isLoading: ledgerLoading,
    error: ledgerError,
    uploadContract,
    createSoftHold,
  } = useSupplierLedger();

  // Unified supplier category + sample search filter
  const [sampleSearch, setSampleSearch] = useState('');
  const [sampleCategory, setSampleCategory] =
    useState<'all' | SupplierCategoryKey>('all');
  const [contractCategory, setContractCategory] =
    useState<'all' | SupplierCategoryKey>('all');

  const filteredContracts = useMemo(() => {
    if (contractCategory === 'all') return contracts;
    return contracts.filter(
      (c) => ((c.supplier_category || 'dmc').toLowerCase() as SupplierCategoryKey) === contractCategory
    );
  }, [contracts, contractCategory]);

  const filteredSamples = useMemo(() => {
    const q = sampleSearch.trim().toLowerCase();
    return SAMPLE_SUPPLIERS.filter((item) => {
      if (sampleCategory !== 'all' && item.category !== sampleCategory) return false;
      if (!q) return true;
      return (
        item.name.toLowerCase().includes(q) ||
        item.region.toLowerCase().includes(q) ||
        item.notes.toLowerCase().includes(q) ||
        SUPPLIER_CATEGORY_LABELS[item.category].toLowerCase().includes(q)
      );
    });
  }, [sampleSearch, sampleCategory]);

  // Contract upload modal state
  const [uploadOpen, setUploadOpen] = useState(false);
  const [supplierName, setSupplierName] = useState('');
  const [supplierCategory, setSupplierCategory] = useState<SupplierCategoryKey>('dmc');
  const [destination, setDestination] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [currency, setCurrency] = useState('INR');
  const [termsText, setTermsText] = useState('');
  const [rateRows, setRateRows] = useState<SupplierRateTableItem[]>([
    {
      room_type: 'Deluxe Room',
      net_rate_per_night: 12000,
      rack_rate_per_night: 16500,
      cancellation_lead_days: 7,
    },
  ]);
  const [uploadSubmitting, setUploadSubmitting] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [actionBanner, setActionBanner] = useState<string | null>(null);

  // Soft-hold modal state
  const [holdContract, setHoldContract] = useState<SupplierContractRecord | null>(null);
  const [holdRoomType, setHoldRoomType] = useState('');
  const [holdGuestName, setHoldGuestName] = useState('');
  const [holdCheckIn, setHoldCheckIn] = useState('');
  const [holdCheckOut, setHoldCheckOut] = useState('');
  const [holdSubmitting, setHoldSubmitting] = useState(false);
  const [holdError, setHoldError] = useState<string | null>(null);

  const openUploadModal = () => {
    setUploadError(null);
    if (!destination && selectedTrip?.destination) {
      setDestination(selectedTrip.destination);
    }
    setUploadOpen(true);
  };

  const openHoldModal = (contract: SupplierContractRecord) => {
    setHoldError(null);
    setHoldContract(contract);
    setHoldRoomType(contract.rate_table[0]?.room_type || '');
    setHoldGuestName('');
    setHoldCheckIn('');
    setHoldCheckOut('');
  };

  const handleUploadSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setUploadError(null);

    if (!supplierName.trim() || !destination.trim()) {
      setUploadError('Supplier name and destination are required.');
      return;
    }

    const validRates = rateRows.filter(
      (r) => r.room_type.trim() && Number.isFinite(r.net_rate_per_night) && r.net_rate_per_night > 0
    );
    if (validRates.length === 0) {
      setUploadError('Add at least one room tier with a positive net rate.');
      return;
    }

    setUploadSubmitting(true);
    try {
      const res = await uploadContract({
        supplier_name: supplierName.trim(),
        supplier_category: supplierCategory,
        destination: destination.trim(),
        contact_email: contactEmail.trim() || undefined,
        currency,
        terms_and_conditions: termsText.trim() || undefined,
        rate_table: validRates.map((r) => ({
          ...r,
          room_type: r.room_type.trim(),
        })),
      });
      setActionBanner(
        `Saved contract for ${res.supplier_name} (${res.total_rates_ingested} room rate${
          res.total_rates_ingested === 1 ? '' : 's'
        }).`
      );
      setUploadOpen(false);
      setSupplierName('');
      setContactEmail('');
      setTermsText('');
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Failed to save contract.');
    } finally {
      setUploadSubmitting(false);
    }
  };

  const handleSoftHoldSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!holdContract) return;
    setHoldError(null);

    if (!holdGuestName.trim() || !holdRoomType || !holdCheckIn || !holdCheckOut) {
      setHoldError('Room tier, guest name, check-in, and check-out dates are required.');
      return;
    }

    setHoldSubmitting(true);
    try {
      const res = await createSoftHold({
        contract_id: holdContract.contract_id,
        room_type: holdRoomType,
        guest_name: holdGuestName.trim(),
        check_in: holdCheckIn,
        check_out: holdCheckOut,
      });
      setActionBanner(
        `Reserved 48h soft-hold (${res.hold_id}) for ${holdGuestName.trim()} — estimated margin ${fmtSupplierMoney(
          res.estimated_agency_margin,
          holdContract.currency
        )}.`
      );
      setHoldContract(null);
    } catch (err) {
      setHoldError(err instanceof Error ? err.message : 'Failed to reserve soft-hold.');
    } finally {
      setHoldSubmitting(false);
    }
  };

  const contractsById = useMemo(
    () => new Map(contracts.map((c) => [c.contract_id, c])),
    [contracts]
  );

  return (
    <div className='p-6 space-y-6'>
      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center justify-between gap-4'>
        <div>
          <div className='flex flex-wrap items-center gap-2.5'>
            <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
              <Building2 className='size-5 text-[#58a6ff]' aria-hidden='true' />
              Suppliers &amp; DMC Directory
            </h1>
            <SimulatedBadge label='Sample data' />
          </div>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Operator-recorded wholesale rate sheets, 48h inventory soft-holds, and trip supplier readiness.
          </p>
        </div>

        <button
          type='button'
          data-testid='open-upload-contract-btn'
          onClick={openUploadModal}
          className='px-3.5 py-2 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors self-start md:self-auto'
        >
          <Plus className='size-4' aria-hidden='true' />
          Upload Rate Sheet
        </button>
      </div>

      {/* KPI Metrics */}
      <div className='grid grid-cols-2 lg:grid-cols-4 gap-3'>
        <div className='rounded-lg border border-[#30363d] bg-[#161b22] p-3.5'>
          <div className='text-xs text-[#8b949e]'>Recorded Contracts</div>
          <div className='mt-1 text-xl font-semibold tabular-nums text-[#e6edf3]'>
            {contracts.length}
          </div>
          <div className='text-[11px] text-[#3fb950] mt-0.5'>Agency workspace ledger</div>
        </div>
        <div className='rounded-lg border border-[#30363d] bg-[#161b22] p-3.5'>
          <div className='text-xs text-[#8b949e]'>Active 48h Soft-Holds</div>
          <div className='mt-1 text-xl font-semibold tabular-nums text-[#58a6ff]'>
            {holds.length}
          </div>
          <div className='text-[11px] text-[#8b949e] mt-0.5'>Zero-cost operator holds</div>
        </div>
        <div className='rounded-lg border border-[#30363d] bg-[#161b22] p-3.5'>
          <div className='text-xs text-[#8b949e]'>External Supplier Feed</div>
          <div className='mt-1 text-sm font-semibold text-[#d29922]'>Not Connected</div>
          <div className='text-[11px] text-[#8b949e] mt-1'>DP-04a live feed offline</div>
        </div>
        <div className='rounded-lg border border-[#30363d] bg-[#161b22] p-3.5'>
          <div className='text-xs text-[#8b949e]'>Illustrative Fixtures</div>
          <div className='mt-1 text-xl font-semibold tabular-nums text-[#8b949e]'>
            {SAMPLE_SUPPLIERS.length}
          </div>
          <div className='text-[11px] text-[#8b949e] mt-0.5'>Sample directory only</div>
        </div>
      </div>

      {actionBanner && (
        <div className='rounded-lg border border-[#238636]/50 bg-[#238636]/10 px-4 py-2.5 flex items-center justify-between text-xs text-[#e6edf3]'>
          <span className='flex items-center gap-2'>
            <CheckCircle2 className='size-4 text-[#3fb950] shrink-0' aria-hidden='true' />
            {actionBanner}
          </span>
          <button
            type='button'
            onClick={() => setActionBanner(null)}
            className='text-[#8b949e] hover:text-[#e6edf3]'
            aria-label='Dismiss confirmation'
          >
            <X className='size-3.5' />
          </button>
        </div>
      )}

      {/* Trip Context & Provenance */}
      <div className='space-y-3'>
        <ScopedTripPickerBar
          label='Trip Supplier Context'
          selectId='suppliers-trip-select'
          selectTestId='suppliers-trip-select'
          scope='suppliers'
          scopedLabel='Active Quotes & Bookings'
          allLabel='All Workspace Trips'
          requestedTripId={urlTripId}
          selectedTripId={selectedTripId}
          onSelectTrip={handleSelectTrip}
          searchPlaceholder='Search trip destination or ref…'
          helperText={
            selectedTrip
              ? `Active context: ${formatTripPickerLabel(selectedTrip)}`
              : undefined
          }
        />

        {selectedTrip && (
          <div className='rounded-xl border border-[#30363d] bg-[#161b22] p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4'>
            <div className='grid grid-cols-1 sm:grid-cols-2 gap-4 flex-1'>
              <div>
                <div className='text-xs text-[#8b949e]'>Trip-derived supplier risk</div>
                <div className='mt-1 text-sm font-medium text-[#e6edf3]'>
                  {supplierRiskLevel
                    ? `${supplierRiskLevel} (not supplier-verified)`
                    : 'Unknown (no supplier evidence)'}
                </div>
              </div>
              <div>
                <div className='text-xs text-[#8b949e]'>Snapshot provenance</div>
                <div className='mt-1 text-sm font-medium text-[#e6edf3]'>
                  {supplierSnapshot
                    ? 'stored trip snapshot (freshness unknown)'
                    : 'no stored supplier snapshot'}
                </div>
              </div>
            </div>
            <div className='flex flex-wrap items-center gap-2'>
              <Link
                href={`/trips/${selectedTrip.id}/ops`}
                className='px-3 py-1.5 rounded-md border border-[#30363d] bg-[#21262d] hover:bg-[#30363d] text-xs font-medium text-[#e6edf3] flex items-center gap-1.5'
              >
                <Layers className='size-3.5 text-[#58a6ff]' aria-hidden='true' />
                Open Trip Ops
              </Link>
              <Link
                href={`/quotes?tripId=${selectedTrip.id}`}
                className='px-3 py-1.5 rounded-md border border-[#30363d] bg-[#0d1117] hover:bg-[#21262d] text-xs font-medium text-[#e6edf3]'
              >
                Quotes &amp; Pricing →
              </Link>
            </div>
          </div>
        )}
      </div>

      {/* Section 1: Operator-Recorded Contracts & 48h Soft-Holds */}
      <section
        data-testid='recorded-contracts-section'
        className='rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-5'
      >
        <div className='flex flex-col sm:flex-row sm:items-center justify-between gap-2'>
          <div>
            <h2 className='text-base font-semibold text-[#e6edf3] flex items-center gap-2'>
              <FileSpreadsheet className='size-4 text-[#3fb950]' aria-hidden='true' />
              Operator-Recorded Contracts &amp; 48h Soft-Holds
            </h2>
            <p className='text-xs text-[#8b949e] mt-0.5'>
              Persisted to your agency supplier ledger for net/rack pricing and 48-hour hold tracking.
            </p>
          </div>
          {ledgerError && (
            <span className='text-xs text-[#ff7b72] flex items-center gap-1'>
              <AlertCircle className='size-3.5' aria-hidden='true' />
              {ledgerError}
            </span>
          )}
        </div>

        {ledgerLoading ? (
          <div className='h-20 rounded-lg bg-[#0d1117] animate-pulse' />
        ) : contracts.length === 0 ? (
          <div className='rounded-lg border border-dashed border-[#30363d] bg-[#0d1117] p-6 text-center space-y-2'>
            <p className='text-sm text-[#e6edf3] font-medium'>
              No wholesale rate sheets recorded yet.
            </p>
            <p className='text-xs text-[#8b949e] max-w-xl mx-auto'>
              Record your negotiated DMC or hotel net/rack rate sheets to calculate agency margins
              and issue 48-hour inventory soft-holds for travelers.
            </p>
            <div className='pt-1'>
              <button
                type='button'
                onClick={openUploadModal}
                className='px-3 py-1.5 rounded-md bg-[#21262d] hover:bg-[#30363d] border border-[#30363d] text-xs font-medium text-[#e6edf3]'
              >
                + Record first rate sheet
              </button>
            </div>
          </div>
        ) : (
          <div className='space-y-3'>
            <div className='flex flex-wrap items-center gap-1.5'>
              {SUPPLIER_CATEGORY_FILTERS.map((cat) => (
                <button
                  key={cat.id}
                  type='button'
                  onClick={() => setContractCategory(cat.id)}
                  aria-pressed={contractCategory === cat.id}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                    contractCategory === cat.id
                      ? 'border-[#3fb950] bg-[#238636]/20 text-[#e6edf3]'
                      : 'border-[#30363d] bg-[#0d1117] text-[#8b949e] hover:text-[#e6edf3]'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
            <div className='grid grid-cols-1 md:grid-cols-2 gap-3'>
              {filteredContracts.map((contract) => {
                const catKey = ((contract.supplier_category || 'dmc').toLowerCase() as SupplierCategoryKey);
                const catLabel = SUPPLIER_CATEGORY_LABELS[catKey] ?? contract.supplier_category ?? 'DMC';
                return (
              <div
                key={contract.contract_id}
                className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-3'
              >
                <div className='flex items-start justify-between gap-2'>
                  <div>
                    <div className='flex items-center gap-2 flex-wrap'>
                      <span className='text-sm font-semibold text-[#e6edf3]'>
                        {contract.supplier_name}
                      </span>
                      <span className='px-2 py-0.5 rounded bg-[#21262d] text-[11px] text-[#8b949e]'>
                        {catLabel}
                      </span>
                    </div>
                    <div className='text-xs text-[#8b949e]'>
                      {contract.destination} · {contract.currency}
                      {contract.contact_email ? ` · ${contract.contact_email}` : ''}
                    </div>
                  </div>
                  <button
                    type='button'
                    onClick={() => openHoldModal(contract)}
                    className='px-2.5 py-1 rounded bg-[#1f6feb] hover:bg-[#388bfd] text-white text-xs font-medium shrink-0'
                  >
                    Reserve 48h Hold
                  </button>
                </div>

                <div className='space-y-1.5'>
                  {contract.rate_table.map((rate) => {
                    const margin = rate.rack_rate_per_night - rate.net_rate_per_night;
                    return (
                      <div
                        key={rate.room_type}
                        className='flex items-center justify-between text-xs rounded bg-[#161b22] px-2.5 py-1.5 border border-[#30363d]/60'
                      >
                        <span className='text-[#e6edf3] font-medium'>{rate.room_type}</span>
                        <span className='text-[#8b949e] tabular-nums'>
                          Net {fmtSupplierMoney(rate.net_rate_per_night, contract.currency)} · Rack{' '}
                          {fmtSupplierMoney(rate.rack_rate_per_night, contract.currency)}{' '}
                          <span className='text-[#3fb950]'>
                            (+{fmtSupplierMoney(margin, contract.currency)}/nt)
                          </span>
                        </span>
                      </div>
                    );
                  })}
                </div>

                {contract.terms_and_conditions && (
                  <p className='text-[11px] text-[#8b949e]'>Terms: {contract.terms_and_conditions}</p>
                )}
              </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Recorded 48h Holds Table */}
        {holds.length > 0 && (
          <div className='space-y-2 pt-2'>
            <h3 className='text-xs font-semibold uppercase tracking-wider text-[#8b949e] flex items-center gap-1.5'>
              <CalendarClock className='size-3.5 text-[#58a6ff]' aria-hidden='true' />
              Active 48h Soft-Holds ({holds.length})
            </h3>
            <div className='overflow-x-auto rounded-lg border border-[#30363d]'>
              <table className='w-full text-left border-collapse text-xs'>
                <thead>
                  <tr className='bg-[#0d1117] border-b border-[#30363d] text-[#8b949e] uppercase tracking-wider'>
                    <th className='px-3 py-2 font-medium'>Supplier &amp; Room</th>
                    <th className='px-3 py-2 font-medium'>Guest</th>
                    <th className='px-3 py-2 font-medium'>Stay Window</th>
                    <th className='px-3 py-2 font-medium text-right'>Net Total</th>
                    <th className='px-3 py-2 font-medium text-right'>Est. Margin</th>
                    <th className='px-3 py-2 font-medium'>Expires</th>
                  </tr>
                </thead>
                <tbody className='divide-y divide-[#30363d] bg-[#0d1117]'>
                  {holds.map((hold) => {
                    const curr = contractsById.get(hold.contract_id)?.currency || 'USD';
                    return (
                      <tr key={hold.hold_id}>
                        <td className='px-3 py-2 text-[#e6edf3]'>
                          <div className='font-medium'>{hold.supplier_name}</div>
                          <div className='text-[#8b949e]'>{hold.room_type}</div>
                        </td>
                        <td className='px-3 py-2 text-[#e6edf3]'>{hold.guest_name}</td>
                        <td className='px-3 py-2 text-[#c9d1d9] tabular-nums'>
                          {hold.check_in} → {hold.check_out}
                        </td>
                        <td className='px-3 py-2 text-right tabular-nums text-[#c9d1d9]'>
                          {fmtSupplierMoney(hold.net_rate_total, curr)}
                        </td>
                        <td className='px-3 py-2 text-right tabular-nums text-[#3fb950] font-medium'>
                          +{fmtSupplierMoney(hold.estimated_agency_margin, curr)}
                        </td>
                        <td className='px-3 py-2 text-[#8b949e] whitespace-nowrap'>
                          {fmtShortDateTime(hold.expires_at)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </section>

      {/* Section 2: Illustrative Sample Directory */}
      <section className='rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4'>
        <div
          data-testid='suppliers-preview-banner'
          className='rounded-lg border border-[#d29922]/40 bg-[#d29922]/10 p-3.5 flex items-start gap-2.5 text-xs text-[#e6edf3]'
        >
          <ShieldAlert className='size-4 text-[#e3b341] shrink-0 mt-0.5' aria-hidden='true' />
          <span>
            <strong className='text-[#e3b341]'>Illustrative Directory Reference:</strong> Sample
            supplier entries below are placeholder examples only —{' '}
            <strong>not evidence that a supplier contract exists</strong> or that live DMC allotment
            feeds (DP-04a) are connected. Record real contracts in the ledger above.
          </span>
        </div>

        <div className='flex flex-col lg:flex-row lg:items-center justify-between gap-3'>
          <div className='flex flex-wrap items-center gap-2'>
            <div className='flex flex-wrap items-center gap-1.5'>
              {SUPPLIER_CATEGORY_FILTERS.map((cat) => (
                <button
                  key={cat.id}
                  type='button'
                  onClick={() => setSampleCategory(cat.id)}
                  aria-pressed={sampleCategory === cat.id}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium border transition-colors ${
                    sampleCategory === cat.id
                      ? 'border-[#58a6ff] bg-[#1f6feb]/15 text-[#e6edf3]'
                      : 'border-[#30363d] bg-[#0d1117] text-[#8b949e] hover:text-[#e6edf3]'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
            <span className='text-xs text-[#8b949e] tabular-nums'>
              Showing {filteredSamples.length} sample {filteredSamples.length === 1 ? 'record' : 'records'}
            </span>
          </div>

          <div className='relative w-full lg:w-64'>
            <Search
              className='size-3.5 text-[#8b949e] absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none'
              aria-hidden='true'
            />
            <input
              id={`${baseId}-sample-search`}
              name='sample_supplier_search'
              type='search'
              value={sampleSearch}
              onChange={(e) => setSampleSearch(e.target.value)}
              placeholder='Filter sample directory…'
              aria-label='Filter illustrative sample directory'
              className='w-full bg-[#0d1117] border border-[#30363d] rounded-md pl-8 pr-3 py-1.5 text-xs text-[#e6edf3] placeholder:text-[#8b949e] focus:border-[#58a6ff] outline-none'
            />
          </div>
        </div>

        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3'>
          {filteredSamples.map((fixture) => (
            <div
              key={fixture.id}
              className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-2'
            >
              <div className='flex items-start justify-between gap-2'>
                <div className='text-sm font-medium text-[#e6edf3]'>{fixture.name}</div>
                <span className='px-2 py-0.5 rounded bg-[#21262d] text-[11px] text-[#8b949e] shrink-0'>
                  {SUPPLIER_CATEGORY_LABELS[fixture.category]}
                </span>
              </div>
              <div className='text-xs text-[#8b949e]'>
                {fixture.region} · {fixture.responseSla}
              </div>
              <div className='text-xs text-[#c9d1d9]'>{fixture.settlementTerms}</div>
              <p className='text-[11px] text-[#8b949e] flex items-start gap-1.5 pt-1'>
                <Info className='size-3.5 shrink-0 mt-0.5 text-[#8b949e]' aria-hidden='true' />
                <span>{fixture.notes}</span>
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Modal: Upload Rate Sheet */}
      {uploadOpen && (
        <div
          data-testid='upload-contract-modal'
          role='dialog'
          aria-modal='true'
          aria-labelledby={`${baseId}-upload-title`}
          className='fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4'
        >
          <div className='w-full max-w-2xl rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4 max-h-[90vh] overflow-y-auto'>
            <div className='flex items-center justify-between'>
              <h2 id={`${baseId}-upload-title`} className='text-base font-semibold text-[#e6edf3]'>
                Record Supplier Rate Sheet
              </h2>
              <button
                type='button'
                onClick={() => setUploadOpen(false)}
                className='text-[#8b949e] hover:text-[#e6edf3]'
                aria-label='Close rate sheet dialog'
              >
                <X className='size-4' />
              </button>
            </div>

            <form onSubmit={(e) => void handleUploadSubmit(e)} className='space-y-4'>
              <div className='grid grid-cols-1 sm:grid-cols-2 gap-3'>
                <div>
                  <label htmlFor={`${baseId}-sup-name`} className='block text-xs text-[#8b949e] mb-1'>
                    Supplier / DMC name
                  </label>
                  <input
                    id={`${baseId}-sup-name`}
                    name='supplier_name'
                    required
                    value={supplierName}
                    onChange={(e) => setSupplierName(e.target.value)}
                    placeholder='e.g. Kyoto Heritage DMC'
                    className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                  />
                </div>
                <div>
                  <label htmlFor={`${baseId}-sup-dest`} className='block text-xs text-[#8b949e] mb-1'>
                    Destination
                  </label>
                  <input
                    id={`${baseId}-sup-dest`}
                    name='destination'
                    required
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                    placeholder='e.g. Kyoto, Japan'
                    className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                  />
                </div>
                <div>
                  <label htmlFor={`${baseId}-sup-category`} className='block text-xs text-[#8b949e] mb-1'>
                    Supplier category
                  </label>
                  <select
                    id={`${baseId}-sup-category`}
                    name='supplier_category'
                    value={supplierCategory}
                    onChange={(e) => setSupplierCategory(e.target.value as SupplierCategoryKey)}
                    className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                  >
                    {(Object.entries(SUPPLIER_CATEGORY_LABELS) as Array<[SupplierCategoryKey, string]>).map(
                      ([key, label]) => (
                        <option key={key} value={key}>
                          {label}
                        </option>
                      )
                    )}
                  </select>
                </div>
                <div>
                  <label htmlFor={`${baseId}-sup-email`} className='block text-xs text-[#8b949e] mb-1'>
                    Contract desk email (optional)
                  </label>
                  <input
                    id={`${baseId}-sup-email`}
                    name='contact_email'
                    type='email'
                    value={contactEmail}
                    onChange={(e) => setContactEmail(e.target.value)}
                    placeholder='reservations@partner.example'
                    className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                  />
                </div>
                <div>
                  <label htmlFor={`${baseId}-sup-curr`} className='block text-xs text-[#8b949e] mb-1'>
                    Contract currency
                  </label>
                  <select
                    id={`${baseId}-sup-curr`}
                    name='currency'
                    value={currency}
                    onChange={(e) => setCurrency(e.target.value)}
                    className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                  >
                    <option value='INR'>INR</option>
                    <option value='USD'>USD</option>
                    <option value='EUR'>EUR</option>
                    <option value='GBP'>GBP</option>
                  </select>
                </div>
              </div>

              <div className='space-y-2'>
                <div className='flex items-center justify-between'>
                  <span className='text-xs font-medium text-[#e6edf3]'>Room &amp; Rate Tiers</span>
                  <button
                    type='button'
                    onClick={() =>
                      setRateRows((prev) => [
                        ...prev,
                        {
                          room_type: '',
                          net_rate_per_night: 15000,
                          rack_rate_per_night: 20000,
                          cancellation_lead_days: 7,
                        },
                      ])
                    }
                    className='text-xs text-[#58a6ff] hover:underline flex items-center gap-1'
                  >
                    <Plus className='size-3.5' /> Add tier
                  </button>
                </div>

                {rateRows.map((row, idx) => (
                  <div
                    key={idx}
                    className='grid grid-cols-12 gap-2 items-center bg-[#0d1117] p-2 rounded-md border border-[#30363d]'
                  >
                    <input
                      aria-label={`Room tier ${idx + 1}`}
                      value={row.room_type}
                      onChange={(e) =>
                        setRateRows((prev) =>
                          prev.map((item, i) => (i === idx ? { ...item, room_type: e.target.value } : item))
                        )
                      }
                      placeholder='Room type'
                      className='col-span-5 bg-[#161b22] border border-[#30363d] rounded px-2 py-1.5 text-xs text-[#e6edf3]'
                    />
                    <input
                      aria-label={`Net rate ${idx + 1}`}
                      type='number'
                      min='1'
                      value={row.net_rate_per_night}
                      onChange={(e) =>
                        setRateRows((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, net_rate_per_night: Number(e.target.value) || 0 } : item
                          )
                        )
                      }
                      placeholder='Net / nt'
                      className='col-span-3 bg-[#161b22] border border-[#30363d] rounded px-2 py-1.5 text-xs text-[#e6edf3]'
                    />
                    <input
                      aria-label={`Rack rate ${idx + 1}`}
                      type='number'
                      min='1'
                      value={row.rack_rate_per_night}
                      onChange={(e) =>
                        setRateRows((prev) =>
                          prev.map((item, i) =>
                            i === idx ? { ...item, rack_rate_per_night: Number(e.target.value) || 0 } : item
                          )
                        )
                      }
                      placeholder='Rack / nt'
                      className='col-span-3 bg-[#161b22] border border-[#30363d] rounded px-2 py-1.5 text-xs text-[#e6edf3]'
                    />
                    <button
                      type='button'
                      disabled={rateRows.length <= 1}
                      onClick={() => setRateRows((prev) => prev.filter((_, i) => i !== idx))}
                      aria-label={`Remove tier ${idx + 1}`}
                      className='col-span-1 flex justify-center text-[#8b949e] hover:text-[#ff7b72] disabled:opacity-30'
                    >
                      <Trash2 className='size-3.5' />
                    </button>
                  </div>
                ))}
              </div>

              <div>
                <label htmlFor={`${baseId}-sup-terms`} className='block text-xs text-[#8b949e] mb-1'>
                  Cancellation &amp; payment terms (optional)
                </label>
                <input
                  id={`${baseId}-sup-terms`}
                  name='terms_and_conditions'
                  value={termsText}
                  onChange={(e) => setTermsText(e.target.value)}
                  placeholder='e.g. Free cancellation up to 14 days prior; 20% deposit on confirmation'
                  className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                />
              </div>

              {uploadError && <p className='text-xs text-[#ff7b72]'>{uploadError}</p>}

              <div className='flex items-center justify-end gap-2 pt-2'>
                <button
                  type='button'
                  onClick={() => setUploadOpen(false)}
                  className='px-3 py-1.5 rounded-md border border-[#30363d] bg-[#21262d] text-xs text-[#e6edf3]'
                >
                  Cancel
                </button>
                <button
                  type='submit'
                  disabled={uploadSubmitting}
                  className='px-4 py-1.5 rounded-md bg-[#238636] hover:bg-[#2ea043] text-xs font-semibold text-white disabled:opacity-50'
                >
                  {uploadSubmitting ? 'Saving…' : 'Save Rate Sheet'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal: Reserve 48h Soft-Hold */}
      {holdContract && (
        <div
          data-testid='soft-hold-modal'
          role='dialog'
          aria-modal='true'
          aria-labelledby={`${baseId}-hold-title`}
          className='fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4'
        >
          <div className='w-full max-w-md rounded-xl border border-[#30363d] bg-[#161b22] p-5 space-y-4'>
            <div className='flex items-center justify-between'>
              <h2 id={`${baseId}-hold-title`} className='text-base font-semibold text-[#e6edf3]'>
                Reserve 48h Soft-Hold · {holdContract.supplier_name}
              </h2>
              <button
                type='button'
                onClick={() => setHoldContract(null)}
                className='text-[#8b949e] hover:text-[#e6edf3]'
                aria-label='Close soft-hold dialog'
              >
                <X className='size-4' />
              </button>
            </div>

            <form onSubmit={(e) => void handleSoftHoldSubmit(e)} className='space-y-3'>
              <div>
                <label htmlFor={`${baseId}-hold-room`} className='block text-xs text-[#8b949e] mb-1'>
                  Room tier
                </label>
                <select
                  id={`${baseId}-hold-room`}
                  name='room_type'
                  value={holdRoomType}
                  onChange={(e) => setHoldRoomType(e.target.value)}
                  className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                >
                  {holdContract.rate_table.map((rate) => (
                    <option key={rate.room_type} value={rate.room_type}>
                      {rate.room_type} (Net {fmtSupplierMoney(rate.net_rate_per_night, holdContract.currency)}/nt)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor={`${baseId}-hold-guest`} className='block text-xs text-[#8b949e] mb-1'>
                  Lead traveler name
                </label>
                <input
                  id={`${baseId}-hold-guest`}
                  name='guest_name'
                  required
                  value={holdGuestName}
                  onChange={(e) => setHoldGuestName(e.target.value)}
                  placeholder='e.g. Aarav Mehta'
                  className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                />
              </div>

              <div className='grid grid-cols-2 gap-3'>
                <div>
                  <label htmlFor={`${baseId}-hold-in`} className='block text-xs text-[#8b949e] mb-1'>
                    Check-in
                  </label>
                  <input
                    id={`${baseId}-hold-in`}
                    name='check_in'
                    type='date'
                    required
                    value={holdCheckIn}
                    onChange={(e) => setHoldCheckIn(e.target.value)}
                    className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                  />
                </div>
                <div>
                  <label htmlFor={`${baseId}-hold-out`} className='block text-xs text-[#8b949e] mb-1'>
                    Check-out
                  </label>
                  <input
                    id={`${baseId}-hold-out`}
                    name='check_out'
                    type='date'
                    required
                    value={holdCheckOut}
                    onChange={(e) => setHoldCheckOut(e.target.value)}
                    className='w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2 text-sm text-[#e6edf3]'
                  />
                </div>
              </div>

              {holdError && <p className='text-xs text-[#ff7b72]'>{holdError}</p>}

              <div className='flex items-center justify-end gap-2 pt-2'>
                <button
                  type='button'
                  onClick={() => setHoldContract(null)}
                  className='px-3 py-1.5 rounded-md border border-[#30363d] bg-[#21262d] text-xs text-[#e6edf3]'
                >
                  Cancel
                </button>
                <button
                  type='submit'
                  disabled={holdSubmitting}
                  className='px-4 py-1.5 rounded-md bg-[#1f6feb] hover:bg-[#388bfd] text-xs font-semibold text-white disabled:opacity-50'
                >
                  {holdSubmitting ? 'Reserving…' : 'Confirm 48h Soft-Hold'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
