// Canonical lifecycle for the departure-board handoff session:
// 1. Departure board writes a claimed case on CTA click (writer).
// 2. Login/signup read it to show the Case Queue banner and build the
//    workbench redirect (readers).
// 3. Cleared once auth completes, or when workbench intake consumes the
//    prefill directly (so a claimed case never resurfaces as a stale banner).

export interface DepartureBoardHandoff {
  source?: string;
  caseSlug?: string;
  caseTitle?: string;
  iataCode?: string;
  prefill?: string;
}

const HANDOFF_STORAGE_KEY = 'waypoint_departure_board_handoff';

export function readDepartureBoardHandoff(): DepartureBoardHandoff | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.sessionStorage.getItem(HANDOFF_STORAGE_KEY);
    return raw ? (JSON.parse(raw) as DepartureBoardHandoff) : null;
  } catch {
    return null;
  }
}

export function writeDepartureBoardHandoff(handoff: DepartureBoardHandoff): void {
  try {
    window.sessionStorage.setItem(HANDOFF_STORAGE_KEY, JSON.stringify(handoff));
  } catch {
    // non-blocking: the board CTA still navigates without the handoff
  }
}

export function clearDepartureBoardHandoff(): void {
  try {
    window.sessionStorage.removeItem(HANDOFF_STORAGE_KEY);
  } catch {
    // non-blocking
  }
}
