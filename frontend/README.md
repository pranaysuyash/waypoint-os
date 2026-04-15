# Travel Agency Agent — Frontend

Next.js frontend for the Travel Agency Agent system. The frontend communicates with the Python spine via a subprocess bridge.

## Architecture

```
Browser → Next.js (localhost:3000) → spine-wrapper.py → Python spine modules
```

- **Frontend**: Next.js 16.2.3 with App Router, TypeScript, Zustand
- **Backend**: Python 3.13+ via `spine-wrapper.py` subprocess
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
│   │   ├── spine-wrapper.py          # Python spine bridge (subprocess)
│   │   ├── spine-client.ts           # TypeScript subprocess client
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

### "Spine subprocess failed"
```bash
cd /Users/pranay/Projects/travel_agency_agent
source .venv/bin/activate
echo '{"raw_note":"test","stage":"discovery","operating_mode":"normal_intake","strict_leakage":false}' | python3 frontend/src/lib/spine-wrapper.py
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
  "packet": { ... },
  "validation": { ... },
  "decision": { "decision_state": "ASK_FOLLOWUP", ... },
  "strategy": { ... },
  "internal_bundle": { ... },
  "traveler_bundle": { ... },
  "leakage": { "ok": true, "items": [] },
  "assertions": null,
  "run_ts": "2026-04-15T..."
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