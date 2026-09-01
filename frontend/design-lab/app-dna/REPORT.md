# App design DNA — measured from the running product

**Captured:** 2026-08-31 01:26:22
**Signed in as:** `newuser@test.com` (agency `Test`, role `owner`)
**Trip resolved:** `trip_8b15e3f848f9`

Method: logged into the live app and read **computed styles and DOM** (not screenshots), so every number below is reproducible by re-running `python3 inspect-app-dna.py`.

## 1. What each screen is actually painted with

| Route | Body bg | Body text | Font | Gradients | blur() | Glow shadows | SMIL |
|---|---|---|---|---:|---:|---:|---:|
| `/` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 17 | 1 | 11 | 2 |
| `/overview` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 2 | 0 | 1 | 0 |
| `/trips` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 3 | 0 | 2 | 0 |
| `/inbox` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 1 | 0 | 0 | 0 |
| `/quotes` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 1 | 0 | 0 | 0 |
| `/settings` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 2 | 0 | 0 | 0 |
| `/insights` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 1 | 0 | 0 | 0 |
| `/suppliers` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 1 | 0 | 0 | 0 |
| `/trips/trip_8b15e3f848f9` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 1 | 0 | 0 | 0 |
| `/trips/trip_8b15e3f848f9/intake` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 1 | 0 | 0 | 0 |
| `/trips/trip_8b15e3f848f9/packet` | `rgb(13, 17, 23)` | `rgb(230, 237, 243)` | Rubik | 1 | 0 | 0 | 0 |

## 2. Theme A vs Theme B — measured, not assumed

Scored by luminance-distance from each canonical palette (DESIGN.md §2).

| Route | Dominant painted backgrounds | Verdict |
|---|---|---|
| `/` | `rgba(13,17,23,0.82)` `rgba(15,17,21,0.72)` `rgba(255,255,255,0.14)` `rgba(57,208,216,0.1)` | B light (A=0.935 B=0.988) |
| `/overview` | `rgb(22,27,34)` `rgb(28,33,40)` `rgb(88,166,255)` `rgb(13,17,23)` `rgba(139,148,158,0.08)` | A dark (A=1.0 B=0.966) |
| `/trips` | `rgba(255,255,255,0.02)` `rgba(210,153,34,0.12)` `rgb(13,17,23)` `rgb(22,27,34)` `rgb(88,166,255)` | A dark (A=0.948 B=0.943) |
| `/inbox` | `rgba(210,153,34,0.1)` `rgb(22,27,34)` `rgb(88,166,255)` `rgba(88,166,255,0.12)` `rgba(248,81,73,0.12)` | A dark (A=1.0 B=0.912) |
| `/quotes` | `rgb(13,17,23)` `rgb(22,27,34)` `rgb(88,166,255)` `rgb(28,33,40)` `rgb(33,38,45)` | A dark (A=0.999 B=0.967) |
| `/settings` | `rgb(13,17,23)` `rgb(22,27,34)` `rgb(88,166,255)` `rgb(28,33,40)` `rgb(63,185,80)` | A dark (A=1.0 B=0.943) |
| `/insights` | `rgb(22,27,34)` `rgb(15,17,21)` `rgb(88,166,255)` `rgb(13,17,23)` `rgb(28,33,40)` | A dark (A=1.0 B=0.968) |
| `/suppliers` | `rgb(22,27,34)` `rgb(13,17,23)` `rgba(35,134,54,0.2)` `rgb(88,166,255)` `rgb(28,33,40)` | A dark (A=0.972 B=0.966) |
| `/trips/trip_8b15e3f848f9` | `rgb(28,33,40)` `rgb(22,27,34)` `rgb(88,166,255)` `rgb(13,17,23)` `rgba(248,81,73,0.12)` | A dark (A=1.0 B=0.964) |
| `/trips/trip_8b15e3f848f9/intake` | `rgb(28,33,40)` `rgb(22,27,34)` `rgb(88,166,255)` `rgb(13,17,23)` `rgba(248,81,73,0.12)` | A dark (A=1.0 B=0.964) |
| `/trips/trip_8b15e3f848f9/packet` | `rgb(22,27,34)` `rgba(139,148,158,0.082)` `rgb(88,166,255)` `rgb(28,33,40)` `rgb(13,17,23)` | A dark (A=1.0 B=0.966) |

## 3. Live CSS custom properties vs DESIGN.md

Tokens observed live: **58**

### 3a. Theme A tokens that differ from DESIGN.md §2

| Token | DESIGN.md | Live value(s) |
|---|---|---|
| `--bg-canvas` | `#080a0c` | `#0d1117` |
| `--bg-surface` | `#0f1115` | `#161b22` |
| `--bg-elevated` | `#161b22` | `#1c2128` |
| `--bg-highlight` | `#1c2128` | `#222833` |
| `--bg-input` | `#111318` | `#0e1116` |

### 3b. Theme B tokens present live: **13/13**

## 4. Typography in use

| Font | elements |
|---|---:|
| Rubik | 1427 |
| JetBrains Mono | 88 |
| Sora | 10 |
| Outfit | 3 |

DESIGN.md §3 specifies **IBM Plex Sans** + **JetBrains Mono**. `layout.tsx` loads **Sora** + **Rubik**. Measured above is what actually rendered.

## 5. Navigation / information architecture

**`/`** — Product, Workflow, For agencies, Pricing, Sign in, Create workspace

**`/overview`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns

**`/trips`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns

**`/inbox`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns

**`/quotes`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns

**`/settings`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns

**`/insights`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns

**`/suppliers`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns

**`/trips/trip_8b15e3f848f9`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns, Open Trip Details

**`/trips/trip_8b15e3f848f9/intake`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns, Open Trip Details

**`/trips/trip_8b15e3f848f9/packet`** — New Inquiry, Overview, Lead Inbox, Quote Review, Trips in Planning, Quotes, Bookings, Documents, Payments, Suppliers, Insights, Audit, Knowledge Base, Settings, Seasonal Campaigns, Open Trip Details

## 6. Design-smell rollup (DESIGN.md §11 retirement targets)

| Pattern | Total across routes | DESIGN.md §11 says |
|---|---:|---|
| gradient backgrounds | 31 | retire (Theme B: none) |
| backdrop-filter (glassmorphism) | 1 | retire (Theme B: none) |
| glow shadows (blur >= 24px) | 14 | retire (Theme B: single subtle) |
| SMIL animations | 2 | not specified |
| infinite CSS animations | 16 | retire (Theme B: none) |

## 7. Border radius in use

| radius | elements |
|---|---:|
| 6px | 228 |
| 9999px | 184 |
| 8px | 125 |
| 12px | 102 |
| 4px | 79 |
| 999px | 21 |
| 2px | 10 |
| 30px | 8 |
| 16px | 6 |
| 20px | 2 |

DESIGN.md §11: Theme A marketing 22–24px -> Theme B 8px everywhere.
