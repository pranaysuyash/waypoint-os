import { describe, expect, it } from 'vitest';
import {
  stripMessagingNoise,
  parseMessyTravelNote,
  formatCleanIntakeNote,
} from '../messy-ingest-cleaner';

describe('Messy Ingest Cleaner & Slot Extractor', () => {
  it('strips WhatsApp timestamps and names correctly', () => {
    const raw = `[11:04 AM, 11/02/2026] Rahul Verma: Hey Pranay, need a trip to Bali.\n[11:05 AM, 11/02/2026] Rahul Verma: Couple only, vegetarian meals please.`;
    const cleaned = stripMessagingNoise(raw);
    expect(cleaned).not.toContain('11:04 AM');
    expect(cleaned).not.toContain('Rahul Verma:');
    expect(cleaned).toContain('Hey Pranay, need a trip to Bali.');
    expect(cleaned).toContain('Couple only, vegetarian meals please.');
  });

  it('strips email forward headers correctly', () => {
    const raw = `---------- Forwarded message ---------
From: Ananya Gupta <ananya@example.com>
Date: Fri, Nov 6, 2026 at 4:15 PM
Subject: Family trip to Dubai
To: trips@waypoint.app

Hi team, we are planning Dubai from DEL Dec 20-28 for family of 4. Budget INR 6 Lakhs.`;

    const cleaned = stripMessagingNoise(raw);
    expect(cleaned).not.toContain('From: Ananya Gupta');
    expect(cleaned).not.toContain('Forwarded message');
    expect(cleaned).toContain('Hi team, we are planning Dubai');
  });

  it('extracts slots from colloquial messy text', () => {
    const raw = `[10:14 AM, 4/12/2026] Client: Planning 6N in Dubai and Abu Dhabi for me and wife with 2 kids. Flying from DEL Dec 20 to 28. Want Atlantis The Palm. Budget around INR 6-7 Lakhs. Vegetarian meals required.`;
    const parsed = parseMessyTravelNote(raw);

    expect(parsed.destinations).toContain('Dubai');
    expect(parsed.destinations).toContain('Abu Dhabi');
    expect(parsed.origin).toBe('DEL');
    expect(parsed.partySize).toBe(4);
    expect(parsed.partySummary).toContain('Couple + 2 children');
    expect(parsed.hotelMentions.some((h) => h.includes('Atlantis'))).toBe(true);
    expect(parsed.budgetSummary).toContain('6-7 Lakhs');
    expect(parsed.dietaryOrPreferences).toContain('Vegetarian meals');
  });

  it('formats structured brief note ready for intake', () => {
    const raw = `Trip from BOM to Maldives for honeymoon, 5 nights in June, budget $6000. Want Four Seasons or private pool villa.`;
    const parsed = parseMessyTravelNote(raw);
    const formatted = formatCleanIntakeNote(parsed);

    expect(formatted).toContain('Trip Request: Maldives');
    expect(formatted).toContain('Origin: BOM');
    expect(formatted).toContain('Budget: $6000');
    expect(formatted).toContain('Honeymoon');
    expect(formatted).toContain('Private pool villa');
    expect(formatted).toContain('Four Seasons');
  });
});
