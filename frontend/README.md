# Travel Agency Agent — Frontend

Next.js frontend for the Travel Agency Agent system. The frontend communicates with the Python spine via a persistent FastAPI service.

## Architecture

```
Browser → Next.js (localhost:3000) → spine_api (FastAPI, port 8000) → run_spine_once
                                                             (persistent process,
                                                              modules pre-loaded)
```

- **Frontend**: Next.js 16.2.3 with App Router, TypeScript, Zustand
- **Backend**: Python 3.13+ via `spine_api` FastAPI service (persistent process)
- **State**: Zustand store for workbench state (no rerun on tab switch)

## Prerequisites

- Node.js 18+
- Python 3.13+
- Virtual environment at `.venv/` in project root

## Quick Start

### 1. Start the Frontend

```bash
cd /Users/pranay/Projects/travel_agency_agent/frontend
npm install  # Only needed first time
npm run dev
```

Open **http://localhost:3000/workbench** in your browser.

### Dev Runtime Consistency (Recommended)

Next.js already provides Fast Refresh in `npm run dev` (no `nodemon` needed for frontend).

If you ever see stale UI (e.g., old nav labels in one window):

```bash
cd /Users/pranay/Projects/travel_agency_agent/frontend
npm run dev:doctor
npm run dev:reset
npm run dev
```

This ensures a single clean runtime on `:3000` and clears stale `.next` artifacts.

### 2. Verify APIs Work

```bash
# List scenarios
curl http://localhost:3000/api/scenarios

# Run a spine test
curl -X POST http://localhost:3000/api/spine/run \
  -H "Content-Type: application/json" \
  -d '{"raw_note":"Family of 4 to Singapore","stage":"discovery","operating_mode":"normal_intake","strict_leakage":false}'
```

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── spine/run/route.ts     # POST /api/spine/run (BFF → spine_api)
│   │   │   └── scenarios/            # GET /api/scenarios, /api/scenarios/[id]
│   │   ├── workbench/                 # Main workbench UI
│   │   │   ├── page.tsx              # 5-tab workbench
│   │   │   ├── IntakeTab.tsx         # Input form + Run Spine
│   │   │   ├── PacketTab.tsx          # Packet inspection
│   │   │   ├── DecisionTab.tsx        # Decision state + blockers
│   │   │   ├── StrategyTab.tsx        # Internal vs traveler-safe
│   │   │   └── SafetyTab.tsx          # Leakage + assertions
│   │   └── globals.css               # Design tokens
│   ├── lib/
│   │   ├── spine-client.ts           # HTTP client → spine_api (port 8000)
│   │   ├── scenario-loader.ts        # Scenario file loader
│   │   └── design-system.ts          # State color constants
│   ├── stores/
│   │   └── workbench.ts             # Zustand store (19 state keys)
│   └── types/
│       └── spine.ts                 # TypeScript types matching Python
└── package.json
```
frontend/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── spine/run/route.ts     # POST /api/spine/run
│   │   │   └── scenarios/            # GET /api/scenarios, /api/scenarios/[id]
│   │   ├── workbench/                 # Main workbench UI
│   │   │   ├── page.tsx              # 5-tab workbench
│   │   │   ├── IntakeTab.tsx         # Input form + Run Spine
│   │   │   ├── PacketTab.tsx          # Packet inspection
│   │   │   ├── DecisionTab.tsx        # Decision state + blockers
│   │   │   ├── StrategyTab.tsx        # Internal vs traveler-safe
│   │   │   └── SafetyTab.tsx          # Leakage + assertions
│   │   └── globals.css               # Design tokens
│   ├── lib/
│   │   ├── spine-client.ts           # HTTP client → spine_api (port 8000)
│   │   ├── scenario-loader.ts        # Scenario file loader
│   │   └── design-system.ts          # State color constants
│   ├── stores/
│   │   └── workbench.ts             # Zustand store (19 state keys)
│   └── types/
│       └── spine.ts                 # TypeScript types matching Python
└── package.json
```

## Routes

| Route | Description |
|-------|-------------|
| `/workbench` | Main workbench with 5 tabs (Intake, Packet, Decision, Strategy, Safety) |
| `/api/spine/run` | POST — Run spine with input payload |
| `/api/scenarios` | GET — List all scenario fixtures |
| `/api/scenarios/[id]` | GET — Load specific scenario (e.g. `/api/scenarios/clean-family-booking`) |
| `/api/version` | GET — Frontend runtime fingerprint (version/env/gitSha) |

### Runtime Fingerprint

The sidebar brand/status now reads from `/api/version`, which is sourced from `package.json` and runtime env.
This prevents stale-window ambiguity by showing what runtime you are actually connected to.

Brand hierarchy in the app shell is now explicit and stable:
- Product: `Waypoint OS`
- Agency: `profile.agency_name`
- Optional descriptors: `profile.sub_brand` and `profile.plan_label`

This avoids accidental-looking renames by separating product identity from tenant branding.

Optional env for richer traceability:

```bash
NEXT_PUBLIC_GIT_SHA=<short-or-full-commit-sha>
```

## Owner Insights Visualizations

The Owner Insights page includes three comprehensive data visualizations:

### 1. Conversion Funnel (Pipeline Funnel)
Shows pipeline stage conversion rates with:
- Trip count by stage (horizontal bar chart)
- Conversion percentages between consecutive stages
- Visual funnel effect indicating drop-off at each stage

Implementation:
- Component: `src/components/visual/PipelineFunnel.tsx`
- Integration: `src/app/owner/insights/page.tsx` (positioned after Stage Breakdown)
- Test coverage: `src/components/visual/__tests__/PipelineFunnel.test.tsx` (4 tests)
- Data source: Pipeline metrics (stages: New Inquiry → Trip Details → Ready to Quote → Build Options → Final Review)

### 2. Monthly Trend (Revenue Chart)
Displays monthly performance with:
- Revenue (bar series in USD)
- Booked count (line series overlay)
- Dual Y-axes for different scales

Implementation:
- Component: `src/components/visual/RevenueChart.tsx`
- Integration: `src/app/owner/insights/page.tsx` (positioned after Pipeline Funnel)
- Test coverage: `src/components/visual/__tests__/RevenueChart.test.tsx` (3 tests)
- Data source: Monthly aggregated revenue and booking data

### 3. Agent Performance Metrics (Team Performance Chart)
Shows individual agent performance across four dimensions:
- Conversion rate (% of inquiries converted to bookings)
- Response time (hours to first response)
- Customer satisfaction (CSAT out of 5.0)
- Workload score (% utilization with color-coded severity)

Implementation:
- Component: `src/components/visual/TeamPerformanceChart.tsx`
- Integration: `src/app/owner/insights/page.tsx` (positioned after Revenue Chart)
- Test coverage: `src/components/visual/__tests__/TeamPerformanceChart.test.tsx` (4 tests)
- Features: Color-coded metrics (green/blue/amber/red) for quick health assessment
- Data source: Team member metrics from mock or API

**Test Coverage**: 11 total visualization tests across 3 components (all passing)

## Using the Workbench

1. **Go to** http://localhost:3000/workbench
2. **Select a scenario** (optional) — choose from dropdown to pre-fill inputs
3. **Enter inputs**:
   - `raw_note`: The incoming agency note
   - `owner_note`: Optional owner note
   - `structured_json`: Optional structured data as JSON
   - `itinerary_text`: Optional itinerary text
4. **Configure**:
   - `stage`: discovery | shortlist | proposal | booking
   - `operating_mode`: normal_intake | audit | emergency | follow_up | cancellation | post_trip | coordinator_group | owner_review
   - `strict_leakage`: Enable strict leakage checking
5. **Click "Run Spine"** — results populate in other tabs
6. **Switch tabs** to inspect — no rerun on tab switch

## State Colors

| Color | Decision State |
|-------|---------------|
| 🟢 Green | PROCEED_TRAVELER_SAFE |
| 🟡 Amber | PROCEED_INTERNAL_DRAFT, BRANCH_OPTIONS |
| 🔴 Red | STOP_NEEDS_REVIEW |
| 🔵 Blue | ASK_FOLLOWUP |

## Troubleshooting

### Start spine_api first
The Next.js BFF calls the spine_api FastAPI service on port 8000. Start it with:
```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run uvicorn spine_api.server:app --port 8000
```

### "spine_api connection failed"
```bash
# Verify spine_api is running
curl http://127.0.0.1:8000/health
# Should return: {"status":"ok","version":"0.0.1"}

# Or test a spine run directly
curl -X POST http://127.0.0.1:8000/run \
  -H "Content-Type: application/json" \
  -d '{"raw_note":"Family of 4 to Singapore","stage":"discovery"}'
```

### "Module not found" errors
```bash
cd /Users/pranay/Projects/travel_agency_agent
source .venv/bin/activate
pip install -e .  # Install project dependencies
```

### Port 3000 in use
```bash
# Find and kill
lsof -ti:3000 | xargs kill -9
cd frontend && npm run dev
```

Or use the built-in reset helper:

```bash
cd /Users/pranay/Projects/travel_agency_agent/frontend
npm run dev:reset
npm run dev
```

### Frontend shows "No scenarios found" or API errors
```bash
# Verify scenarios are found
curl http://localhost:3000/api/scenarios
# Should return: {"items":[{"id":"clean-family-booking",...}, ...]}

# If empty, the path might be wrong. Check:
node -e "const p=require('path'); console.log(p.join(process.cwd(),'..','data','fixtures','scenarios'))"
# Should be: /Users/pranay/Projects/travel_agency_agent/data/fixtures/scenarios
```

## API Contract

### POST /api/spine/run

**Request:**
```json
{
  "raw_note": "Family of 4 from Bangalore to Singapore",
  "owner_note": null,
  "structured_json": null,
  "itinerary_text": null,
  "stage": "discovery",
  "operating_mode": "normal_intake",
  "strict_leakage": false,
  "scenario_id": null
}
```

**Response:**
```json
{
  "ok": true,
  "run_id": "abc123",
  "packet": { ... },
  "validation": { ... },
  "decision": { "decision_state": "ASK_FOLLOWUP", ... },
  "strategy": { ... },
  "internal_bundle": { ... },
  "traveler_bundle": { ... },
  "safety": { "strict_leakage": false, "leakage_passed": true, "leakage_errors": [] },
  "assertions": null,
  "meta": { "stage": "discovery", "operating_mode": "normal_intake", "fixture_id": null, "execution_ms": 45.2 }
}
```

### GET /api/scenarios

**Response:**
```json
{
  "items": [
    { "id": "clean-family-booking", "title": "Clean family booking — proceed traveler-safe" },
    { "id": "vague-under-specified", "title": "Vague under-specified lead — ask followup" },
    { "id": "hybrid-contradiction", "title": "Hybrid conflict — husband vs wife contradiction" }
  ]
}
```

### GET /api/scenarios/[id]

**Response:**
```json
{
  "id": "clean-family-booking",
  "input": { "raw_note": "...", "stage": "discovery", ... },
  "expected": { "allowed_decision_states": [...], ... }
}
```

## Development

```bash
cd /Users/pranay/Projects/travel_agency_agent/frontend

# Install dependencies
npm install

# TypeScript check + build
npm run build

# Start dev server (hot reload)
npm run dev

# Start production server
npm start
```
