'use client';

import React, { useState } from 'react';
import { Sparkles, MessageSquare, Mail, RefreshCw, Check, ArrowRight, X } from 'lucide-react';
import {
  parseMessyTravelNote,
  formatCleanIntakeNote,
  type ExtractedTravelSlots,
} from '@/lib/messy-ingest-cleaner';

interface QuickIngestPaletteProps {
  onApply: (formattedText: string) => void;
}

const SAMPLE_WHATSAPP = `[10:14 AM, 4/12/2026] Rahul Verma: Hey Pranay! Need a 6N vacation in Dubai and Abu Dhabi for me, wife and 2 kids (ages 7 and 11).
[10:15 AM, 4/12/2026] Rahul Verma: Flying from DEL around Dec 20 to 28. Want Atlantis The Palm for the waterpark.
[10:16 AM, 4/12/2026] Rahul Verma: Budget is around INR 6-7 Lakhs total. Pure vegetarian meals is a must!`;

const SAMPLE_EMAIL = `---------- Forwarded message ---------
From: Ananya Singhania <ananya@example.com>
Date: Fri, Nov 6, 2026 at 4:15 PM
Subject: Maldives luxury honeymoon
To: reservations@waypoint.app

Hi, looking for a 5-night honeymoon in Maldives in late June. Flying from BOM. Budget is around $6,000 USD. Prefer Four Seasons or private pool water villa. Halal dining preferred.`;

export function QuickIngestPalette({ onApply }: QuickIngestPaletteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [rawInput, setRawInput] = useState('');
  const [parsed, setParsed] = useState<ExtractedTravelSlots | null>(null);
  const [applied, setApplied] = useState(false);

  const handleTextChange = (text: string) => {
    setRawInput(text);
    setApplied(false);
    if (text.trim().length >= 10) {
      setParsed(parseMessyTravelNote(text));
    } else {
      setParsed(null);
    }
  };

  const loadSample = (sample: string) => {
    handleTextChange(sample);
  };

  const handleApply = () => {
    if (!parsed) return;
    const cleanNote = formatCleanIntakeNote(parsed);
    onApply(cleanNote);
    setApplied(true);
    setTimeout(() => {
      setApplied(false);
      setIsOpen(false);
    }, 1200);
  };

  if (!isOpen) {
    return (
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#30363d] bg-[#161b22] hover:bg-[#21262d] text-[#58a6ff] hover:text-[#79c0ff] text-ui-xs font-medium transition-colors"
      >
        <Sparkles className="size-3.5 text-[#39d0d8]" />
        <span>Quick Ingest (WhatsApp / Email Scrub)</span>
      </button>
    );
  }

  return (
    <div className="rounded-xl border border-[#30363d] bg-[#161b22] p-4 space-y-4 mb-4 transition-all">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="size-4 text-[#39d0d8]" />
          <h4 className="text-ui-sm font-semibold text-[#e6edf3]">
            Quick Ingest & Transcript Scrub
          </h4>
          <span className="text-[10px] font-mono text-[#39d0d8] bg-[#39d0d8]/10 px-1.5 py-0.5 rounded border border-[#39d0d8]/30">
            Stream 2 Utility
          </span>
        </div>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          className="text-[#8b949e] hover:text-[#e6edf3] p-1 rounded transition-colors"
          aria-label="Close Quick Ingest"
        >
          <X className="size-4" />
        </button>
      </div>

      <p className="text-ui-xs text-[#8b949e]">
        Paste messy forwarded emails, WhatsApp conversations, or raw voice transcripts. Waypoint strips headers, timestamps, and formatting noise, and extracts structured travel slots.
      </p>

      {/* Preset Test Buttons */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[11px] text-[#8b949e]">Try sample:</span>
        <button
          type="button"
          onClick={() => loadSample(SAMPLE_WHATSAPP)}
          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] text-[11px] border border-[#30363d] transition-colors"
        >
          <MessageSquare className="size-3 text-[#3fb950]" />
          WhatsApp Family Chat
        </button>
        <button
          type="button"
          onClick={() => loadSample(SAMPLE_EMAIL)}
          className="inline-flex items-center gap-1 px-2 py-1 rounded bg-[#21262d] hover:bg-[#30363d] text-[#c9d1d9] text-[11px] border border-[#30363d] transition-colors"
        >
          <Mail className="size-3 text-[#58a6ff]" />
          Email Forward
        </button>
        {rawInput && (
          <button
            type="button"
            onClick={() => handleTextChange('')}
            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-transparent hover:bg-[#21262d] text-[#8b949e] text-[11px] transition-colors ml-auto"
          >
            <RefreshCw className="size-3" />
            Clear
          </button>
        )}
      </div>

      {/* Raw Input Area */}
      <textarea
        value={rawInput}
        onChange={(e) => handleTextChange(e.target.value)}
        placeholder="Paste WhatsApp chat export, messy forwarded email, or client voice transcript here..."
        rows={4}
        className="w-full px-3 py-2 bg-[#0d1117] border border-[#30363d] rounded-lg text-ui-xs text-[#e6edf3] placeholder:text-[#484f58] focus:outline-none focus:border-[#58a6ff] resize-none font-mono"
      />

      {/* Extracted Slots Badges */}
      {parsed && (
        <div className="p-3 rounded-lg border border-[#30363d] bg-[#0d1117] space-y-2.5">
          <div className="text-[11px] font-semibold uppercase tracking-wider text-[#8b949e]">
            Extracted Travel Slots
          </div>
          <div className="flex flex-wrap gap-2 text-ui-xs">
            {parsed.destinations.length > 0 && (
              <span className="px-2 py-1 rounded bg-[#238636]/20 border border-[#238636]/40 text-[#3fb950] font-medium">
                📍 {parsed.destinations.join(' & ')}
              </span>
            )}
            {parsed.origin && (
              <span className="px-2 py-1 rounded bg-[#1f6feb]/20 border border-[#1f6feb]/40 text-[#58a6ff] font-medium">
                🛫 Ex: {parsed.origin}
              </span>
            )}
            {parsed.partySummary && (
              <span className="px-2 py-1 rounded bg-[#388bfd]/20 border border-[#388bfd]/40 text-[#79c0ff]">
                👥 {parsed.partySummary}
              </span>
            )}
            {parsed.datesSummary && (
              <span className="px-2 py-1 rounded bg-[#d29922]/20 border border-[#d29922]/40 text-[#e3b341]">
                📅 {parsed.datesSummary}
              </span>
            )}
            {parsed.budgetSummary && (
              <span className="px-2 py-1 rounded bg-[#238636]/20 border border-[#238636]/40 text-[#3fb950]">
                💰 {parsed.budgetSummary}
              </span>
            )}
            {parsed.hotelMentions.length > 0 && (
              <span className="px-2 py-1 rounded bg-[#a371f7]/20 border border-[#a371f7]/40 text-[#d2a8ff]">
                🏨 {parsed.hotelMentions.join(', ')}
              </span>
            )}
            {parsed.dietaryOrPreferences.map((pref, i) => (
              <span key={i} className="px-2 py-1 rounded bg-[#21262d] border border-[#30363d] text-[#c9d1d9]">
                ✨ {pref}
              </span>
            ))}
          </div>

          <div className="pt-2 flex items-center justify-end gap-2 border-t border-[#21262d]">
            <button
              type="button"
              onClick={handleApply}
              disabled={applied}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-ui-xs font-semibold transition-all ${
                applied
                  ? 'bg-[#238636] text-white'
                  : 'bg-[#1f6feb] hover:bg-[#388bfd] text-white'
              }`}
            >
              {applied ? (
                <>
                  <Check className="size-3.5" />
                  Applied to Intake!
                </>
              ) : (
                <>
                  <span>Apply Structured Brief to Draft</span>
                  <ArrowRight className="size-3.5" />
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
