'use client';

import React, { useEffect, useState, useMemo } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  CheckCircle2,
  ShieldCheck,
  Clock,
  Award,
  ChevronRight,
  Sparkles,
  MapPin,
  Calendar,
  Users,
  DollarSign,
  Loader2,
  AlertTriangle,
  Plane,
  Building2,
  Car,
  Compass,
  Check,
  Download,
  Share2,
  Plus,
} from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

interface ItineraryDay {
  day: number;
  title: string;
  location: string;
  summary: string;
  hotel: string;
  inclusions: string[];
}

interface ProposalAddOn {
  id: string;
  title: string;
  price: number;
  duration: string;
  description: string;
  selected: boolean;
}

export default function InteractiveProposalPage() {
  const routeParams = useParams();
  const proposalId = (routeParams?.proposalId as string) || 'proposal_demo';
  const [loading, setLoading] = useState(true);
  const [accepted, setAccepted] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [activeTier, setActiveTier] = useState<'saver' | 'curated' | 'prestige'>('curated');
  const [copied, setCopied] = useState(false);

  const [addOns, setAddOns] = useState<ProposalAddOn[]>([
    {
      id: 'add_01',
      title: 'Table Mountain Private Helicopter & Vineyard Landing',
      price: 620,
      duration: '4 Hours',
      description: 'Scenic aerial flight over Cape Peninsula with champagne landing at Delaire Graff.',
      selected: false,
    },
    {
      id: 'add_02',
      title: 'Private Sommelier Wine Tasting & Cellar Tour in Franschhoek',
      price: 240,
      duration: '3 Hours',
      description: 'Exclusive barrel tasting with master winemaker and artisan cheese pairings.',
      selected: false,
    },
    {
      id: 'add_03',
      title: 'VIP Fast-Track Airport Immigrations & Lounge Escort',
      price: 180,
      duration: 'Arrival & Departure',
      description: 'Dedicated tarmac greeting, expedited customs clearance, and business lounge access.',
      selected: true,
    },
  ]);

  const itineraryDays: ItineraryDay[] = useMemo(() => {
    return [
      {
        day: 1,
        title: 'Arrival in Cape Town & Waterfront Sunset Welcome',
        location: 'Cape Town, South Africa',
        summary: 'Private VIP airport reception and chauffeur transfer to Victoria & Alfred Waterfront. Evening champagne reception overlooking Table Mountain.',
        hotel: activeTier === 'prestige' ? 'The Silo Hotel (Deluxe Harbour Suite)' : 'The Victoria & Alfred Hotel Luxury Suite',
        inclusions: ['Private Chauffeur Airport Transfer', 'VIP Hotel Welcome Amenities', 'Sunset Welcome Dinner'],
      },
      {
        day: 2,
        title: 'Table Mountain Cableway & Historic City Curator Walk',
        location: 'Cape Town City Center',
        summary: 'Fast-track morning ascent of Table Mountain followed by a private art and architectural walking tour of Bo-Kaap and Company Gardens.',
        hotel: activeTier === 'prestige' ? 'The Silo Hotel (Deluxe Harbour Suite)' : 'The Victoria & Alfred Hotel Luxury Suite',
        inclusions: ['Skip-the-Line Cableway Tickets', 'Private Cultural Historian Guide', 'Curated Chef Lunch at Kloof Street House'],
      },
      {
        day: 3,
        title: 'Cape Point Peninsula & Boulders Beach Penguin Colony',
        location: 'Cape Peninsula & Simon’s Town',
        summary: 'Coastal drive along Chapman’s Peak, private boat cruise to Seal Island, and intimate boardwalk viewing of African penguins.',
        hotel: activeTier === 'prestige' ? 'The Silo Hotel (Deluxe Harbour Suite)' : 'The Victoria & Alfred Hotel Luxury Suite',
        inclusions: ['Private Mercedes-Benz V-Class Throughout', 'Cape Point Reserve Access & Funicular', 'Private Seafood Lunch at Harbour House'],
      },
      {
        day: 4,
        title: 'Private Transfer to Franschhoek Wine Valley',
        location: 'Cape Winelands',
        summary: 'Scenic morning drive into the Franschhoek Valley. Check-in to luxury vineyard estate and afternoon private tasting.',
        hotel: activeTier === 'prestige' ? 'La Residence Vineyard Suite' : 'Mont Rochelle Franschhoek Estate',
        inclusions: ['Private Chauffeur Transfer', 'Vineyard Cellar Master Tour', 'Gourmet 5-Course Dinner with Wine Pairings'],
      },
      {
        day: 5,
        title: 'Exclusive Wildlife Safari Charter Transfer',
        location: 'Kruger National Park / Sabi Sand',
        summary: 'Federal Air charter flight directly to private safari reserve runway. Afternoon open-vehicle leopard and elephant tracking game drive.',
        hotel: activeTier === 'prestige' ? 'Singita Boulders Luxury Lodge' : 'Lion Sands River Lodge Suite',
        inclusions: ['Charter Flight Direct to Lodge Runway', 'All-Inclusive Luxury Dining & Premium Spirits', 'Sunset Safari Drive with Sundowner Cocktails'],
      },
    ];
  }, [activeTier]);

  const basePrices = {
    saver: 3800,
    curated: 4850,
    prestige: 7600,
  };

  const selectedAddOnsTotal = useMemo(() => {
    return addOns.filter((a) => a.selected).reduce((sum, a) => sum + a.price, 0);
  }, [addOns]);

  const grandTotal = basePrices[activeTier] + selectedAddOnsTotal;

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [proposalId]);

  const handleToggleAddOn = (id: string) => {
    setAddOns((prev) =>
      prev.map((a) => (a.id === id ? { ...a, selected: !a.selected } : a))
    );
  };

  const handleCopyLink = () => {
    navigator.clipboard?.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleAccept = async () => {
    setAccepting(true);
    setTimeout(() => {
      setAccepted(true);
      setAccepting(false);
    }, 600);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0d1117] text-[#e6edf3] flex items-center justify-center p-6">
        <div className="flex items-center gap-3 text-sm text-[#8b949e]">
          <Loader2 className="w-5 h-5 animate-spin text-[#58a6ff]" />
          <span>Loading sample proposal preview...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0d1117] text-[#e6edf3] font-sans pb-20">
      {/* Sticky Traveler Navigation Bar */}
      <header className="border-b border-[#30363d] bg-[#161b22]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#1f6feb] flex items-center justify-center font-bold text-white shadow-md">
              W
            </div>
            <div>
              <span className="font-bold text-sm text-[#e6edf3]">Waypoint Agency</span>
              <span className="text-[10px] text-[#8b949e] block">Bespoke Travel Proposal</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleCopyLink}
              className="hidden sm:flex items-center gap-1.5 text-xs text-[#8b949e] hover:text-[#e6edf3] bg-[#0d1117] border border-[#30363d] px-3 py-1.5 rounded-md transition-colors"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#3fb950]" /> : <Share2 className="w-3.5 h-3.5" />}
              <span>{copied ? 'Link Copied' : 'Share'}</span>
            </button>

            <div className="flex items-center gap-2 text-xs text-[#8b949e] bg-[#30363d]/30 border border-[#30363d] px-3 py-1.5 rounded-full font-medium">
              <Clock className="w-3.5 h-3.5" />
              <span>Illustrative pricing · no hold active</span>
            </div>
          </div>
        </div>
      </header>

      <section
        aria-label="Sample proposal notice"
        className="max-w-5xl mx-auto mt-6 px-6"
      >
        <div className="flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3">
          <SimulatedBadge label="Sample proposal" />
          <div className="text-xs text-[#f0e6c8] leading-relaxed">
            <p className="font-semibold">Demonstration itinerary — not a supplier-backed booking</p>
            <p className="text-[#d8cda9]">
              This page is a local fixture for proposal review. Supplier availability, DMC verification,
              pricing holds, bookings, and acceptance are not connected to an external system.
            </p>
          </div>
        </div>
      </section>

      {/* Main Container */}
      <main className="max-w-5xl mx-auto px-6 pt-8 space-y-8">
        {/* Hero Banner */}
        <section className="relative overflow-hidden bg-gradient-to-br from-[#161b22] via-[#0d1117] to-[#161b22] border border-[#30363d] rounded-2xl p-8 shadow-xl">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#58a6ff] uppercase tracking-widest mb-3">
            <Sparkles className="w-4 h-4 text-[#d29922]" />
            <span>Curated Luxury Itinerary Proposal</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-[#e6edf3] tracking-tight mb-3">
            South Africa: Cape Town, Winelands & Private Safari
          </h1>

          <p className="text-[#8b949e] text-sm max-w-2xl leading-relaxed">
            Illustrative November 2026 journey with proposed 5-star suite accommodation, private vehicle logistics, and bush safari charter options. All details require supplier confirmation.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-8 pt-6 border-t border-[#30363d] text-xs">
            <div className="flex items-center gap-2.5 text-[#c9d1d9]">
              <MapPin className="w-4 h-4 text-[#58a6ff]" />
              <div>
                <span className="text-[#8b949e] block text-[10px]">Destination</span>
                <span className="font-semibold text-[#e6edf3]">Cape Town & Kruger</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 text-[#c9d1d9]">
              <Calendar className="w-4 h-4 text-[#3fb950]" />
              <div>
                <span className="text-[#8b949e] block text-[10px]">Travel Dates</span>
                <span className="font-semibold text-[#e6edf3]">15 Nov – 24 Nov 2026</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 text-[#c9d1d9]">
              <Users className="w-4 h-4 text-[#a371f7]" />
              <div>
                <span className="text-[#8b949e] block text-[10px]">Travelers</span>
                <span className="font-semibold text-[#e6edf3]">2 Guests (Private)</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 text-[#c9d1d9]">
              <ShieldCheck className="w-4 h-4 text-[#d29922]" />
              <div>
                <span className="text-[#8b949e] block text-[10px]">Supplier status</span>
                <span className="font-semibold text-[#d8cda9]">Sample details — confirm availability</span>
              </div>
            </div>
          </div>
        </section>

        {/* Tier Selector */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-[#e6edf3]">Select Your Preferred Proposal Tier</h2>
              <p className="text-xs text-[#8b949e]">Toggle options to view differences in accommodation and logistics.</p>
            </div>
            <span className="text-xs font-mono text-[#8b949e]">Illustrative pricing · not refreshed</span>
          </div>

          <div className="grid sm:grid-cols-3 gap-4">
            {[
              {
                id: 'saver',
                title: 'Essential Saver',
                tag: 'Balanced Luxury',
                price: basePrices.saver,
                hotelText: '4/5-Star City Suites & Standard Safari',
              },
              {
                id: 'curated',
                title: 'Signature Curator',
                tag: 'RECOMMENDED',
                price: basePrices.curated,
                hotelText: 'The Silo Hotel & Private Sabi Sand Game Lodge',
              },
              {
                id: 'prestige',
                title: 'Ultra Prestige Suite',
                tag: 'Ultimate VIP',
                price: basePrices.prestige,
                hotelText: 'Deluxe Penthouse & Singita Bush Villa',
              },
            ].map((tier) => {
              const isSelected = activeTier === tier.id;
              return (
                <div
                  key={tier.id}
                  onClick={() => setActiveTier(tier.id as any)}
                  className={`p-5 rounded-xl border transition-all cursor-pointer space-y-3 relative ${
                    isSelected
                      ? 'bg-[#161b22] border-[#58a6ff] ring-1 ring-[#58a6ff] shadow-lg'
                      : 'bg-[#0d1117] border-[#30363d] hover:bg-[#161b22]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        tier.id === 'curated'
                          ? 'bg-[#1f6feb] text-white'
                          : 'bg-[#30363d] text-[#8b949e]'
                      }`}
                    >
                      {tier.tag}
                    </span>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-[#58a6ff]" />}
                  </div>

                  <div>
                    <h3 className="font-bold text-sm text-[#e6edf3]">{tier.title}</h3>
                    <p className="text-xs text-[#8b949e] mt-1">{tier.hotelText}</p>
                  </div>

                  <div className="pt-2 border-t border-[#30363d] flex items-baseline justify-between">
                    <span className="text-xs text-[#8b949e]">Package Base</span>
                    <span className="text-lg font-bold text-[#3fb950] font-mono">
                      ${tier.price.toLocaleString()}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Day-by-Day Itinerary Experience */}
        <section className="space-y-4">
          <div className="flex items-center justify-between border-b border-[#30363d] pb-3">
            <h2 className="text-lg font-bold text-[#e6edf3]">Detailed Day-by-Day Journey</h2>
            <span className="text-xs text-[#8b949e]">5 Days / 4 Nights Curated Schedule</span>
          </div>

          <div className="space-y-4">
            {itineraryDays.map((day) => (
              <div
                key={day.day}
                className="bg-[#161b22] border border-[#30363d] rounded-xl p-5 space-y-3 hover:border-[#8b949e]/40 transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#30363d]/60 pb-3">
                  <div className="flex items-center gap-3">
                    <span className="w-8 h-8 rounded-full bg-[#1f6feb]/20 border border-[#1f6feb]/40 text-[#58a6ff] font-bold text-xs flex items-center justify-center">
                      D{day.day}
                    </span>
                    <div>
                      <h3 className="font-semibold text-sm text-[#e6edf3]">{day.title}</h3>
                      <span className="text-xs text-[#8b949e] flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-[#58a6ff]" />
                        {day.location}
                      </span>
                    </div>
                  </div>

                  <div className="text-xs text-[#3fb950] bg-[#238636]/10 px-2.5 py-1 rounded border border-[#238636]/30 flex items-center gap-1.5 self-start sm:self-auto">
                    <Building2 className="w-3.5 h-3.5" />
                    <span>{day.hotel}</span>
                  </div>
                </div>

                <p className="text-xs text-[#c9d1d9] leading-relaxed">{day.summary}</p>

                <div className="pt-2 flex flex-wrap gap-2">
                  {day.inclusions.map((inc, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 text-[11px] bg-[#0d1117] border border-[#30363d] text-[#8b949e] rounded-md flex items-center gap-1"
                    >
                      <Check className="w-3 h-3 text-[#3fb950]" />
                      {inc}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Optional Add-Ons & Excursions */}
        <section className="space-y-4">
          <div>
            <h2 className="text-lg font-bold text-[#e6edf3]">Enhance Your Journey (Optional Add-Ons)</h2>
            <p className="text-xs text-[#8b949e]">Select optional bespoke excursions to add to your itinerary total.</p>
          </div>

          <div className="space-y-3">
            {addOns.map((addon) => (
              <div
                key={addon.id}
                onClick={() => handleToggleAddOn(addon.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer flex items-center justify-between gap-4 ${
                  addon.selected
                    ? 'bg-[#161b22] border-[#3fb950] shadow-sm'
                    : 'bg-[#0d1117] border-[#30363d] hover:bg-[#161b22]'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`w-5 h-5 rounded border mt-0.5 flex items-center justify-center transition-colors ${
                      addon.selected
                        ? 'bg-[#238636] border-[#3fb950] text-white'
                        : 'border-[#8b949e] bg-[#0d1117]'
                    }`}
                  >
                    {addon.selected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                  </div>

                  <div>
                    <h4 className="font-semibold text-sm text-[#e6edf3]">{addon.title}</h4>
                    <p className="text-xs text-[#8b949e] mt-0.5">{addon.description}</p>
                    <span className="text-[11px] text-[#58a6ff] block mt-1">Duration: {addon.duration}</span>
                  </div>
                </div>

                <div className="text-right shrink-0">
                  <span className="text-sm font-bold text-[#3fb950] font-mono">+${addon.price}</span>
                  <span className="text-[10px] text-[#8b949e] block">per person</span>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Grand Total & Acceptance Studio */}
        <section className="bg-gradient-to-r from-[#161b22] to-[#1f242c] border border-[#30363d] rounded-2xl p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#30363d] pb-6">
            <div>
              <span className="text-xs text-[#58a6ff] font-semibold uppercase tracking-wider">
                Illustrative Proposal Total
              </span>
              <h3 className="text-xl font-bold text-[#e6edf3] mt-1">
                Tier: {activeTier === 'saver' ? 'Essential Saver' : activeTier === 'curated' ? 'Signature Curator' : 'Ultra Prestige'}
              </h3>
              <p className="text-xs text-[#8b949e]">
                Illustrative accommodation, transfer, charter, and add-on options ({addOns.filter((a) => a.selected).length} selected).
              </p>
            </div>

            <div className="text-right">
              <div className="text-3xl sm:text-4xl font-extrabold text-[#3fb950] font-mono">
                ${grandTotal.toLocaleString()}
              </div>
              <span className="text-xs text-[#8b949e]">Illustrative total; taxes and fees require confirmation</span>
            </div>
          </div>

          {/* Action Trigger */}
          {accepted ? (
            <div className="bg-[#238636]/10 border border-[#238636]/40 rounded-xl p-6 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-[#3fb950] mx-auto" />
              <h3 className="text-base font-bold text-[#3fb950]">Acceptance Preview Complete (Demo)</h3>
              <p className="text-xs text-[#c9d1d9] max-w-md mx-auto leading-relaxed">
                This demo rendered an acceptance result locally. A sample hold request is shown for review — nothing was submitted and no inventory hold has actually been placed.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              <button
                type="button"
                onClick={handleAccept}
                disabled={accepting}
                className="w-full py-4 bg-[#238636] hover:bg-[#2ea043] text-white font-bold text-sm rounded-xl transition-all shadow-lg shadow-[#238636]/20 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {accepting ? (
                  <span>Simulating acceptance preview…</span>
                ) : (
                  <>
                    <span>Simulate Proposal Acceptance</span>
                    <ChevronRight className="w-4 h-4" />
                  </>
                )}
              </button>
              <div className="text-center text-[11px] text-[#8b949e]">
                Demo only • no acceptance is submitted and no accommodation or charter slots are held
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
