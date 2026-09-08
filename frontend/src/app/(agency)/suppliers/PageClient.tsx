'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import { useTrip, useTrips } from '@/hooks/useTrips';
import { formatTripPickerLabel } from '@/lib/trip-picker-label';
import {
  Briefcase,
  Search,
  Building2,
  Plane,
  Car,
  Shield,
  Star,
  Clock,
  Plus,
  FileSpreadsheet,
} from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

interface SupplierPartner {
  id: string;
  name: string;
  category: 'dmc' | 'hotel' | 'airline' | 'transport' | 'insurance';
  destinations: string[];
  commissionTier: string;
  paymentTerms: string;
  slaScore: number;
  softHoldSupported: boolean;
  contactEmail: string;
  rating: number;
  activeRateSheets: number;
  evidenceStatus: 'sample';
}

export default function SuppliersPage() {
  const { data: trips, isLoading } = useTrips({ view: 'workspace', limit: 100 });
  const [selectedTripId, setSelectedTripId] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);

  const tripOptions = useMemo(
    () => trips.map((trip) => ({ id: trip.id, label: formatTripPickerLabel(trip) })),
    [trips],
  );
  const selectedTripExists = trips.some((trip) => trip.id === selectedTripId);
  const effectiveSelectedTripId = selectedTripExists ? selectedTripId : trips[0]?.id ?? '';
  const { data: selectedTrip } = useTrip(effectiveSelectedTripId || null);

  const supplierRiskLevel = selectedTrip?.agentOperations?.supplierRiskLevel ?? null;
  const supplierSnapshot = selectedTrip?.agentOperations?.supplierIntelligenceSnapshot ?? null;

  const suppliersList: SupplierPartner[] = useMemo(() => {
    return [
      {
        id: 'sup_01',
        name: 'Wilderness Safaris DMC',
        category: 'dmc',
        destinations: ['South Africa', 'Botswana', 'Namibia', 'Zimbabwe'],
        commissionTier: '18% Net Wholesale Markup',
        paymentTerms: 'Net 30 Days (48h Soft-Hold)',
        slaScore: 99.2,
        softHoldSupported: true,
        contactEmail: 'ops@example.invalid',
        rating: 4.95,
        activeRateSheets: 4,
        evidenceStatus: 'sample',
      },
      {
        id: 'sup_02',
        name: 'The Royal Portfolio Luxury Collection',
        category: 'hotel',
        destinations: ['Cape Town', 'Franschhoek', 'Kruger National Park'],
        commissionTier: '15% Preferred Direct Commission',
        paymentTerms: 'Pre-paid 14 days before check-in',
        slaScore: 98.8,
        softHoldSupported: true,
        contactEmail: 'reservations@example.invalid',
        rating: 4.98,
        activeRateSheets: 2,
        evidenceStatus: 'sample',
      },
      {
        id: 'sup_03',
        name: 'Singapore DMC & Sentosa Experiences',
        category: 'dmc',
        destinations: ['Singapore', 'Malaysia', 'Bintan'],
        commissionTier: '14% Wholesale Net Contract',
        paymentTerms: 'Instant Confirmation / Net 15',
        slaScore: 97.9,
        softHoldSupported: true,
        contactEmail: 'b2b@example.invalid',
        rating: 4.88,
        activeRateSheets: 6,
        evidenceStatus: 'sample',
      },
      {
        id: 'sup_04',
        name: 'Emirates Airlines B2B Partner Portal',
        category: 'airline',
        destinations: ['Global Routes via Dubai Hub'],
        commissionTier: 'Standard IATA + Incentive Override',
        paymentTerms: 'BSP / GDS Instant Ticketing',
        slaScore: 99.5,
        softHoldSupported: false,
        contactEmail: 'trade-support@example.invalid',
        rating: 4.9,
        activeRateSheets: 1,
        evidenceStatus: 'sample',
      },
      {
        id: 'sup_05',
        name: 'Cape Executive VIP Logistics & Chauffeur',
        category: 'transport',
        destinations: ['Western Cape', 'Garden Route'],
        commissionTier: '12% Net Margin Protection',
        paymentTerms: 'Net 15 Days',
        slaScore: 99.0,
        softHoldSupported: true,
        contactEmail: 'dispatch@example.invalid',
        rating: 4.92,
        activeRateSheets: 2,
        evidenceStatus: 'sample',
      },
      {
        id: 'sup_06',
        name: 'Allianz Global Assistance Luxury Travel Care',
        category: 'insurance',
        destinations: ['Worldwide Comprehensive Cover'],
        commissionTier: '25% Policy Issuance Commission',
        paymentTerms: 'Monthly Commission Remittance',
        slaScore: 98.4,
        softHoldSupported: false,
        contactEmail: 'agency-support@example.invalid',
        rating: 4.85,
        activeRateSheets: 3,
        evidenceStatus: 'sample',
      },
    ];
  }, []);

  const filteredSuppliers = useMemo(() => {
    return suppliersList.filter((s) => {
      const matchesCategory = selectedCategory === 'all' || s.category === selectedCategory;
      const matchesSearch =
        s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        s.destinations.some((d) => d.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCategory && matchesSearch;
    });
  }, [suppliersList, selectedCategory, searchQuery]);

  const renderCategoryIcon = (category: SupplierPartner['category']) => {
    switch (category) {
      case 'dmc':
        return <Briefcase className='size-4 text-[#58a6ff]' />;
      case 'hotel':
        return <Building2 className='size-4 text-[#3fb950]' />;
      case 'airline':
        return <Plane className='size-4 text-[#58a6ff]' />;
      case 'transport':
        return <Car className='size-4 text-[#d29922]' />;
      case 'insurance':
        return <Shield className='size-4 text-[#a371f7]' />;
      default:
        return <Briefcase className='size-4 text-[#58a6ff]' />;
    }
  };

  return (
    <div className='p-6 space-y-6'>
      <BackToOverviewLink />

      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <Briefcase className='size-6 text-[#58a6ff]' />
            Suppliers & DMC Directory
            <SimulatedBadge label='Sample data' />
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Illustrative supplier records and workflow previews. No live supplier directory, rate feed, SLA monitor, inventory hold, or provider confirmation is connected.
          </p>
        </div>

        <button
          type='button'
          onClick={() => setIsUploadModalOpen(true)}
          className='px-3.5 py-2 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm self-start md:self-auto'
        >
          <Plus className='size-3.5' />
          Preview Rate-Sheet Intake
        </button>
      </div>

      <div
        data-testid='suppliers-preview-banner'
        role='note'
        className='rounded-lg border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100'
      >
        <div className='font-semibold'>Local preview only</div>
        <p className='mt-1 text-xs leading-5 text-amber-100/80'>
          The records, commercial terms, scores, and destinations below are sample fixtures for interface review. They are not evidence that a supplier contract exists, a rate sheet is current, an SLA was measured, or inventory is available.
        </p>
      </div>

      {/* Trip Context & Intelligence Banner */}
      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <div className='flex flex-col md:flex-row md:items-center justify-between gap-3'>
          <div className='space-y-1'>
            <label htmlFor='suppliers-trip-select' className='block text-xs font-medium text-[#8b949e] uppercase tracking-wider'>
              Trip context (local preview only)
            </label>
            <select
              id='suppliers-trip-select'
              data-testid='suppliers-trip-select'
              value={effectiveSelectedTripId}
              onChange={(e) => setSelectedTripId(e.target.value)}
              className='w-full md:w-[460px] bg-[#161b22] border border-[#30363d] rounded-md p-2 text-sm text-[#e6edf3] focus:border-[#58a6ff] outline-none'
              disabled={isLoading || tripOptions.length === 0}
            >
              {tripOptions.length === 0 ? (
                <option value=''>No trips in planning</option>
              ) : (
                tripOptions.map((trip) => (
                  <option key={trip.id} value={trip.id}>
                    {trip.label}
                  </option>
                ))
              )}
            </select>
          </div>

          {effectiveSelectedTripId && (
            <div className='flex items-center gap-3 text-xs bg-[#161b22] px-3 py-2 rounded-md border border-[#30363d]'>
              <div className='text-[#8b949e]'>
                Trip-derived risk: <span className='text-[#d29922] font-medium'>{supplierRiskLevel ? `${supplierRiskLevel} (not supplier-verified)` : 'Unknown (no supplier evidence)'}</span>
              </div>
              <div className='w-px h-4 bg-[#30363d]' />
              <div className='text-[#8b949e]'>
                Snapshot: <span className='text-[#58a6ff] font-medium'>{supplierSnapshot ? 'stored trip snapshot (freshness unknown)' : 'no stored supplier snapshot'}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className='grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4'>
        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Illustrative Partner Records</span>
            <Briefcase className='size-4 text-[#58a6ff]' />
          </div>
          <div className='text-2xl font-bold text-[#e6edf3]'>{suppliersList.length} Sample Records</div>
          <div className='text-xs text-[#8b949e]'>DMCs, hotels, airlines, transfers, and insurance fixtures</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Illustrative Rate Sheets</span>
            <FileSpreadsheet className='size-4 text-[#3fb950]' />
          </div>
          <div className='text-2xl font-bold text-[#3fb950]'>18 Sample Rows</div>
          <div className='text-xs text-[#8b949e]'>No contract has been uploaded or persisted</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Sample SLA Score</span>
            <Star className='size-4 text-[#d29922]' />
          </div>
          <div className='text-2xl font-bold text-[#d29922]'>98.8% Fixture</div>
          <div className='text-xs text-[#8b949e]'>Not measured or monitored live</div>
        </div>

        <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-4 space-y-1.5'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider flex items-center justify-between'>
            <span>Soft-Hold Capability Preview</span>
            <Clock className='size-4 text-[#a371f7]' />
          </div>
          <div className='text-2xl font-bold text-[#a371f7]'>Not Connected</div>
          <div className='text-xs text-[#8b949e]'>No inventory hold has been reserved</div>
        </div>
      </div>

      {/* Search & Category Filter Bar */}
      <div className='flex flex-col sm:flex-row gap-3 items-center justify-between'>
        <div className='relative w-full sm:w-80'>
          <Search className='absolute left-3 top-2.5 size-4 text-[#8b949e]' />
          <input
            type='text'
            placeholder='Search by supplier or destination…'
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className='w-full pl-9 pr-3 py-2 bg-[#161b22] border border-[#30363d] rounded-md text-sm text-[#e6edf3] placeholder-[#8b949e] focus:border-[#58a6ff] outline-none'
          />
        </div>

        <div className='flex flex-wrap gap-1.5 w-full sm:w-auto'>
          {[
            { id: 'all', label: 'All Categories' },
            { id: 'dmc', label: 'DMCs & Inbound' },
            { id: 'hotel', label: 'Hotels & Resorts' },
            { id: 'airline', label: 'Airlines' },
            { id: 'transport', label: 'Transfers' },
            { id: 'insurance', label: 'Insurance' },
          ].map((cat) => (
            <button
              key={cat.id}
              type='button'
              onClick={() => setSelectedCategory(cat.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                selectedCategory === cat.id
                  ? 'bg-[#1f6feb] text-white'
                  : 'bg-[#161b22] text-[#8b949e] hover:text-[#e6edf3] border border-[#30363d]'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Supplier Directory Table */}
      <div className='rounded-lg border border-[#30363d] bg-[#0d1117] overflow-hidden'>
        <div className='p-4 border-b border-[#30363d] flex items-center justify-between bg-[#161b22]'>
          <div className='flex items-center gap-2 font-semibold text-sm text-[#e6edf3]'>
            <Briefcase className='size-4 text-[#58a6ff]' />
            <span>Illustrative Supplier Records</span>
          </div>
          <span className='text-xs text-[#8b949e]'>Showing {filteredSuppliers.length} sample records</span>
        </div>

        <div className='overflow-x-auto'>
          <table className='w-full text-left text-sm'>
            <thead>
              <tr className='border-b border-[#30363d] bg-[#0d1117] text-xs font-semibold text-[#8b949e] uppercase tracking-wider'>
                <th className='p-3.5'>Partner & Category</th>
                <th className='p-3.5'>Destination Coverage</th>
                <th className='p-3.5'>Illustrative Commission / Markup</th>
                <th className='p-3.5'>Illustrative Payment Terms</th>
                <th className='p-3.5'>Illustrative Score</th>
                <th className='p-3.5 text-right'>Action</th>
              </tr>
            </thead>
            <tbody className='divide-y divide-[#30363d]'>
              {filteredSuppliers.map((supplier) => (
                <tr key={supplier.id} className='hover:bg-[#161b22] transition-colors'>
                  <td className='p-3.5'>
                    <div className='flex items-center gap-2.5'>
                      <div className='p-2 bg-[#161b22] rounded border border-[#30363d]'>
                        {renderCategoryIcon(supplier.category)}
                      </div>
                      <div>
                        <div className='font-medium text-[#e6edf3]'>{supplier.name}</div>
                        <div className='text-xs text-[#8b949e] capitalize'>{supplier.category} · {supplier.evidenceStatus} record</div>
                      </div>
                    </div>
                  </td>

                  <td className='p-3.5'>
                    <div className='flex flex-wrap gap-1 max-w-xs'>
                      {supplier.destinations.map((d, i) => (
                        <span
                          key={i}
                          className='px-1.5 py-0.5 text-[11px] bg-[#161b22] border border-[#30363d] text-[#c9d1d9] rounded'
                        >
                          {d}
                        </span>
                      ))}
                    </div>
                  </td>

                  <td className='p-3.5 font-mono text-xs font-semibold text-[#3fb950]'>
                    Fixture: {supplier.commissionTier}
                  </td>

                  <td className='p-3.5 text-xs text-[#8b949e]'>
                    <div className='flex items-center gap-1.5'>
                      <span>Fixture: {supplier.paymentTerms}</span>
                      {supplier.softHoldSupported && (
                        <span className='px-1.5 py-0.2 text-[10px] bg-[#238636]/20 text-[#3fb950] rounded border border-[#238636]/40'>
                          Sample hold terms
                        </span>
                      )}
                    </div>
                  </td>

                  <td className='p-3.5'>
                    <div className='flex items-center gap-1.5 font-mono text-xs font-semibold text-[#58a6ff]'>
                      <Clock className='size-3.5 text-[#d29922]' />
                      <span>{supplier.slaScore}% (demo)</span>
                    </div>
                    <div className='text-[11px] text-[#8b949e]'>Sample score · rating (demo) {supplier.rating}/5.0</div>
                  </td>

                  <td className='p-3.5 text-right'>
                    <span className='text-xs text-[#8b949e]' title='Provider contact is unavailable in local preview'>
                      Contact unavailable in preview
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Rate Sheet Modal */}
      {isUploadModalOpen && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4'>
          <div
            role='dialog'
            aria-modal='true'
            aria-labelledby='supplier-rate-sheet-preview-title'
            className='w-full max-w-lg bg-[#0d1117] border border-[#30363d] rounded-lg shadow-xl p-6 space-y-4'
          >
            <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
              <div className='flex items-center gap-2 font-semibold text-base text-[#e6edf3]'>
                <FileSpreadsheet className='size-5 text-[#3fb950]' />
                <span id='supplier-rate-sheet-preview-title'>Preview Rate-Sheet Intake</span>
              </div>
              <button
                type='button'
                onClick={() => setIsUploadModalOpen(false)}
                className='text-[#8b949e] hover:text-[#e6edf3] text-sm'
              >
                ✕
              </button>
            </div>

            <div className='space-y-3 text-xs text-[#c9d1d9]'>
              <div className='rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-amber-100'>
                This is a local form preview. No file is uploaded, no contract is persisted, and no supplier is contacted.
              </div>
              <div>
                <label htmlFor='supplier-preview-name' className='block text-[#8b949e] mb-1 font-medium'>Supplier / DMC Company Name</label>
                <input
                  id='supplier-preview-name'
                  type='text'
                  placeholder='e.g., Wilderness Safaris Botswana'
                  className='w-full p-2 bg-[#161b22] border border-[#30363d] rounded text-sm text-[#e6edf3] outline-none focus:border-[#58a6ff]'
                />
              </div>

              <div>
                <label htmlFor='supplier-preview-destination' className='block text-[#8b949e] mb-1 font-medium'>Destination / Region Covered</label>
                <input
                  id='supplier-preview-destination'
                  type='text'
                  placeholder='e.g., Okavango Delta, Botswana'
                  className='w-full p-2 bg-[#161b22] border border-[#30363d] rounded text-sm text-[#e6edf3] outline-none focus:border-[#58a6ff]'
                />
              </div>

              <div className='p-4 border-2 border-dashed border-[#30363d] rounded-lg bg-[#161b22] text-center space-y-2'>
                <FileSpreadsheet className='size-8 text-[#58a6ff] mx-auto' />
                <div className='text-sm font-medium text-[#e6edf3]'>Drag and drop Excel or CSV rate sheet</div>
                <div className='text-[11px] text-[#8b949e]'>Supports .xlsx, .csv rate cards with net/rack columns</div>
              </div>
            </div>

            <div className='flex justify-end gap-2 pt-2 border-t border-[#30363d]'>
              <button
                type='button'
                onClick={() => setIsUploadModalOpen(false)}
                className='px-3.5 py-1.5 bg-[#21262d] text-[#e6edf3] rounded text-xs hover:bg-[#30363d] border border-[#30363d]'
              >
                Cancel
              </button>
              <button
                type='button'
                onClick={() => setIsUploadModalOpen(false)}
                className='px-3.5 py-1.5 bg-[#238636] text-white rounded text-xs font-semibold hover:bg-[#2ea043]'
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
