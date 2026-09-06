'use client';

import React, { useState } from 'react';
import { FileText, CheckCircle2, Sparkles } from 'lucide-react';
import SimulatedBadge from '@/components/ui/SimulatedBadge';

/**
 * GM-01 honesty fix: the ICAO 9303 checksum engine is real math, but this
 * surface parses a sample passport string typed into the form — no scanner or
 * document intake pipeline feeds it.
 */

type DocSubTab = 'passport_mrz' | 'vouchers';

type ParsedPassport = {
  surname: string;
  given_names: string;
  passport_number: string;
  nationality: string;
  date_of_birth: string;
  gender: string;
  expiration_date: string;
  checksums_valid: {
    passport_number: boolean;
    date_of_birth: boolean;
    expiration_date: boolean;
    composite: boolean;
  };
};

export default function DocumentMRZPanel() {
  const [activeTab, setActiveTab] = useState<DocSubTab>('passport_mrz');
  const [line1, setLine1] = useState('P<UTOERIKSSON<<ANNA<MARIA<<<<<<<<<<<<<<<<<<<');
  const [line2, setLine2] = useState('L898902C<3UTO6908061F2801027ZE184226B<<<<<10');
  const [parsedPassport, setParsedPassport] = useState<ParsedPassport | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [parseError, setParseError] = useState<string | null>(null);

  const handleParseMRZ = async () => {
    setIsParsing(true);
    setParseError(null);
    setParsedPassport(null);
    try {
      const res = await fetch('/api/v1/documents/mrz/parse-td3', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ line1, line2 }),
      });
      if (res.ok) {
        const data = await res.json();
        if (!data.passport) {
          throw new Error('Parser response did not include a passport result');
        }
        setParsedPassport(data.passport as ParsedPassport);
      } else {
        throw new Error('Parser request failed');
      }
    } catch {
      // Do not substitute a hardcoded passport when the parser is unavailable:
      // an unavailable parser is not evidence that the submitted text is valid.
      setParseError('Parser unavailable. No checksum result was produced, and no document was verified.');
    } finally {
      setIsParsing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <SimulatedBadge label="Sample data" />
      </div>
      <div
        data-testid="mrz-preview-notice"
        role="note"
        className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-xs leading-5 text-amber-100"
      >
        <strong>Local parser preview:</strong> checksum mathematics run against the text supplied here. This does not authenticate a passport, establish identity, detect every transcription error, or query an airline, border authority, GDS, or hotel system.
      </div>
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <button
          type="button"
          aria-pressed={activeTab === 'passport_mrz'}
          onClick={() => setActiveTab('passport_mrz')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'passport_mrz' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <FileText className="h-3.5 w-3.5" />
          ICAO Doc 9303 MRZ Engine
        </button>
        <button
          type="button"
          aria-pressed={activeTab === 'vouchers'}
          onClick={() => setActiveTab('vouchers')}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
            activeTab === 'vouchers' ? 'bg-primary text-primary-foreground shadow-sm' : 'bg-muted text-muted-foreground hover:bg-accent'
          }`}
        >
          <Sparkles className="h-3.5 w-3.5" />
          13-Digit E-Ticket & Vouchers
        </button>
      </div>

      {activeTab === 'passport_mrz' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-4">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <FileText className="h-4 w-4 text-primary" />
              ICAO 7-3-1 Modulo-10 Checksum Verifier (TD3 2x44)
            </h4>
              <span className="text-[10px] font-mono bg-amber-500/10 text-amber-300 px-2 py-0.5 rounded">CHECKSUM RULES APPLIED</span>
          </div>
          <div className="space-y-2">
            <div>
              <label htmlFor="mrz-line-1" className="text-[11px] font-mono text-muted-foreground">Line 1 (44 chars)</label>
              <input
                id="mrz-line-1"
                type="text"
                value={line1}
                onChange={(e) => setLine1(e.target.value)}
                className="w-full p-2 font-mono text-xs rounded border border-border bg-background text-foreground"
              />
            </div>
            <div>
              <label htmlFor="mrz-line-2" className="text-[11px] font-mono text-muted-foreground">Line 2 (44 chars)</label>
              <input
                id="mrz-line-2"
                type="text"
                value={line2}
                onChange={(e) => setLine2(e.target.value)}
                className="w-full p-2 font-mono text-xs rounded border border-border bg-background text-foreground"
              />
            </div>
          </div>
          <button
            type="button"
            disabled={isParsing}
            onClick={handleParseMRZ}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-xs font-semibold hover:bg-primary/90"
          >
            {isParsing ? 'Computing checksum preview…' : 'Compute Checksum Preview'}
          </button>

          {parseError && (
            <p role="alert" className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-200">
              {parseError}
            </p>
          )}

          {parsedPassport && (
            <div className="p-3.5 rounded-lg border border-border bg-muted/40 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-foreground">
                  {parsedPassport.given_names} {parsedPassport.surname}
                </span>
                <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  CHECKSUMS VALID — FORMAT ONLY
                </span>
              </div>
              <p className="text-[11px] leading-4 text-muted-foreground">
                The parser accepted the supplied MRZ structure and check digits. It did not verify document authenticity, identity, immigration status, or any external booking record.
              </p>
              <div className="grid grid-cols-4 gap-2 text-xs">
                <div>
                  <span className="text-[10px] text-muted-foreground block">Passport No.</span>
                  <span className="font-mono font-semibold">{parsedPassport.passport_number}</span>
                </div>
                <div>
                  <span className="text-[10px] text-muted-foreground block">Nationality</span>
                  <span className="font-mono font-semibold">{parsedPassport.nationality}</span>
                </div>
                <div>
                  <span className="text-[10px] text-muted-foreground block">Date of Birth</span>
                  <span className="font-mono font-semibold">{parsedPassport.date_of_birth}</span>
                </div>
                <div>
                  <span className="text-[10px] text-muted-foreground block">Expiration</span>
                  <span className="font-mono font-semibold">{parsedPassport.expiration_date}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'vouchers' && (
        <div className="p-4 rounded-xl border border-border bg-card space-y-3">
          <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-amber-500" />
            13-Digit E-Ticket & Hotel Confirmation Parser (Sample Fixtures)
          </h4>
          <p data-testid="voucher-preview-notice" className="text-xs leading-5 text-muted-foreground">
            Illustrative strings only. No ticket, booking, or hotel voucher is checked against an airline, GDS, supplier, or hotel API.
          </p>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <span className="text-muted-foreground block text-[10px]">SAMPLE E-TICKET STRING</span>
              <span className="font-mono font-bold text-foreground text-sm">006-2345678901</span>
              <span className="text-[10px] text-amber-300 block mt-1">Format preview only</span>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <span className="text-muted-foreground block text-[10px]">SAMPLE RECORD LOCATOR</span>
              <span className="font-mono font-bold text-foreground text-sm">W4KZ9L</span>
              <span className="text-[10px] text-amber-300 block mt-1">No GDS lookup</span>
            </div>
            <div className="p-3 rounded-lg border border-border bg-muted/30">
              <span className="text-muted-foreground block text-[10px]">SAMPLE HOTEL VOUCHER CODE</span>
              <span className="font-mono font-bold text-foreground text-sm">HTL-883921</span>
              <span className="text-[10px] text-amber-300 block mt-1">No hotel API lookup</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
