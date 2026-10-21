# trvl Producer Probe — 2026-10-20

Evidence for exploration topic 48 (External Ideas Sweep) and the **MCP sandbox producer DECIDE**.
Full write-up: `Docs/exploration/EXTERNAL_IDEAS_SWEEP_NONTRADITIONAL_2026-10-18.md` § "Probe addendum (2026-10-20)".

## What was run

- Binary: `trvl` v1.27.0 (released 2026-10-10), `darwin_arm64`, SHA-256 verified against the release `checksums.txt`
  (`38ad972c…df18`, match).
- **Isolation** (the README states cookies are read from the browser Keychain at launch by default, no flag turns it on):
  `HOME=/tmp/trvl-probe/home` · `TRVL_NO_BROWSER_COOKIES=1` · `TRVL_NO_TIER2_CDP=1` · `TRVL_NO_TELEMETRY=1` · `NO_TELEMETRY=1`.
  All state landed under the sandbox `~/.trvl`; nothing in the real home directory was read or written.
- Probe 1: `trvl flights BOM DXB 2027-02-10 --format json`
- Probe 2: `trvl hotels "Dubai" --checkin 2027-02-10 --checkout 2027-02-13 --format json`

## Files

| File | Content |
|---|---|
| `flights_BOM-DXB_2027-02-10_sample.json` | 5 priced + 2 unpriced of 158 results, full `provider_statuses` + `completeness` + `price_position` |
| `hotels_Dubai_2027-02-10_sample.json` | 3 of 135 hotels, full `provider_statuses` + `completeness` |
| `summary_stats.json` | Counts: confidence-label distribution, zero-price count, currency mix, provenance field list |

Full payloads (~580 KB) were not stored; rerun the commands above to regenerate.

## Headline numbers

- Flights: 158 results, 4/5 queried providers succeeded (`completeness.state = partial`, missing `wizzair` with a typed error + fix hint).
  Confidence labels: high 23 / medium 87 / **unrated 48** (30% of results carry no price — Air India / IX codeshare rows from Google Flights).
  27 prices are fractional INR = currency-converted estimates (Kiwi, Skiplagged), not native quotes.
- Hotels: 135 results, 7/13 providers succeeded; `booking` failed *because* the headless-browser fallback was disabled — status says so verbatim.
  Currencies in one result set: `AED, EUR, INR, USD, ""` — FX normalization is mandatory at any ingestion boundary.
- Room-rate provenance vocabulary worth adopting: `price_basis` (e.g. `tax_inclusive_total`), `price_confidence` (`verified`),
  `match_confidence` (`similar_room_match`), `taxes_fees_included`, `free_cancellation`, `refundable`, `cancellation_policy`.

## License / production eligibility

- trvl: **PolyForm Noncommercial 1.0** → research/reference only; not production-eligible for a commercial product without a separate license.
- LetsFG (the 2.1k⭐ alternative): code is **MIT** (MENTAL BALANCE sp. z o.o.); the hosted letsfg.co API is governed by its own ToS — check before any producer wiring.
