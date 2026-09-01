# EX-DEMO-02 — Colloquial Extraction Gaps: Destination, Party, Dates (2026-08-31)

*Source briefs: `Docs/SIMULATED_PRODUCT_DEMO_TOOL_TASTER_2026-08-31.md` (findings DEMO-02, DEMO-03) + `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md` (EX-DEMO-02; covers DEMO-02, DEMO-03, DEMO-12, DEMO-13). Feeds IMP-02 (colloquial extraction) and IMP-07 (fixture wiring).*
*Method: static trace of `src/intake/extractors.py` + empirical in-process runs of the canonical extractors on the exact demo note. Read-only; no code, fixture, or data changes made.*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## 1. Executive Summary

1. **Destinations `-` is a pattern gap, not a data gap.** Geography DB knows Japan + all three cities (`is_known_destination("Japan")` → True, `src/intake/geography.py:78-104,463-492`), but the demo note is all-lowercase and uses verb-object phrasing ("want to do japan", "thinking tokyo + kyoto + osaka") that matches zero extraction patterns. `Destination Status: open @80%` is set at `src/intake/extractors.py:721` purely because the note contains the word "somewhere" (from "a cooking class somewhere").
2. **Party=1 is silent wrong data.** `me` fires the `\b(?:me|myself|i)\b → adults=1` pattern (`extractors.py:1248-1254`); "3 friends" is counted by nothing. The result is stamped `party_size=1 @0.9, authority=explicit_user` (`extractors.py:2040-2044`), which no validation check can flag (LOW_CONFIDENCE_FACT needs conf <0.5, `validation.py:213-221`).
3. **Dates missing is three sub-gaps**: no season handling ("next spring"), "late march" fails the month regex (requires an `in|during|for` prefix, `extractors.py:170-174`), and "10-12 days" (trip duration) has no extraction path or packet field at all. Bonus: "dates flexible **plus or minus** a week" also misses the flexibility phrase list (`extractors.py:1093-1098` knows `+/-` but not spelled-out "plus or minus").
4. **Two bonus silent defects found**: (a) "3.5k USD **each**" → budget_scope `unknown` → silently coerced to `total` (`extractors.py:1997-2006`) — per-person money presented as trip-total; (b) the destination string leaks into `soft_preferences` ("to do japan next spring", `extractors.py:1445-1455`) without ever being promoted to the destination field.
5. Golden fixtures confirm the eval/real-world gap (DEMO-13): all 20 budget-golden inputs use canonical phrasing ("trip to", "visit", "want to go to"); zero verb-object, zero lowercase-only notes, zero "me and N friends".
6. **Top 3 fixes**: (1) extend `_TRAVEL_VERB_DEST_RE` verb alternation ("do/hit/cover/wanna do") + accept `+`/`,`-separated city lists; (2) add group-size patterns (`N friends`, `N of us`, `the four of us`, `party of N`) **plus a PARTY_UNDERDETECTED validation warning**; (3) add season + "late <month>" + trip-duration parsing to `_extract_dates`, and "plus or minus" / "dates flexible" to `_extract_date_flexibility`. Estimated 3–4.5 agent-days total including fixture wiring and the required 2 review cycles for the contract-affecting pieces.

---

## 2. Per-Field Gap Analysis (evidence-cited)

### 2.1 Destinations — verb-object phrasing + lowercase text defeat both passes

The destination extractor has two passes:

**Pass 1 — capitalized proper-noun regex** (`_DESTINATION_RE`, `src/intake/extractors.py:109-111`):
```python
_DESTINATION_RE = re.compile(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b")
```
It only matches `Capitalized` tokens. The demo note is entirely lowercase ("want to do japan", "thinking tokyo + kyoto + osaka") → **zero matches** (empirically verified: `DESTINATION_RE matches: []`).

**Pass 2 — travel-verb fallback** (`_TRAVEL_VERB_DEST_RE`, `extractors.py:315-319`; consumed in the fallback loop at `extractors.py:695-719` alongside `_HINGLISH_DEST_RE` `:323-326` and `_ORIGIN_DEST_RE` `:330-333`):
```python
_TRAVEL_VERB_DEST_RE = re.compile(
    r"(?:want to go|go to|travel to|visit|flying to|trip to|holiday in|vacation in"
    r"|planning to go to|planning to visit|head to|going to)\s+"
    r"([a-z]+(?:\s+[a-z]+)*)",
)
```
The verb alternation covers "trip to X" / "visit X" / "go to X" — but **not**:
- "want to **do** japan" — "do" is absent from the alternation (and ironically `do` is in `_STOP_WORDS`, `extractors.py:66`, and in `_RELATION_WORDS`-adjacent guardrails for candidates);
- "**hitting** bali" / "**covering** tokyo" / "**check out** X" — colloquial verbs absent;
- "**thinking** tokyo" — the hedge regex `_HEDGING_RE` (`extractors.py:223-226`) requires `thinking about` (with "about"); the note's bare "thinking tokyo + kyoto + osaka" does not match;
- `+` / comma city lists — no pattern anywhere handles "tokyo + kyoto + osaka" as a multi-destination set. The only multi-candidate path, `_OR_DESTINATION_RE` (`extractors.py:133-135`), requires `Capitalized or|and Capitalized`, so lowercase "tokyo and kyoto" also fails (verified).

Empirically on the demo note both passes return nothing, and the final fallback at `extractors.py:721` fires:
```python
return [], "open" if ("somewhere" in text_lower or "any" in text_lower) else "undecided", None
```
→ `([], 'open', None)` **because the note contains "somewhere"** — from the unrelated sentence "we also wanna do a cooking class somewhere". The packet then records `destination_status='open' @0.8, authority=explicit_user` at `extractors.py:1895-1898` (evidence string: "Derived from destination text"). This also answers DEMO-11 partially: the `explicit_user` authority here reflects that the *status* was derived from the user's own text, not that a destination was captured.

**Ground truth check**: `is_known_destination("Japan")` → True (`_COUNTRY_DESTINATIONS`, `geography.py:78-104`; `is_known_destination`, `geography.py:463-492`), `is_known_city("Tokyo"/"Kyoto"/"Osaka")` → all True. One near-miss worth noting: `_MAYBE_RE` (`extractors.py:147`) does capture "maybe late" from the note, but `is_known_destination("Late")` is False, so it correctly declines — the geography gate prevented a false positive, it just had nothing correct to accept.

**Leak observed**: "want to do japan next spring" is captured — as `soft_preferences: ['to do japan next spring']` via `(?:want|prefer|like|interested\s+in)\s+([^.,]+)` (`extractors.py:1445-1455`). The signal exists in the packet; nothing promotes it to `destination_candidates`.

### 2.2 Party — "me" fires, "3 friends" is invisible

`_extract_party` (`extractors.py:1238-1357`) counts via:
- `_FAMILY_PATTERNS` (`:1248-1254`) — first entry is `\b(?:me|myself|i)\b → adults + 1`. In "me and 3 friends", **"me" contributes adults=1** and nothing else contributes → `party_size=1, {'adults': 1}` (empirically verified on the full note).
- There is **no pattern** for "N friends", "N of us", "the four of us". "friend" appears in `_RELATION_WORDS` (`extractors.py:50-55`) but that set is only used to reject destination candidates, never to count people.
- `_GROUP_SIZE_RE` (`extractors.py:261`) covers `family|group … of N` only — "party of 4" → 0 (verified), "group of 4 friends" → 4 (verified, works).
- `_PEOPLE_RE` (`extractors.py:249-252`) covers `N people|persons|pax|travelers` — not matched by any demo phrasing.

The slot is then written **only when > 0** (`extractors.py:2040-2044`) at **confidence 0.9, `AuthorityLevel.EXPLICIT_USER`**, evidence = the number itself (`"1"`). Two consequences:
- When a group is detected as 1, the packet asserts wrong data at high confidence (the demo case).
- When phrasing yields 0 ("the four of us", verified → `party_size 0, {}`), the field is silently absent — no warning distinguishes "user never said" from "we failed to parse".

Validation cannot catch either case: the only party-relevant check is `LOW_CONFIDENCE_FACT` (< 0.5, `src/intake/validation.py:213-221`), and party is stamped 0.9. There is no text-vs-slot cross-check anywhere in `validation.py`.

### 2.3 Dates — season, "late <month>", duration, and flexibility-marker gaps

`_extract_dates` (`extractors.py:728-814`) is a fixed ladder (ISO range `:211-213` → month-day range `:201-208` → "9th-14th feb" `:193-198` → "this weekend" `:153-156` → "June-July 2026" window `:157-163` → "after July 10" `:175-181` → "in March 2026" `:164-169` → "in July" `:170-174` → "around March" `:182-185`). Against the note:

- **"maybe late march"** → None. `_SINGLE_MONTH_NO_YEAR_RE` (`extractors.py:170-174`) requires a leading `in|during|for`; the note has "late march **for** the cherry blossoms" (the preposition trails, doesn't lead). No `late/early/mid <month>` modifier support exists anywhere.
- **"next spring"** → None. There is no season vocabulary (`spring/summer/fall/autumn/winter`, `next month/year`) in any date pattern.
- **"10-12 days"** → None, and correctly so as a *date*, but there is **no trip-duration extractor at all**: `rg "duration"` over `src/intake/extractors.py` finds only an urgency `days_until` derived signal (`extractors.py:2515-2517`); `packet_models.py` has no `trip_duration` field (only `days_since_last_reply`, `packet_models.py:287`); `QUOTE_READY` (`validation.py:52-59`) has no duration slot. A guest can state trip length and it is structurally unrepresentable.
- **"in march 2027"** works (verified → `('in march 2027', None, None, 'flexible')`), and **"we have 10 days in april"** works via the "in april" branch — the gap is specifically the colloquial forms.
- **Bonus — flexibility marker miss**: the note says "dates flexible **plus or minus** a week", yet `_extract_date_flexibility` (`extractors.py:1085-1104`) returned **None** on the full note. Its phrase list knows `"+/-"`, `"+-"`, `"plus minus"` but not spelled-out `"plus or minus"`; and it knows `"flexible dates"`/`"dates are flexible"` but not the inverted `"dates flexible"` word order used in the note. Verified contrast: "dates flexible, +/- one week" → `"flexible"`. The user explicitly granted ±1 week and the packet records nothing — this is the same silent-data-loss class as party.

### 2.4 Budget (captured, but with a silent scope error)

Budget amount/currency are correct: `min=3500, max=3500, USD` (the `k` multiplier path, `extractors.py:899-914`). However:
- `_extract_budget_scope` (`extractors.py:1119-1129`) recognizes `per person`/`per head`/`per night`/`a day`/total-markers — **not "each"**. So "3.5k USD each" → `unknown`, and `_extract_from_freeform` then **coerces unknown → "total"** when any budget exists (`extractors.py:1997-2006`). Verified: "budget 3.5k USD each" → `unknown` → packet `budget_scope='total' @0.7`. The packet asserts trip-total for what is explicitly per-person money — a 4× commercial error waiting downstream (and it compounds with the Party=1 bug).
- "not sure if that includes flights" produced no ambiguity entry (only a destination `value_vague` ambiguity was recorded) — the flights-inclusive question is unmodeled.

---

## 3. Empirical Verification (read-only, in-process)

Commands: `uv run python -c "..."` calling the canonical extractor functions directly. **Side-effect audit before running**: `record_seen_city` (the only geographic persistence, `geography.py:305-345` → writes `data/accumulated_cities.json`) is exported (`src/intake/__init__.py:75,145`) but **never called anywhere in the extraction path** (`rg` over `src/intake/*.py` confirms only definitions/exports). All helpers are pure regex-over-text plus read-only dataset loads. Nothing was written to the DB, `data/`, or any store.

**Full-pipeline run on the exact demo note** (`ExtractionPipeline().extract([SourceEnvelope.from_freeform(note)])`):

| Slot | Value | Conf | Authority |
|------|-------|------|-----------|
| destination_candidates | `[]` | 0.5 | explicit_user |
| destination_status | `open` | 0.8 | explicit_user |
| party_size | `1` | 0.9 | explicit_user |
| party_composition | `{'adults': 1}` | 0.85 | explicit_user |
| budget_min/max | `3500 / 3500` | 0.9 | explicit_user |
| budget_scope | `total` (should be per_person) | 0.7 | explicit_user |
| origin_city | `SF` | 0.9 | explicit_user |
| date_window, date_start, date_end, date_flexibility, trip_purpose | **absent** | — | — |
| soft_preferences | `['to do japan next spring']` (leak) | 0.8 | explicit_user |
| hard_constraints | `['cable cars please', 'idea of the name' (false positive from "no idea of the name", negation regex `extractors.py:1436`)]` | 0.8 | explicit_user |

This exactly reproduces the demo UI observation (Destination `-`, Status open @80%, Party 1, Budget ✓, Dates/Purpose missing → blocked on Travel Dates + Trip Purpose per `INTAKE_MINIMUM`/`QUOTE_READY`, `validation.py:46-59`).

**Targeted probes (pattern boundaries):**

| Input | Result |
|-------|--------|
| `me and 3 friends want to do japan` | party 1 `{'adults': 1}` |
| `the four of us are going somewhere` | party 0 `{}` (field silently absent) |
| `4 of us want a beach trip` | party 0 `{}` |
| `party of 4 to japan` | party 0 `{}` |
| `group of 4 friends to japan` | party 4 (works) |
| `me and my wife and 2 friends` | party 2 (wife counted; friends invisible) |
| `want to do japan` / `hitting bali` / `covering tokyo and kyoto` / `thinking tokyo + kyoto + osaka` | all `([], 'undecided', None)` |
| `trip to japan` / `want to visit japan` | `(['Japan'], 'definite', …)` (works) |
| `next spring, maybe late march` | dates None, flex None |
| `dates flexible plus or minus a week` | flex **None** |
| `dates flexible, +/- one week` | flex `flexible` |
| `budget 3.5k USD each` | scope `unknown` → packet coerces to `total` |

---

## 4. Phrasing-Gap Catalog (new eval cases)

| # | Field | Phrasing (from demo + natural variants) | Expected extraction | Today's result |
|---|-------|------------------------------------------|--------------------|----------------|
| D1 | destination | "want to do japan" | `["Japan"]`, definite | `[]`, undecided |
| D2 | destination | "hitting bali next month" | `["Bali"]`, definite | `[]`, undecided |
| D3 | destination | "covering tokyo and kyoto" | `["Tokyo","Kyoto"]` | `[]`, undecided |
| D4 | destination | "thinking tokyo + kyoto + osaka" | 3 cities (modeling per §7) | `[]`, undecided |
| D5 | destination | "wanna do a cooking class somewhere" (verb-object non-place) | no destination; status not promoted to open from this clause alone | — (currently the source of the false "open") |
| D6 | destination | "we wanna check out seoul" | `["Seoul"]` | `[]`, undecided |
| P1 | party | "me and 3 friends" | party 4 (1 self + 3 friends) | 1 |
| P2 | party | "4 of us want a beach trip" | party 4 | absent |
| P3 | party | "the four of us" | party 4 | absent |
| P4 | party | "party of 4" | party 4 | absent |
| P5 | party | "me and my wife and 2 friends" | party 4 | 2 |
| P6 | party | "me and 3 friends" + no other count | **warning** PARTY_UNDERDETECTED if slot=1 | silent 1 @0.9 |
| T1 | dates | "next spring" | season window (Mar–May next year), flexible | absent |
| T2 | dates | "late march" (no prefix) | March window, "late" qualifier preserved | absent |
| T3 | dates | "10-12 days" | trip duration 10–12 | absent (no field) |
| T4 | dates | "dates flexible plus or minus a week" | date_flexibility = flexible (±7d) | flex None |
| T5 | dates | "flexible plus or minus a week" combined with "late march" | window + flexibility | both absent |
| B1 | budget scope | "budget around 3.5k USD each" | scope per_person | scope total (coerced) |
| B2 | budget ambiguity | "not sure if that includes flights" | budget flights-inclusive ambiguity flagged | nothing |

---

## 5. Proposed Fixtures (draft — NOT written to data/fixtures/)

Schema mirrors `data/fixtures/budget/golden_dataset.json` (`fixture_id`, `raw_input`, `expected_extracted_fields`, `tags`), so it can drop in beside it and wire into the audit extraction gate (`src/evals/audit/manifest.yaml` `extraction` category → `_run_extraction_baseline()` in `snapshot.py`, per IMP-07):

```json
[
  {
    "fixture_id": "colloq_dest_verb_object_001",
    "description": "Verb-object destination: 'do X' with fully lowercase text",
    "difficulty": "hard",
    "raw_input": "hey! me and 3 friends want to do japan next spring, maybe late march for the cherry blossoms.",
    "expected_extracted_fields": {
      "destination_candidates": ["Japan"],
      "destination_status": "definite"
    },
    "expected_field_count": 2,
    "tags": ["colloquial", "verb_object", "lowercase_text", "destination"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_dest_city_set_001",
    "description": "Plus-separated city list with implied country",
    "difficulty": "hard",
    "raw_input": "thinking tokyo + kyoto + osaka, 10-12 days.",
    "expected_extracted_fields": {
      "destination_candidates": ["Tokyo", "Kyoto", "Osaka"],
      "destination_country": "Japan"
    },
    "expected_field_count": 2,
    "tags": ["colloquial", "city_set", "country_plus_cities", "destination"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_party_friends_001",
    "description": "Group size via 'me and N friends'",
    "difficulty": "hard",
    "raw_input": "me and 3 friends want a beach trip",
    "expected_extracted_fields": {
      "party_size": 4,
      "party_composition": {"adults": 4}
    },
    "expected_field_count": 2,
    "tags": ["colloquial", "group_size", "party"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_party_of_us_001",
    "description": "Group size via 'N of us' and 'the four of us'",
    "difficulty": "hard",
    "raw_input": "the four of us are looking at 4 of us doing a greek island hop",
    "expected_extracted_fields": {
      "party_size": 4
    },
    "expected_field_count": 1,
    "tags": ["colloquial", "group_size", "party"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_party_mixed_001",
    "description": "Self + spouse + friends must count all named companions",
    "difficulty": "hard",
    "raw_input": "me and my wife and 2 friends want to do japan",
    "expected_extracted_fields": {
      "party_size": 4
    },
    "expected_field_count": 1,
    "tags": ["colloquial", "group_size", "mixed_composition", "party"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_dates_season_001",
    "description": "Season window with late-month qualifier",
    "difficulty": "hard",
    "raw_input": "want to do japan next spring, maybe late march for the cherry blossoms",
    "expected_extracted_fields": {
      "date_window": "next spring (Mar-May), late march preferred",
      "date_confidence": "flexible"
    },
    "expected_field_count": 2,
    "tags": ["colloquial", "relative_dates", "season", "dates"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_dates_flex_001",
    "description": "Spelled-out flexibility with numeric window",
    "difficulty": "medium",
    "raw_input": "dates flexible plus or minus a week",
    "expected_extracted_fields": {
      "date_flexibility": "flexible"
    },
    "expected_field_count": 1,
    "tags": ["colloquial", "flexibility_marker", "dates"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_dates_duration_001",
    "description": "Trip duration stated as day range without dates",
    "difficulty": "hard",
    "raw_input": "thinking tokyo + kyoto + osaka, 10-12 days",
    "expected_extracted_fields": {
      "trip_duration_days": {"min": 10, "max": 12}
    },
    "expected_field_count": 1,
    "tags": ["colloquial", "trip_duration", "dates"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_budget_each_001",
    "description": "Per-person budget via 'each' + flights-inclusiveness question",
    "difficulty": "medium",
    "raw_input": "budget around 3.5k USD each, not sure if that includes flights",
    "expected_extracted_fields": {
      "budget_min": 3500,
      "budget_currency": "USD",
      "budget_scope": "per_person",
      "budget_ambiguity": "flights_inclusiveness_unknown"
    },
    "expected_field_count": 4,
    "tags": ["colloquial", "budget_scope", "ambiguity", "budget"],
    "document_type": "freeform_note"
  },
  {
    "fixture_id": "colloq_full_note_001",
    "description": "Exact Tool-Taster demo note — end-to-end regression anchor",
    "difficulty": "hard",
    "raw_input": "hey! me and 3 friends want to do japan next spring, maybe late march for the cherry blossoms. flying from SF. we are all pretty active, one friend is vegetarian. budget around 3.5k USD each, not sure if that includes flights. thinking tokyo + kyoto + osaka, 10-12 days. one of us is terrified of heights so no cable cars please. we saw this amazing ryokan on tiktok, no idea of the name. dates flexible plus or minus a week. we also wanna do a cooking class somewhere. thx!!",
    "expected_extracted_fields": {
      "destination_candidates": ["Tokyo", "Kyoto", "Osaka"],
      "destination_country": "Japan",
      "origin_city": "SF",
      "party_size": 4,
      "budget_min": 3500,
      "budget_currency": "USD",
      "budget_scope": "per_person",
      "date_window": "next spring, late march",
      "date_flexibility": "flexible",
      "trip_duration_days": {"min": 10, "max": 12},
      "meal_preferences": "vegetarian",
      "hard_constraints": ["no cable cars"]
    },
    "expected_field_count": 12,
    "tags": ["colloquial", "end_to_end", "demo_regression", "full_note"],
    "document_type": "freeform_note"
  }
]
```

Naming note for the implementing agent: propose landing as `data/fixtures/extraction/colloquial_golden.json` (separate file so the existing 50-case `golden_dataset.json` F1 baseline stays comparable) — pending Pranay's call in §9 Q6.

---

## 6. Fix Design (canonical extractors only — no forked pipeline)

### 6.1 Destination (`src/intake/extractors.py`)

1. **Extend the verb alternation** in `_TRAVEL_VERB_DEST_RE` (`extractors.py:315-319`) with `do|wanna do|hit|hitting|cover|covering|check out|keen on|down for`. Guard: the destination-validation gate (`_is_valid_destination_candidate`, `extractors.py:524-556`) already requires `is_known_destination(...)` for lowercase spans, so "do a cooking class" cannot become a destination — the geography gate is the false-positive backstop. Add a test proving "do a cooking class somewhere" yields no destination.
2. **Bare "thinking X" hedge**: extend `_HEDGING_RE` (`extractors.py:223-226`) with a variant allowing `thinking` without `about`, but only accept the captured span when `is_known_destination` is True (same guard the existing hedge branch already applies at `extractors.py:626-630`).
3. **`+`/`,` city sets**: in `_extract_destination_candidates` (`extractors.py:559-721`), add a list-separator pass: split on `+` (and `,`/`and` between known-city tokens), validate each part with `is_known_destination`, and return them as multiple candidates. This is where the country+city resolution hook belongs (§7).
4. **"open"-status trigger tightening**: the bare `"somewhere" in text_lower` check at `extractors.py:721` is too coarse — "a cooking class somewhere" is an activity clause, not destination intent. Restrict the "open" trigger to `somewhere` in destination-ish positions (e.g., `somewhere (warm|tropical|...|with|for)` via the existing `_SOMEWHERE_DEST_RE`) or require absence of any activity-noun context; at minimum add a test for the demo note asserting the note's `somewhere` does not alone produce `open`.

### 6.2 Party (`src/intake/extractors.py` + `src/intake/validation.py`)

1. **New group patterns** in `_extract_party` (`extractors.py:1238-1357`), all writing into `composition["adults"]` and evaluated as max-fallbacks like the existing `family_group_size` path (`:1334-1335`):
   - `(?:me|us)\s+(?:and|plus)\s+({_COUNT_TOKEN_RE})\s+friends?` → self + N
   - `({_COUNT_TOKEN_RE}|one|two|…|ten)\s+of\s+us` (incl. `the four of us`) → N
   - extend `_GROUP_SIZE_RE` (`extractors.py:261`) from `family|group` to also cover `party`
   - bare `({_COUNT_TOKEN_RE})\s+friends?` → N (counts companions; combined with the self pattern this fixes P5)
2. **Validation warning (data-loss-prevention compliant — warn, never skip silently; repo Pattern 5)**: add `PARTY_UNDERDETECTED` to `validate_packet` (`src/intake/validation.py:96-259`). Fire when a `party_size` fact ≤ 1 **and** the source text contains group signals (`\b\d+\s+friends?\b`, `\bof\s+us\b`, `\bparty\s+of\b`, `\bcouple\s+of\s+friends\b`). Implementation shape: `_extract_party` should return a `group_signals: List[str]` alongside size (raw phrases it saw but could not convert), carried onto the envelope result; validation compares signals vs slot. Symmetric second warning: `PARTY_UNPARSED_GROUP_PHRASING` when signals exist but no `party_size` fact was set at all (the "the four of us" silent-absent case). Warnings surface through the existing `PacketValidationReport.warnings` (`validation.py:82-93`) — visibility decision in §9 Q4.

### 6.3 Dates (`src/intake/extractors.py`)

1. **Season parser**: new pre-month step in `_extract_dates` (`extractors.py:728+`): `next <season>` / `this <season>` / bare `<season>` → year-resolved month range (spring=Mar–May, summer=Jun–Aug, fall/autumn=Sep–Nov, winter=Dec–Feb, hemisphere-neutral default northern; note in evidence text). Returns the raw phrase with `date_confidence="flexible"` — consistent with how "in July" already degrades gracefully (`extractors.py:803-806`).
2. **`late|early|mid <month>`**: extend `_SINGLE_MONTH_NO_YEAR_RE` (`extractors.py:170-174`) / add a modifier-capturing variant; keep the modifier in `date_window` raw text (e.g., "late march") rather than inventing day-level precision — the packet's own convention keeps raw windows when ends are unknown (`extractors.py:785-794`).
3. **Trip duration**: new `_extract_trip_duration(text) → Optional[Dict]` for `N-M days`, `N days`, `N-night`, `two weeks`; store as a new `trip_duration` packet fact (or `trip_duration_days` min/max). **This is a contract addition** (new fact name + optional `QUOTE_READY` candidacy) → triggers the repo's mandatory 2 review cycles (AGENTS.md, Code Review Iteration Pattern) and a decision from Pranay (§9 Q3).
4. **Flexibility phrases**: add `"plus or minus"` and `"dates flexible"` to the lists in `_extract_date_flexibility` (`extractors.py:1085-1104`). Optionally capture the numeric window ("±1 week") into the flexibility value.

### 6.4 Budget scope (`src/intake/extractors.py`)

Add `each` / `apiece` / `per head each` markers to `_extract_budget_scope` (`extractors.py:1119-1129`) so "3.5k USD each" → `per_person` instead of the current silent coercion at `extractors.py:1997-2006`. For "not sure if that includes flights", add a `Normalizer.detect_ambiguities` rule (budget field family) emitting a `flights_inclusiveness_unknown` ambiguity — following the existing ambiguity-synthesis pattern (`extractors.py:1919-1935`).

---

## 7. Multi-Destination Open Question (DEMO-12 — explicit decision needed)

Current model is a **flat list + status**: `destination_candidates: List[str]` with `destination_status ∈ {definite, semi_open, open}` (`extractors.py:559-721`, `packet_models.py`). Two modeling problems surface with the demo note:

1. **Country + city sets.** "japan" + "tokyo + kyoto + osaka" would (after the §6.1 fix) yield a flat `["Japan", "Tokyo", "Kyoto", "Osaka"]` where Japan is a *container* of the other three. Options:
   - **(a) Containment resolution**: detect via `get_city_country` (`geography.py:436-460`) that all cities ∈ one country present in the candidate list, then keep the country as a separate `destination_country` fact (or a scope hint) and cities as candidates. Pros: no schema break; country survives as routing/visa signal; cities feed quoting. Cons: new derived-ish fact needs classification (fact vs derived per `validation.py:27-43`).
   - **(b) Hierarchical value**: `destination_candidates = [{"country": "Japan", "cities": [...]}]` — cleanest semantically, but breaks every consumer of the flat string list (strategy, decision, frontend types) — high blast radius, not recommended now.
   - Recommendation: **(a)**.
2. **Status semantics conflate "or" with "+".** Today, ≥2 candidates forces `semi_open` (`extractors.py:689-690`) plus a synthesized `unresolved_alternatives` ambiguity (`extractors.py:1924-1935`). That is correct for "bali **or** lombok" but wrong for "tokyo **+** kyoto **+** osaka", which is a committed multi-city route, not an open question. Proposed: a separator-aware status — `+`/`and`-joined validated cities → `definite` (multi) with no ambiguity; `or`/hedged → `semi_open` with the ambiguity. This needs Pranay's sign-off because `semi_open` may have downstream strategy/decision meaning (§9 Q2).

---

## 8. Effort Estimate

| Work item | Estimate |
|-----------|----------|
| §6.1 destination verbs + city-set pass + "open" tightening + tests | 0.5–1.0 day |
| §6.2 party patterns + `group_signals` + 2 validation warnings + tests | 0.5–0.75 day |
| §6.3 season/"late month"/flexibility phrases + tests | 0.5–0.75 day |
| §6.3 trip_duration fact (contract change → 2 review cycles per repo discipline) | 0.75–1.0 day |
| §6.4 budget scope "each" + flights ambiguity + tests | 0.25 day |
| Fixtures (§5) + audit-manifest wiring (IMP-07) + golden-baseline re-run via `scripts/run_backend_tests.sh` | 0.5 day |
| **Total** | **~3–4.5 agent-days** |

Sequencing: §6.1/§6.2/§6.4 are additive and independent (can land in parallel); `trip_duration` should be sequenced after Pranay answers §9 Q3.

---

## 9. Open Questions for Pranay

1. **Multi-destination model** (§7): approve option (a) — flat city candidates + separate `destination_country` fact via containment resolution? Or defer country modeling entirely for IMP-02 (cities-only) and file country handling separately?
2. **Status semantics**: should `+`/`and`-joined city sets yield `definite` (multi) with *no* `unresolved_alternatives` ambiguity, reserving `semi_open` for genuine "or"/hedged alternatives? Any downstream consumer of `semi_open` that would break?
3. **`trip_duration` contract**: add as a new packet fact (my recommendation — it's explicit user data currently unrepresentable), and should it join `QUOTE_READY` or stay informational? This sets whether 2 review cycles + frontend type updates are in scope.
4. **Party-warning surfacing**: should `PARTY_UNDERDETECTED` / `PARTY_UNPARSED_GROUP_PHRASING` warnings render in the blocked banner (folding into the DEMO-09/EX-DEMO-06 specificity work) or only in the Trip Details packet table?
5. **Budget-scope coercion**: keep the current "unknown → total" default when a budget exists (`extractors.py:1998-2001`), but only after "each" is recognized? Or stop coercing and leave scope `unknown` + ambiguity-flagged when no marker is present (more honest, but changes golden budget expectations)?
6. **Fixture placement**: new file `data/fixtures/extraction/colloquial_golden.json` (recommended — keeps the existing 50-case F1 baseline comparable) vs extending `data/fixtures/extraction/golden_dataset.json` in place?
7. **False-positive cleanup scope**: `hard_constraints` currently captures junk ("idea of the name" from "no idea of the name", negation regex `extractors.py:1436`) — fix in IMP-02's pass or track separately? It's the same blast radius (one regex + guard) but different field.

---

*Evidence file map: `src/intake/extractors.py` (destination `:109-135,147-226,315-333,425-556,559-721`; dates `:144-213,728-814`; flexibility `:1085-1104`; budget scope `:1119-1129` + coercion `:1997-2006`; party `:240-261,1238-1357`; slot writes `:1863-2054`; intent leak `:1445-1455`; status/stamps `:1888-1898,2040-2044`), `src/intake/geography.py` (`:44-107,263-302,436-492`), `src/intake/validation.py` (`:17-65,96-259`), `src/intake/packet_models.py:304-319`, `data/fixtures/budget/golden_dataset.json`, `data/fixtures/extraction/golden_dataset.json`, `src/evals/audit/manifest.yaml`.*
