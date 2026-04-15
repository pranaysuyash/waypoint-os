# Travel Agency Agent — Frontend

Next.js frontend for the Travel Agency Agent system. The frontend communicates with the Python spine via a persistent FastAPI service.

## Architecture

```
Browser → Next.js (localhost:3000) → spine-api (FastAPI, port 8000) → run_spine_once
                                                             (persistent process,
                                                              modules pre-loaded)
```

- **Frontend**: Next.js 16.2.3 with App Router, TypeScript, Zustand
- **Backend**: Python 3.13+ via `spine-api` FastAPI service (persistent process)
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
│   │   │   ├── spine/run/route.ts     # POST /api/spine/run (BFF → spine-api)
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
│   │   ├── spine-client.ts           # HTTP client → spine-api (port 8000)
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
│   │   ├── spine-client.ts           # HTTP client → spine-api (port 8000)
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

### Start spine-api first
The Next.js BFF calls the spine-api FastAPI service on port 8000. Start it with:
```bash
cd /Users/pranay/Projects/travel_agency_agent
uv run uvicorn spine-api.server:app --port 8000
```

### "spine-api connection failed"
```bash
# Verify spine-api is running
curl http://127.0.0.1:8000/health
# Should return: {"status":"ok","version":"1.0.0"}

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