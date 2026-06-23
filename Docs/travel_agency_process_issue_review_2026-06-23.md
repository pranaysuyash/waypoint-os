# Travel Agency Process Issue Review

Date: 2026-06-23

## Issue

The live workbench treated a global corporate request with the phrasing `18-traveler` as if party size was missing, even though the count was explicitly present in the customer message.

## Evidence

- Live authenticated browser replay on the main workbench processed:
  - `Lagos agency handling a 18-traveler corporate offsite from Lagos to Cape Town in September 2026. Budget NGN 15m, needs visa support, rooming list, airport transfers, and a fast internal approval-ready summary.`
- Before the fix, the Risk Review tab showed:
  - `WAITING ON CUSTOMER`
  - `Please provide party size to generate a quote.`
- The same message is a valid 18-person group request.

## Root Cause

`src/intake/extractors.py::_extract_party()` recognized space-separated forms like `18 travelers` but did not accept the hyphenated variant `18-traveler`.

The party parser therefore left `party_size` unset, which triggered the downstream incomplete-intake blocker.

## Fix

- `src/intake/extractors.py`
  - Expand explicit traveler-count parsing to accept hyphenated and dash-separated phrasing.
  - Keep the same logic for plural `travelers`, `travellers`, `people`, `persons`, and `pax`.
- `tests/test_extraction_fixes.py`
  - Added a regression test for the exact live request phrasing.

## Validation

- Targeted tests
  - `3 passed`
- Direct parser check
  - `party_size = 18`
- Live browser verification
  - The same workbench request now promotes to a durable trip with `18 pax`
  - The saved trip page shows `Cape Town business trip`
  - The trip details preserve `₦15,000,000` and procurement-sharing guidance

## Remaining Follow-Up

- Keep adding real operator phrasing to the extractor regression set.
- Global-market phrases should keep working even when they use punctuation-heavy shorthand from WhatsApp or call summaries.
