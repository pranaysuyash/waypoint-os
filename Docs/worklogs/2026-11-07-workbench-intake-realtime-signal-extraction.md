# Worklog: 2026-11-07 — Workbench Intake Overhaul & Real-Time Signal Extraction

**Date:** 2026-11-07  
**Target:** `http://localhost:3005/inquiries/new` (`/workbench`)  
**Components Modified:**
* [`frontend/src/app/(agency)/workbench/IntakeTab.tsx`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/workbench/IntakeTab.tsx)
* [`frontend/src/app/(agency)/workbench/RepeatTravelerRecallCard.tsx`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/workbench/RepeatTravelerRecallCard.tsx)
* [`frontend/src/lib/messy-ingest-cleaner.ts`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/lib/messy-ingest-cleaner.ts)
* [`frontend/src/app/(agency)/workbench/__tests__/IntakeTab.test.tsx`](file:///Users/pranay/Projects/travel_agency_agent/frontend/src/app/(agency)/workbench/__tests__/IntakeTab.test.tsx)

---

## 1. Executive Summary & First-Principles Motivation

Previous intake handling was constrained by two architectural flaws:
1. **Narrow Handoff Assumption:** Inquiries arriving at the advisor's desk were treated as if they primarily came from the departure board marketing banner, ignoring real agency intake reality (phone consultations, messy WhatsApp exports, forwarded client emails, direct walk-ins).
2. **Disconnected Intelligence & Delayed Value:** While the application possessed regex slot parsing utilities (`messy-ingest-cleaner.ts`) and a fast semantic triage engine (`Jev`), the slot extractor was locked away inside a secondary modal palette. Typing into the main Customer Message box produced only abstract telemetry tags (`INTENT: NEW_BOOKING`, `Tone: CALM`), while the primary "Captured Details" card remained completely blank until the advisor ran a full backend pipeline cycle.

### What Was Built:
* **Synchronous Travel Slot Parsing:** Direct, zero-lag parsing on the main textarea via `parseMessyTravelNote(input_raw_note)`.
* **Live Ingestion Signal Radar:** Replaced the static empty state with dynamic, real-time slot projection across 6 dimensions:
  - 📍 **Destination** (e.g. *Tokyo & Kyoto & Japan*, *Dubai & Abu Dhabi*)
  - 🛫 **Origin** (e.g. *Mumbai (BOM)*, *DEL*)
  - 👥 **Party Size** (e.g. *Couple (2 travelers)*, *Couple + 2 children (4 travelers)*)
  - 📅 **Dates / Duration** (e.g. *October (10-day)*, *Dec 20 (6N)*)
  - 💰 **Budget** (e.g. *$18,000*, *INR 6-7 Lakhs*)
  - ✨ **Preferences / Constraints** (e.g. *Vegetarian meals*, *Ryokans*, *Private Tea Ceremony*)
* **One-Click Real-World Ingest Presets:** Added quick-test buttons directly above the Customer Message input (`[💬 WhatsApp]`, `[✉️ Email]`, `[🎙️ Phone Notes]`, `[✕ Clear]`) for instant verification of raw, messy messaging transcripts without manual copy-paste.
* **Streamlined Repeat-Traveler Recall Panel:** Relocated and unsloped `RepeatTravelerRecallCard` into clean, calm `#161b22` / `#0d1117` design tokens below the primary inputs, keeping the intake action front and center while preserving all test contracts (`data-testid="sample-data-badge"`).

---

## 2. Verification Receipts

* **Automated Unit Tests:**
  * `frontend/src/app/(agency)/workbench/__tests__/IntakeTab.test.tsx`: 10/10 passing (added regression coverage for live slot extraction & signal display).
  * `frontend/src/app/(agency)/workbench/__tests__/RepeatTravelerRecallCard.test.tsx`: 7/7 passing.
  * Entire `frontend/src/app/(agency)/workbench/__tests__/` suite: 21 test files, 146/146 tests passing.
* **Static Analysis:**
  * `eslint -c eslint.config.mjs`: Zero warnings or errors on modified files.
  * `tsc --noEmit`: 100% type-safe; zero compilation errors.
* **Browser Runtime & Screenshots:**
  * Authenticated session via `/api/auth/login`.
  * Captured live phone consultation ingestion: `workbench_live_intake_signal.png` (Jev triage: 358ms, slots extracted).
  * Captured messy WhatsApp chat scrub: `workbench_whatsapp_ingest.png` (Jev triage: 418ms, slots extracted).
