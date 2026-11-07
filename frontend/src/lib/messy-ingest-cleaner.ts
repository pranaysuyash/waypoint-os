/**
 * Messy Ingest Cleaner & Parser (Stream 2 - Daily Utility)
 * 
 * Cleans messy communication transcripts (WhatsApp, SMS, email forwards, voice transcripts)
 * and extracts high-confidence travel brief slots without manual re-typing.
 */

export interface ExtractedTravelSlots {
  destinations: string[];
  origin?: string;
  partySummary?: string;
  partySize?: number;
  datesSummary?: string;
  budgetSummary?: string;
  hotelMentions: string[];
  dietaryOrPreferences: string[];
  cleanedText: string;
}

const COMMON_DESTINATIONS = [
  'Dubai', 'Abu Dhabi', 'Bali', 'Singapore', 'Phuket', 'Bangkok', 'Koh Samui',
  'Maldives', 'Mauritius', 'Paris', 'Rome', 'London', 'Tokyo', 'Kyoto',
  'Osaka', 'Switzerland', 'Zurich', 'Lucerne', 'Interlaken', 'Santorini',
  'Athens', 'Amsterdam', 'Barcelona', 'Madrid', 'New York', 'Hawaii',
  'Vietnam', 'Da Nang', 'Hanoi', 'Iceland', 'Norway', 'Kashmir', 'Ladakh',
  'Goa', 'Kerala', 'Rajasthan', 'Jaipur', 'Udaipur'
];

const COMMON_HOTEL_CHAINS = [
  'Atlantis', 'Ritz-Carlton', 'The Ritz', 'Four Seasons', 'St. Regis',
  'Bulgari', 'Aman', 'Belmond', 'Rosewood', 'Mandarin Oriental',
  'One&Only', 'Waldorf Astoria', 'Marriott', 'Hilton', 'Hyatt', 'Taj',
  'Oberoi', 'Leela', 'Banyan Tree', 'Six Senses', 'Jumeirah'
];

export function stripMessagingNoise(rawText: string): string {
  let cleaned = rawText;

  // 1. Strip WhatsApp export timestamps [11:04 AM, 11/02/2026] Name: or 11/02/26, 11:04 - Name:
  cleaned = cleaned.replace(/\[\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?,?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\]\s*[^:\n\r]+:\s*/gi, '');
  cleaned = cleaned.replace(/\d{1,2}[/-]\d{1,2}[/-]\d{2,4},?\s*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*-\s*[^:\n\r]+:\s*/gi, '');

  // 2. Strip Email forward headers & markers
  cleaned = cleaned.replace(/---------- Forwarded message ---------/gi, '');
  cleaned = cleaned.replace(/^(?:From|Sent|Date|To|Subject|Cc):\s*.*$/gmi, '');

  // 3. Normalize multiple whitespace and extra blank lines
  cleaned = cleaned.replace(/\r\n/g, '\n').replace(/\n{3,}/g, '\n\n').trim();

  return cleaned;
}

export function parseMessyTravelNote(rawText: string): ExtractedTravelSlots {
  const cleaned = stripMessagingNoise(rawText);
  const textLower = cleaned.toLowerCase();

  // Extract Destinations
  const matchedDestinations: string[] = [];
  for (const dest of COMMON_DESTINATIONS) {
    const regex = new RegExp(`\\b${dest}\\b`, 'i');
    if (regex.test(cleaned)) {
      matchedDestinations.push(dest);
    }
  }

  // Extract Origin
  let origin: string | undefined;
  const airportCodeMatch = cleaned.match(/\b(?:from|ex|departs?|departing|origin)\s*[:\-]?\s*([A-Z]{3})\b/i)
    ?? cleaned.match(/\b([A-Z]{3})\s*(?:to|->|—)\b/i);
  if (airportCodeMatch) {
    origin = airportCodeMatch[1].toUpperCase();
  } else {
    const originCityMatch = cleaned.match(/\b(?:from|ex|flying from)\s+([A-Za-z\s]+?)(?=[,\.\n]|for|to|\bwith\b|\bin\b|$)/i);
    if (originCityMatch) {
      origin = originCityMatch[1].trim();
    }
  }

  // Extract Party Size / Composition
  let partySize: number | undefined;
  let partySummary: string | undefined;
  
  if (
    /\bcouple\b/i.test(textLower) ||
    /\bme\s*(?:and|&|,)\s*(?:wife|husband|partner|fiancee?)\b/i.test(textLower) ||
    /\b(?:wife|husband|partner)\s*(?:and|&|,)\s*me\b/i.test(textLower)
  ) {
    const kidsMatch = cleaned.match(/(\d+)\s*(?:kids?|children|child)/i);
    if (kidsMatch) {
      const kids = parseInt(kidsMatch[1], 10);
      partySize = 2 + kids;
      partySummary = `Couple + ${kids} children (${partySize} travelers)`;
    } else {
      partySize = 2;
      partySummary = 'Couple (2 travelers)';
    }
  } else {
    const paxMatch = cleaned.match(/(\d+)\s*(?:pax|people|travelers?|travellers?|adults?|guests)/i);
    if (paxMatch) {
      partySize = parseInt(paxMatch[1], 10);
      partySummary = `${partySize} travelers`;
    }
  }

  // Extract Dates / Duration
  let datesSummary: string | undefined;
  const durationMatch = cleaned.match(/(\d+)\s*(?:n(?:ights?)?|d(?:ays?)?)\s*(?:[\/&]\s*(\d+)\s*(?:d(?:ays?)?|n(?:ights?)?))?/i);
  const dateWindowMatch = cleaned.match(/\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:\s*[-–to]\s*\d{1,2})?(?:,?\s*\d{4})?/i)
    ?? cleaned.match(/\b\d{1,2}(?:st|nd|rd|th)?\s*[-–to]\s*\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*/i);

  if (durationMatch && dateWindowMatch) {
    datesSummary = `${dateWindowMatch[0]} (${durationMatch[0]})`;
  } else if (dateWindowMatch) {
    datesSummary = dateWindowMatch[0];
  } else if (durationMatch) {
    datesSummary = durationMatch[0];
  }

  // Extract Budget
  let budgetSummary: string | undefined;
  const inrBudgetMatch = cleaned.match(/(?:INR|Rs\.?|₹)\s*(\d+\s*[-–to]\s*\d+\s*(?:lakhs?|lac|cr|k)?|[\d,]+(?:\.\d+)?\s*(?:lakhs?|lac|cr|k)?)/i)
    ?? cleaned.match(/(\d+\s*[-–to]\s*\d+|\d+)\s*(?:lakhs?|lacs?)\s*(?:INR|rupees)?/i);
  const usdBudgetMatch = cleaned.match(/(?:\$|USD|EUR|GBP|£|€)\s*([\d,]+(?:\s*[-–to]\s*[\d,]+)?(?:\s*[kK])?)/i);

  if (inrBudgetMatch) {
    budgetSummary = inrBudgetMatch[0].trim();
  } else if (usdBudgetMatch) {
    budgetSummary = usdBudgetMatch[0].trim();
  }

  // Extract Hotels
  const matchedHotels: string[] = [];
  for (const hotel of COMMON_HOTEL_CHAINS) {
    const regex = new RegExp(`\\b${hotel}\\b[^,.\\n]*`, 'i');
    const m = cleaned.match(regex);
    if (m) {
      matchedHotels.push(m[0].trim());
    }
  }

  // Extract Dietary / Preferences
  const dietary: string[] = [];
  if (/\b(?:pure\s+)?veg(?:etarian)?\b/i.test(textLower)) dietary.push('Vegetarian meals');
  if (/\bjain\b/i.test(textLower)) dietary.push('Jain vegetarian meals');
  if (/\bvegan\b/i.test(textLower)) dietary.push('Vegan');
  if (/\bhalal\b/i.test(textLower)) dietary.push('Halal');
  if (/\banniversary\b/i.test(textLower)) dietary.push('Anniversary celebration');
  if (/\bhoneymoon\b/i.test(textLower)) dietary.push('Honeymoon');
  if (/\bbirthday\b/i.test(textLower)) dietary.push('Birthday trip');
  if (/\bprivate\s+(?:pool|villa)\b/i.test(textLower)) dietary.push('Private pool villa');
  if (/\bbeachfront|beach\s+villa\b/i.test(textLower)) dietary.push('Beachfront');

  return {
    destinations: matchedDestinations,
    origin,
    partySummary,
    partySize,
    datesSummary,
    budgetSummary,
    hotelMentions: matchedHotels,
    dietaryOrPreferences: dietary,
    cleanedText: cleaned,
  };
}

export function formatCleanIntakeNote(parsed: ExtractedTravelSlots): string {
  const lines: string[] = [];

  const headline = parsed.destinations.length > 0
    ? `Trip Request: ${parsed.destinations.join(' & ')}`
    : 'Trip Request';
  lines.push(headline);

  const logistics: string[] = [];
  if (parsed.origin) logistics.push(`Origin: ${parsed.origin}`);
  if (parsed.datesSummary) logistics.push(`Dates: ${parsed.datesSummary}`);
  if (parsed.partySummary) logistics.push(`Party: ${parsed.partySummary}`);
  if (logistics.length > 0) lines.push(logistics.join(' | '));

  const commercial: string[] = [];
  if (parsed.budgetSummary) commercial.push(`Budget: ${parsed.budgetSummary}`);
  if (parsed.hotelMentions.length > 0) commercial.push(`Hotels: ${parsed.hotelMentions.join(', ')}`);
  if (commercial.length > 0) lines.push(commercial.join(' | '));

  if (parsed.dietaryOrPreferences.length > 0) {
    lines.push(`Preferences: ${parsed.dietaryOrPreferences.join(' · ')}`);
  }

  lines.push('');
  lines.push('— Extracted from source transcript:');
  lines.push(parsed.cleanedText);

  return lines.join('\n');
}
