'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { BackToOverviewLink } from '@/components/navigation/BackToOverviewLink';
import {
  BookOpen,
  Search,
  Sparkles,
  Compass,
  FileCheck2,
  Users,
  ShieldCheck,
  Plus,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
  Tag,
} from 'lucide-react';

interface PlaybookEntry {
  id: string;
  category: 'playbook' | 'visa' | 'preference' | 'rule';
  title: string;
  destination: string;
  summary: string;
  keyTakeaways: string[];
  lastUpdated: string;
  author: string;
  tags: string[];
}

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPlaybookId, setSelectedPlaybookId] = useState<string | null>(null);
  const [isNewPlaybookModalOpen, setIsNewPlaybookModalOpen] = useState<boolean>(false);

  const entries: PlaybookEntry[] = useMemo(() => {
    return [
      {
        id: 'kb_01',
        category: 'playbook',
        title: 'South Africa Luxury Safari & Malaria-Free Reserves Guide',
        destination: 'South Africa',
        summary: 'Operational playbook for high-net-worth families seeking 5-star safari experiences with zero malaria risk (Madikwe & Eastern Cape).',
        keyTakeaways: [
          'Madikwe Game Reserve is premier malaria-free destination for under-12 kids.',
          'Book private game vehicles to allow flexible schedule for younger children.',
          'Connect JNB to lodge directly via Federal Air charter to avoid 5h road transfers.',
        ],
        lastUpdated: '2026-08-20',
        author: 'Senior Africa Specialist',
        tags: ['Safari', 'Luxury', 'Family', 'Malaria-Free'],
      },
      {
        id: 'kb_02',
        category: 'visa',
        title: 'Schengen Visa Processing & Appointment Strategy for Indian Passports',
        destination: 'Europe (Schengen)',
        summary: 'Comprehensive checklist of mandatory documents, VFS appointment availability windows, and required travel insurance clauses.',
        keyTakeaways: [
          'Mandatory 6 months passport validity from intended return date with 2 blank pages.',
          'Travel insurance must cover minimum EUR 30,000 with COVID & repatriation inclusion.',
          'Apply via primary destination country to prevent entry refusal under Schengen rules.',
        ],
        lastUpdated: '2026-08-25',
        author: 'Head of Visa Operations',
        tags: ['Visa', 'Schengen', 'Compliance', 'Indian Passport'],
      },
      {
        id: 'kb_03',
        category: 'playbook',
        title: 'Japan Sakura (Cherry Blossom) 2027 Sourcing & Ryokan Playbook',
        destination: 'Japan',
        summary: 'Critical lead-time requirements for Kyoto ryokans, private kaiseki dining, and Shinkansen luggage booking rules during peak blossom season.',
        keyTakeaways: [
          'Top Kyoto ryokans (Tawaraya, Hiiragiya) open bookings 6 months in advance; lock in Oct.',
          'Tokaido Shinkansen requires oversized luggage area reservations (baggage > 160cm).',
          'Recommend Hiroshima/Miyajima or Kanazawa for less crowded secondary blossom spots.',
        ],
        lastUpdated: '2026-08-15',
        author: 'Asia Curator Lead',
        tags: ['Japan', 'Sakura', 'Ryokan', 'Peak Season'],
      },
      {
        id: 'kb_04',
        category: 'preference',
        title: 'Learned Customer Memory: HNW Family Dining & Transfer Heuristics',
        destination: 'Global',
        summary: 'Agency-wide learned taste profile from 150+ completed luxury trips. Tracks common unspoken preferences and VIP ground arrangements.',
        keyTakeaways: [
          'Always arrange pre-stocked vehicle with chilled still water and electrolyte drinks.',
          'Families with >2 kids prefer interconnecting suites over adjacent separate rooms.',
          'Automatic dietary flag: Ensure Jain / Vegan preferences communicated directly to hotel GM.',
        ],
        lastUpdated: '2026-08-28',
        author: 'Autonomous Customer Memory Engine',
        tags: ['Customer Memory', 'Taste Graph', 'VIP Concierge'],
      },
      {
        id: 'kb_05',
        category: 'rule',
        title: 'Agency Margin & Sourcing Guardrail Rules',
        destination: 'Internal Policy',
        summary: 'Standard operating rules governing minimum wholesale markup, quote risk overrides, and mandatory supplier credit checks.',
        keyTakeaways: [
          'Bespoke multi-city itineraries must maintain >= 14% gross markup before operator override.',
          'Quotes exceeding ,000 require senior operator approval in Quote Review queue.',
          'Only tier-1 DMCs eligible for 48h zero-cost hold without upfront client deposit.',
        ],
        lastUpdated: '2026-08-29',
        author: 'Agency Principal',
        tags: ['Governance', 'Margin Guardrails', 'Operating Policy'],
      },
    ];
  }, []);

  const filteredEntries = useMemo(() => {
    return entries.filter((e) => {
      const matchesCategory = selectedCategory === 'all' || e.category === selectedCategory;
      const matchesSearch =
        e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.destination.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
        e.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));
      return matchesCategory && matchesSearch;
    });
  }, [entries, selectedCategory, searchQuery]);

  const activeEntry = entries.find((e) => e.id === selectedPlaybookId) || filteredEntries[0] || entries[0];

  return (
    <div className='p-6 space-y-6'>
      <BackToOverviewLink />

      {/* Header */}
      <div className='flex flex-col md:flex-row md:items-center md:justify-between gap-4'>
        <div>
          <h1 className='text-ui-xl font-semibold text-[#e6edf3] flex items-center gap-2'>
            <BookOpen className='size-6 text-[#58a6ff]' />
            Knowledge Base & Agency Memory
          </h1>
          <p className='text-ui-sm text-[#8b949e] mt-1'>
            Canonical agency intelligence, destination playbooks, visa compliance checklists, and learned customer memory.
          </p>
        </div>

        <button
          type='button'
          onClick={() => setIsNewPlaybookModalOpen(true)}
          className='px-3.5 py-2 bg-[#238636] hover:bg-[#2ea043] text-white text-xs font-semibold rounded-md flex items-center gap-1.5 transition-colors shadow-sm self-start md:self-auto'
        >
          <Plus className='size-3.5' />
          Create New Playbook
        </button>
      </div>

      {/* RAG Search Bar */}
      <div className='rounded-lg border border-[#30363d] p-4 bg-[#0d1117] space-y-3'>
        <div className='relative w-full'>
          <Search className='absolute left-3.5 top-3 size-4 text-[#58a6ff]' />
          <input
            type='text'
            placeholder='Ask Agency Brain (e.g. "Schengen passport rules", "South Africa safari with kids", "Kyoto ryokan booking timeline")…'
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className='w-full pl-10 pr-4 py-2.5 bg-[#161b22] border border-[#30363d] rounded-md text-sm text-[#e6edf3] placeholder-[#8b949e] focus:border-[#58a6ff] outline-none shadow-inner'
          />
        </div>

        <div className='flex flex-wrap gap-1.5 pt-1'>
          {[
            { id: 'all', label: 'All Intelligence' },
            { id: 'playbook', label: 'Playbooks & Cheatsheets' },
            { id: 'visa', label: 'Visa & Regulatory' },
            { id: 'preference', label: 'Customer Memory' },
            { id: 'rule', label: 'Agency Rules' },
          ].map((cat) => {
            const isSelected = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                type='button'
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  isSelected
                    ? 'bg-[#1f6feb] text-white'
                    : 'bg-[#161b22] text-[#8b949e] hover:text-[#e6edf3] border border-[#30363d]'
                }`}
              >
                {cat.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Knowledge List & Playbook Detail Drawer */}
      <div className='grid gap-6 lg:grid-cols-3'>
        {/* Knowledge Articles List */}
        <div className='lg:col-span-2 space-y-3'>
          <div className='text-xs font-semibold text-[#8b949e] uppercase tracking-wider px-1'>
            Verified Articles & Memory Nodes ({filteredEntries.length})
          </div>

          <div className='space-y-3'>
            {filteredEntries.map((entry) => {
              const isSelected = entry.id === (selectedPlaybookId || activeEntry?.id);
              const categoryBadgeClass =
                entry.category === 'playbook'
                  ? 'bg-[#1f6feb]/20 text-[#58a6ff] border border-[#1f6feb]/40'
                  : entry.category === 'visa'
                  ? 'bg-[#d29922]/20 text-[#d29922] border border-[#d29922]/40'
                  : entry.category === 'preference'
                  ? 'bg-[#a371f7]/20 text-[#a371f7] border border-[#a371f7]/40'
                  : 'bg-[#238636]/20 text-[#3fb950] border border-[#238636]/40';

              return (
                <div
                  key={entry.id}
                  onClick={() => setSelectedPlaybookId(entry.id)}
                  className={`p-4 rounded-lg border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-[#161b22] border-[#58a6ff] shadow-md'
                      : 'bg-[#0d1117] border-[#30363d] hover:bg-[#161b22] hover:border-[#8b949e]/40'
                  }`}
                >
                  <div className='flex items-start justify-between gap-3'>
                    <div className='space-y-1'>
                      <div className='flex items-center gap-2'>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider ${categoryBadgeClass}`}>
                          {entry.category}
                        </span>
                        <span className='text-xs font-medium text-[#8b949e]'>• {entry.destination}</span>
                      </div>
                      <h3 className='text-sm font-semibold text-[#e6edf3]'>{entry.title}</h3>
                    </div>
                    <span className='text-[11px] text-[#8b949e] shrink-0 font-mono'>{entry.lastUpdated}</span>
                  </div>

                  <p className='text-xs text-[#8b949e] mt-2 line-clamp-2'>{entry.summary}</p>

                  <div className='flex flex-wrap items-center gap-1.5 mt-3'>
                    {entry.tags.map((tag, i) => (
                      <span
                        key={i}
                        className='px-2 py-0.5 text-[10px] bg-[#161b22] border border-[#30363d] text-[#c9d1d9] rounded-full flex items-center gap-1'
                      >
                        <Tag className='size-2.5 text-[#8b949e]' />
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detailed Inspector Drawer */}
        <div className='space-y-4'>
          {activeEntry ? (
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-5 space-y-4 sticky top-6'>
              <div className='border-b border-[#30363d] pb-3 space-y-2'>
                <div className='flex items-center justify-between text-xs text-[#8b949e]'>
                  <span>Author: {activeEntry.author}</span>
                  <span className='font-mono'>{activeEntry.lastUpdated}</span>
                </div>
                <h2 className='text-sm font-bold text-[#e6edf3] leading-snug'>{activeEntry.title}</h2>
                <div className='text-xs text-[#58a6ff]'>Scope: {activeEntry.destination}</div>
              </div>

              <div className='space-y-3 text-xs'>
                <div>
                  <div className='font-semibold text-[#8b949e] uppercase text-[10px] mb-1'>Executive Summary</div>
                  <p className='text-[#c9d1d9] leading-relaxed'>{activeEntry.summary}</p>
                </div>

                <div className='pt-2 border-t border-[#30363d]'>
                  <div className='font-semibold text-[#8b949e] uppercase text-[10px] mb-2'>
                    Mandatory Operational Rules & Takeaways
                  </div>
                  <ul className='space-y-2'>
                    {activeEntry.keyTakeaways.map((point, i) => (
                      <li key={i} className='flex items-start gap-2 text-[#c9d1d9]'>
                        <CheckCircle2 className='size-4 text-[#3fb950] shrink-0 mt-0.5' />
                        <span className='leading-tight'>{point}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className='pt-3 border-t border-[#30363d] flex items-center justify-between text-xs'>
                <span className='text-[#8b949e]'>Synced with RAG Vector Store</span>
                <Link
                  href='/overview'
                  className='text-[#58a6ff] hover:text-[#79b8ff] font-medium inline-flex items-center gap-1'
                >
                  <span>Return to Command</span>
                  <ArrowRight className='size-3' />
                </Link>
              </div>
            </div>
          ) : (
            <div className='rounded-lg border border-[#30363d] bg-[#0d1117] p-6 text-center text-xs text-[#8b949e]'>
              Select an article to inspect full playbooks.
            </div>
          )}
        </div>
      </div>

      {/* Create New Playbook Modal */}
      {isNewPlaybookModalOpen && (
        <div className='fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4'>
          <div className='w-full max-w-lg bg-[#0d1117] border border-[#30363d] rounded-lg shadow-xl p-6 space-y-4'>
            <div className='flex items-center justify-between border-b border-[#30363d] pb-3'>
              <div className='flex items-center gap-2 font-semibold text-base text-[#e6edf3]'>
                <BookOpen className='size-5 text-[#58a6ff]' />
                <span>Create New Agency Playbook</span>
              </div>
              <button
                type='button'
                onClick={() => setIsNewPlaybookModalOpen(false)}
                className='text-[#8b949e] hover:text-[#e6edf3] text-sm'
              >
                ✕
              </button>
            </div>

            <div className='space-y-3 text-xs text-[#c9d1d9]'>
              <div>
                <label className='block text-[#8b949e] mb-1 font-medium'>Playbook Title</label>
                <input
                  type='text'
                  placeholder='e.g., Vietnam & Cambodia Luxury River Cruise Logistics'
                  className='w-full p-2 bg-[#161b22] border border-[#30363d] rounded text-sm text-[#e6edf3] outline-none focus:border-[#58a6ff]'
                />
              </div>

              <div>
                <label className='block text-[#8b949e] mb-1 font-medium'>Destination / Category</label>
                <input
                  type='text'
                  placeholder='e.g., Southeast Asia (Mekong)'
                  className='w-full p-2 bg-[#161b22] border border-[#30363d] rounded text-sm text-[#e6edf3] outline-none focus:border-[#58a6ff]'
                />
              </div>

              <div>
                <label className='block text-[#8b949e] mb-1 font-medium'>Operational Guidance & Takeaways</label>
                <textarea
                  rows={4}
                  placeholder='Enter operational notes, preferred DMC contacts, visa rules, and pacing recommendations…'
                  className='w-full p-2 bg-[#161b22] border border-[#30363d] rounded text-sm text-[#e6edf3] outline-none focus:border-[#58a6ff]'
                ></textarea>
              </div>
            </div>

            <div className='flex justify-end gap-2 pt-2 border-t border-[#30363d]'>
              <button
                type='button'
                onClick={() => setIsNewPlaybookModalOpen(false)}
                className='px-3.5 py-1.5 bg-[#21262d] text-[#e6edf3] rounded text-xs hover:bg-[#30363d] border border-[#30363d]'
              >
                Cancel
              </button>
              <button
                type='button'
                onClick={() => setIsNewPlaybookModalOpen(false)}
                className='px-3.5 py-1.5 bg-[#238636] text-white rounded text-xs font-semibold hover:bg-[#2ea043]'
              >
                Save & Index into Agency Brain
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
