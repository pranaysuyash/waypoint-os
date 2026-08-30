# Case Study: Live Product Demo Simulation — Sam (Boutique Hobbyist)

**Date**: 2026-08-30  
**Simulation Mode**: Live Browser Computer-Use (`chrome-devtools-mcp`)  
**Persona**: Sam Rivera (`P-HOBBYIST-01`) — Boutique Travel Designer & Solo Curator  
**Target Platform**: Waypoint OS (`Next.js :3005` + `FastAPI :8000`)

---

## 1. Executive Summary

A live, unscripted product walkthrough was conducted from the perspective of **Sam Rivera**, a boutique travel hobbyist transitioning into bespoke travel consulting. The simulation exercised tenant registration, raw text message intake, automated entity extraction, guardrail enforcement, persona council governance, and memory retention policies.

### Commercial Verdict
* **Decision**: **WILL BUY (Solo Pro Tier)**
* **Primary Value Driver**: 1-click unstructured WhatsApp intake, strict stage gating (preventing half-baked quotes), and automated missing-field follow-up copy.
* **Secondary Value Driver**: Cross-trip memory graph preserving dietary and medical safety rules permanently.

---

## 2. Visual Artifacts & Live Evidence

| Step | Stage | Key Interaction | Asset Reference |
| :--- | :--- | :--- | :--- |
| **01** | **Workspace Setup** | Zero-bloat dark-mode overview with keyboard shortcuts (`Cmd + N`) | `Docs/review/assets/sim_01_overview.png` |
| **02** | **Raw Intake** | Ingested messy WhatsApp paragraph for cherry blossom family trip | `Docs/review/assets/sim_02_raw_intake.png` |
| **03** | **Extraction Packet** | Extracted April 10–20 2027 dates, 3 pax, ryokan & tea preferences | `Docs/review/assets/sim_03_extracted_packet.png` |
| **04** | **Council Center** | Explored EU261 compensation, FX volatility buffers, and tokens | `Docs/review/assets/sim_04_persona_council.png` |
| **05** | **Hard Blockers** | Locked downstream quote stages until origin & budget verified | `Docs/review/assets/sim_05_intake_blockers.png` |
| **06** | **Unlocked Planning** | Filled origin (JFK) and $14k budget; planning stages unlocked | `Docs/review/assets/sim_06_unlocked_planning.png` |
| **07** | **Payment Ledger** | Automated reconciliation queue and supplier split tracking | `Docs/review/assets/sim_07_payments_ledger.png` |
| **08** | **5-Tier Memory** | Permanent allergy retention vs. decaying seasonal vibes | `Docs/review/assets/sim_08_memory_retention.png` |

---

## 3. Step-by-Step Simulation Observations

### Step 1: Onboarding & Workspace Initialization
* Navigated to `/signup`, filled name `Sam Rivera` and work email `sam.rivera.escapes@testdemo.io`.
* Onboarding cards presented immediate actionable next steps without forced product tours.
* **User Feedback**: *"Clean, fast, looks like Linear. Doesn't feel like a legacy enterprise GDS tool."*

### Step 2: Unstructured WhatsApp Intake
* Raw input:
  > *"Hi Sam! We're planning a trip to Japan for our family of 3 (me, my wife Sarah, and our 7-year-old son Leo). Dates: April 10 to April 20, 2027 (Cherry Blossom season). Destinations: Tokyo (4 nights) and Kyoto (6 nights). Budget: Around $14,000 total excluding international flights. Preferences: High-end boutique ryokan with private onsen in Kyoto, bullet train first class (Green car), private tea ceremony, hands-on sushi making class in Tokyo, and family-friendly walking pace. Leo is mildly allergic to peanuts. Passports: US passports valid through 2030. Purpose: Family vacation."*
* Extraction executed in <1s.
* **Friction Discovered**: Initial salutation *"Hi Sam!"* led the heuristic destination parser to tag destination as *"Sam"*.
* **User Feedback**: *"Very fast parsing. Caught the exact travel dates in 2027 and party count immediately."*

### Step 3: Stage Gatekeeper Enforcement
* System blocked quote options generation with clear visual status: `Origin city [REQUIRED]` and `Budget range [REQUIRED]`.
* System generated pre-filled follow-up question: *"Hi, to start planning properly, could you confirm your approximate budget range and your departure city?"*
* **User Feedback**: *"This is a lifesaver. I normally spend 20 minutes reviewing my notes to figure out what I forgot to ask."*

### Step 4: Persona Council Governance & Memory
* Inspected EU261 compensation calculator, dynamic FX volatility netting, and zero-trust capability tokens.
* Inspected 5-tier memory retention rules in Settings (Allergies: Permanent; Passports: 36 mo; Seasonal vibes: 6 mo).
* **User Feedback**: *"The memory retention rule differentiation makes complete sense. Other CRMs just keep rotting old notes forever."*

---

## 4. Engineering Findings & Remediations Applied

1. **Remediated**: Fixed TypeScript/JSX Python f-string formatting syntax in `DistributionPanel.tsx`.
2. **Remediated**: Fixed Next.js 14 layout export compliance in `src/app/(agency)/trips/[tripId]/layout.tsx`.
3. **Remediated**: Fixed `setOffset` state updater typing in `src/app/(agency)/payments/PageClient.tsx`.
4. **Remediated**: Fixed non-null type safety checks in `CrisisEvacuationPanel.tsx`.
5. **Backlog Action**: Update fast-intake regex to strip leading greetings (`Hi <Name>,`, `Dear <Name>,`) before candidate entity extraction.
