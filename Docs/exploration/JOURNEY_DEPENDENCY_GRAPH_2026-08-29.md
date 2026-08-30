# Journey Dependency Graph (JDG) for IROPS Ripple Analysis — Design Exploration

**Date:** 2026-08-29
**Status:** Exploration / proposed design. **Not implemented.**
**Origin finding:** R-12 from `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md` — "No Journey Dependency Graph for IROPS ripple analysis."
**Parent index:** [`../EXPLORATION_TOPICS.md`](../EXPLORATION_TOPICS.md)
**Sibling exploration:** [`ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md`](./ARCHITECTURE_TOPOLOGY_REVIEW_2026-05-11.md)
**Governing doctrine:** `OPERATING_DOCTRINE.md` v8.0 — truth taxonomy (§2), canonical paths (§5), first-principles decomposition (§7), durable knowledge (§9/§14).

---

> **Precision note on the origin finding.** R-12 reads "No Journey Dependency Graph for IROPS ripple analysis." That is accurate for *IROPS ripple analysis as a reachable capability*, but it is **not** accurate as a literal statement that no JDG code exists. The ground truth (Observed, verified below) is:
>
> - A JDG **schema and ripple evaluator already exist** at `src/schemas/journey_graph.py`.
> - The graph is **constructed** in `spine_api/routers/constraints.py` and fed to `ConstraintEngine`, but **only from a minimal flight/activity subset of the trip**, and **`evaluate_disruption()` is never called from any router, service, or agent** — it is invoked only from `tests/test_journey_graph.py`.
> - There is **no IROPS trigger path**: the `FlightStatusAgent` produces a `flight_status_snapshot` (delay/risk) but nothing feeds that signal into a ripple computation, and nothing surfaces a `DisruptionRippleReport` to an operator.
>
> So the honest framing for this document is: **a JDG prototype exists in seed form; the IROPS ripple capability is not wired, not composed from the full trip, and not reachable by any product surface.** This doc designs the *complete*, *composed*, *reachable* JDG.

---

## 1. Problem Statement — Why a JDG Is Needed for IROPS Ripple Analysis

**IROPS** = *Irregular Operations*. In a travel agency operating system this means any operational deviation from the planned itinerary: a flight delay, a flight cancellation, a missed connection, a weather event that closes an activity, a transfer that cannot operate. Each is a discrete failure at one point in a trip. The operational question is not "what broke here" but **"what else breaks downstream, and how fast does the agency need to act?"**

Observed gap — the current system answers the *local* question and stops:

- `src/agents/runtime.py:2555` `FlightStatusAgent` reads a `FlightStatusTool` and writes `flight_status_snapshot` → `risk_level` (`low/medium/high/unknown`), `operator_next_action` (`monitor_flights` / `review_flight_disruption`). This is a **per-node, snapshot-level** answer. It says "this flight is 90 minutes late" — it does **not** say "therefore the airport transfer at 15:00 is missed, the 17:00 yacht tour is lost, the hotel check-in window at 19:00 is violated, and the 08:00 return leg is at risk."
- `src/agents/runtime.py:1936` `ConstraintFeasibilityAgent` reads `flight_status.risk_level` and, when `high`, emits a generic `hard_blocker` "Flight disruption risk is high" with a generic relaxation option ("Revalidate operational timing and alternatives"). No connection graph, no specific downstream node, no per-impact detail.
- `spine_api/routers/constraints.py` `evaluate_trip_constraints` builds a `JourneyDependencyGraph` **without calling** `evaluate_disruption`, and only from a fallback flight node or `itinerary_legs` where non-flight legs are typed as `ACTIVITY`. No hotel, no transfer edges, no traveler edges, no buffer/connection semantics beyond the MCT rule.

The consequence is **compounding operational blindness**: when the first link breaks, an agent must manually re-derive every downstream dependency by reading the flat itinerary and doing mental temporal arithmetic. For a 6-leg international trip with hotels, transfers, and activities, this is error-prone and slow precisely when speed matters most. Missed rebooking of a connecting leg is a hard failure; a same-day activity is a soft miss; a hotel late-arrival is a cost/comfort issue. Each has a different *severity*, *failure cost*, and *action window* — none of which a flat list or a per-node status can express.

**What a JDG buys:** a single, replayable, queryable graph of *how the trip is physically, temporally, and causally connected*, plus an algorithm that — given one node's disruption — walks the connection edges, detects which downstream connections break, computes how bad each break is (severity), how much it costs (failure cost), and what the agency should do (recommended action) and by when (time budget).

The JDG is **not** a booking engine, a pricing engine, or a replanning optimizer. It is the **situational-awareness substrate** that makes IROPS response tractable. It answers "what is affected and how urgently," leaving "how to fix it" to the operator (or a later recovery planner).

---

## 2. Domain Model

### 2.1 Entities

The travel-agency domain decomposes into five node families plus a traveler overlay. Names here align to the existing `NodeType` enum in `src/schemas/journey_graph.py` where they already exist, and extend it where they do not.

| Entity | What it is | Existing enum value (`NodeType`) | Primary temporal anchor |
|---|---|---|---|
| **Flight** | One scheduled flight segment (departure airport → arrival airport, on a carrier/flight number) | `FLIGHT` | `end_time` (arrival) — the arrival clock matters most for downstream deps |
| **Rail / Ferry** | One scheduled rail or ferry leg (connects a journey along a rail/water path) | `RAIL`, `FERRY` | `end_time` (arrival) |
| **Transfer** | A ground transfer (airport pickup, private car, shared shuttle, train-to-venue) | `TRANSFER` | `start_time` (pickup) |
| **Hotel** | A stay at a hotel (one night or a run of nights). Split into **check-in** (arrival/window) and **stay** (the occupied nights) | `HOTEL_CHECKIN`, `HOTEL_STAY` | check-in window `start_time`; stay = a date range |
| **Activity** | A bookable experience (tour, excursion, restaurant reservation, attraction) | `ACTIVITY`, `RESTAURANT` | `start_time` |
| **Traveler** | A person in the party; the *subject* of all the above nodes (who is affected). Not a time-anchored node — an **overlay/grouping dimension** | — (proposed: overlay, not a node) | n/a |

### 2.2 Relationship Types

A relationship is a **directed edge** with a causal direction: the *upstream* node's state determines the *downstream* node's feasibility. This is the single most important modeling decision — the graph is a **directed acyclic-ish temporal causal graph**, not a symmetric set of "related" items.

| Relationship type | Direction | Semantics | Example |
|---|---|---|---|
| **Sequential** | A → B | B's start requires A's end to have happened with a minimum gap (a strict `>=` precedence). The canonical case: connecting flights, flight → transfer. | Flight arrives 14:00; transfer picks up 15:00. |
| **Dependency** | A → B | B is *contingent on* A being feasible, but the ordering may be loose (same day, same venue) rather than a hard precedence. | A hotel checkout is contingent on a prior night's stay; an activity is contingent on an arrival the same day. |
| **Buffer window** | A → B (edge carries a `buffer` value) | A's arrival must be complete by B's start **minus** a buffer; the buffer is the *slack* the connection carries. If A is late by more than the buffer, the connection breaks. | Arrival 14:00, transfer 15:00 → buffer = 60m. A 90m delay breaks it. |
| **Same-day** | A → B (edge marks same-day co-location) | A and B occur on the same calendar date and must be co-located and non-overlapping. Used for activities that share a day with an arrival or with each other. | Flight + same-day museum visit. |
| **Cross-day** | A → B (edge crosses a date boundary) | The relationship spans days — typically a hotel night that must *contain* the gap between an arrival day and the next day's departure, or a stay that provides the overnight anchor for a multi-day activity span. | Hotel check-in day 1, activity day 2, hotel check-out day 2. |

> These five map onto the two existing edge semantics found in `src/schemas/journey_graph.py` (`REQUIRES_ARRIVAL_BEFORE`, `TRANSFER_CONNECTS`, `SAME_DAY_ACTIVITY`, `HOTEL_NIGHT_FOR`, `RETURN_LEG_OF`) and the existing constraint categories in `src/schemas/constraints.py` (`TEMPORAL_MCT`, `SPATIAL_CONTINUITY`, `CAPACITY_ROOMING`, `TEMPORAL_PACING`). The design generalizes the existing enum rather than replacing it. This is a **Proposed** consolidation; the current enums are **Observed**.

### 2.3 The Three "Why" Maps

A good JDG answers three distinct questions, each with its own edge family. The design should **separate** these rather than overload one edge type:

1. **Temporal-causal map** — "does A's end precede B's start by enough?" → `sequential` / `dependency` edges with buffers. This is the propagation backbone.
2. **Physical-co-location map** — "are A and B at the same place, or is there a journey between them?" → location identity + a transfer/distance edge (drives `SPATIAL_CONTINUITY`). This determines whether a same-day activity is even reachable.
3. **Ownership/grouping map** — "which traveler(s) does this node belong to, and which nodes belong to the same traveler/party?" → traveler overlay edges. This determines *who* is impacted and enables per-traveler severity.

---

## 3. Graph Data Model

### 3.1 Node Types (extending the existing `NodeType`)

The existing `NodeType` in `src/schemas/journey_graph.py:16` is **Observed**:

```python
class NodeType(StrEnum):
    FLIGHT = "FLIGHT"
    RAIL = "RAIL"
    FERRY = "FERRY"
    TRANSFER = "TRANSFER"
    HOTEL_CHECKIN = "HOTEL_CHECKIN"
    HOTEL_STAY = "HOTEL_STAY"
    ACTIVITY = "ACTIVITY"
    RESTAURANT = "RESTAURANT"
```

The design retains all of these. **Proposed additions / refinements:**

| Node attribute | Existing (`JourneyNode`) | Proposed rationale |
|---|---|---|
| `node_id`, `node_type`, `title`, `location` | present | keep |
| `start_time`, `end_time` | present | keep — these are the temporal anchors the ripple math needs |
| `buffer_minutes_before` | present (default 30) | keep, but **promote buffer to edge-level** (see §3.3) so each connection can carry its own minimum |
| `provider`, `confirmation_code` | present | keep — provenance for the rebooking/contact action |
| `is_cancellable`, `cancellation_deadline` | present | keep — needed to decide whether a recommended action is even possible |
| `timezone` | **missing** | **add.** A 14:00 arrival in Dubai and a 15:00 transfer in Dubai are both local; but comparing a UTC-normalized flight clock to a local activity clock will corrupt deficits. Every node needs an explicit tz. |
| `per_traveler_ids` | **missing** | **add.** The overlay dimension (which travelers ride this node). |
| `co_location_group` | missing | **add.** A stable key for "same physical venue/area" so co-location checks are O(1) not geographic. |
| `epistemic_status` | missing | **add** (`FACT/INFERRED/ASSUMED/UNKNOWN` from `src/intake/packet_models.py:91`, which is **Observed** to already exist). Distinguishes a confirmed booking (FACT) from an agent-assumed transfer slot (ASSUMED). |

### 3.2 Edge Types with Semantics

**Proposed** edge schema — a directed edge `(from, to, kind, buffer, weight, scope)`:

| Edge kind | Meaning | Used for | Causal propagation |
|---|---|---|---|
| `SEQUENTIAL` | `to` cannot start until `from` ends + `buffer` | flight→flight, flight→transfer, transfer→activity | **yes** — the backbone of ripple |
| `DEPENDENCY` | `to` contingent on `from` being feasible, looser ordering | hotel checkout→next arrival, activity→same-day arrival | **yes** (with a configurable, often looser, tolerance) |
| `BUFFER_WINDOW` | an explicit slack value; encodes *how much* late `from` can be before `to` breaks | any connection with a known minimum | **yes** — the quantitative core |
| `SAME_DAY` | `from` and `to` same date, must be co-located & non-overlapping | arrival→activity, activity→activity | partial (overlap violation, not just lateness) |
| `CROSS_DAY` | relationship spans a date boundary (hotel overnight anchor) | arrival→hotel stay→next-day activity | **yes** — determines whether a lost night cascades |
| `TRAVELER_GROUPING` | nodes share a traveler/party (overlay, no time semantics) | per-traveler severity, "who is affected" | **no** — grouping only |

### 3.3 Edge Weights

Every edge carries **quantitative** properties so the propagation algorithm can compute deficits and severity deterministically:

| Weight / attribute | Meaning | Default | Source |
|---|---|---|---|
| `buffer_minutes` | Minimum slack required between `from.end` and `to.start`. The larger this is, the more delay the connection absorbs. | 30 (domestic), 60 (standard), 90 (international) | Currently a constant in `ConstraintEngine` (`src/decision/constraint_engine.py:72` — `90 if international else 45`). **Proposed** to move to edge-level so different edges carry different minimums. |
| `connection_min` | Hard minimum connect time (MCT) — a *legal/operational* floor distinct from comfort buffer. | 45/90 | `ConstraintEngine` `min_mct`. |
| `travel_cost_minutes` | Time to physically move between the two nodes' locations (drives `SPATIAL_CONTINUITY`). | configurable | **add.** Needed for cross-location same-day feasibility. |
| `failure_cost` | The monetary/experience/legal cost of breaking this connection. | per-kind default | **add.** See §3.4. |
| `cancellation_penalty` | Cost of cancelling/rebooking `to`. | per-kind | **add.** Distinguishes "soft miss" (activity) from "hard rebook" (connecting flight) from "costly no-show" (prepaid hotel/activity). |
| `criticality` | `hard` vs `soft` vs `advisory` vs `preference`. | `hard` for connections, `soft` for activities | **add.** Mirrors `ConstraintType.HARD/SOFT` in `src/schemas/constraints.py:15`. |

### 3.4 Failure Cost (a severity multiplier, not just a deficit)

Severity must be **more than time deficit**. A 30-minute deficit on a restaurant reservation is trivial; a 30-minute deficit on a connecting flight with a cancelled itinerary is critical. The design computes a **failure cost** per impacted node that combines:

- **Monetary exposure** — prepaid vs pay-at-venue; non-refundable penalties; rebooking fare difference.
- **Recoverability** — is the node cancellable (`is_cancellable`)? Does a later option exist (next flight, next transfer)? This directly uses the existing `is_cancellable` / `cancellation_deadline` fields.
- **Traveler-criticality** — is this node on the critical path (a connection that gates many downstream nodes) vs a leaf (a single activity)? Critical-path nodes have higher cascading weight.
- **Irreversibility window** — how fast must the agency act (drives the `time to act` and the operator priority).

**Proposed severity ladder** (kept simple and deterministic):

| Severity | Signal | Typical trigger | Action |
|---|---|---|---|
| `critical` | irrecoverable, gating, or cancellation cascade | cancelled connecting flight; missed last connection of the day; flight node broken | "Rebook / cancel now — connection is broken." |
| `high` | recoverable but materially costly or timing-impossible without action | transfer missed with no easy substitute; prepaid non-refundable activity lost | "Rebook to a later slot or fast-track the transfer." |
| `medium` | timing budget violated but node still feasible with a change | late arrival still inside the venue's window, but buffer is eroded | "Add buffer / confirm flexible start." |
| `low` | absorbed within the buffer, or trivial | minor delay inside existing slack | "Monitor." |

This matches the existing `DisruptionImpact.impact_severity` literal (`critical/low/medium/high`) in `src/schemas/journey_graph.py:92`. **Observed** — and the design keeps that vocabulary.

### 3.5 Temporal Attributes

Every node and every computed impact carries a **time model**. The critical ones:

- `scheduled_start` / `scheduled_end` — the planned window (from the packet / booking).
- `feasible_start` — the earliest the node *could* start given upstream disruption = `max(upstream affected end, scheduled_start) + buffer`.
- `time_deficit_minutes` — `feasible_start − scheduled_start` (0 if absorbed). **Observed** in `DisruptionImpact` (`src/schemas/journey_graph.py:95`).
- `timezone` — **must be added** to avoid tz-corrupted deficits (§3.1).

Time is the dimension the whole propagation runs on; getting normalization right (UTC for computation, local for display, per-node tz for comparison) is a first-principle requirement, not a detail.

---

## 4. Ripple Propagation Algorithm

### 4.1 Core idea

Given a **root disruption** at one node (`delay_minutes` and/or `is_cancellation`), walk the **outgoing temporal edges** (BFS) from the disrupted node. For each downstream node, compute the *earliest feasible start* — `upstream affected end time + buffer`. If that is `> scheduled_start`, the connection is violated, a `DisruptionImpact` is recorded, and the *deficit* is propagated to that node's own end time, cascading further downstream. This is exactly the algorithm already prototyped in `JourneyDependencyGraph.evaluate_disruption()` at `src/schemas/journey_graph.py:168`. **Observed.**

### 4.2 Algorithm (Proposed — generalizing the observed prototype)

```
FUNCTION evaluate_disruption(graph, root_id, delay_minutes, is_cancellation):
    root = graph.nodes[root_id]
    # Seed: the root node's own end time is pushed back by the delay
    affected_end[root_id]  = root.end_time + delay_minutes
    queue = FIFO([root_id])
    impacts = []; visited = {root_id}; cost = {root_id: delay_minutes}

    WHILE queue not empty:
        curr = queue.pop_front()
        FOR each edge in graph.outgoing_edges(curr):
            target = graph.nodes[edge.to]
            IF is_cancellation:
                # A cancelled upstream = connection definitely broken
                record IMPACT(target, severity=critical, reason="Upstream cancelled")
                propagate: affected_end[target] = target.end_time + 1 day  (unless absorbable via alternate)
                queue.push(target)
            ELSE:
                feasible_start = affected_end[curr] + edge.buffer_minutes
                if feasible_start > target.scheduled_start:
                    deficit = feasible_start - target.scheduled_start
                    severity = classify(deficit, target.node_type, edge.criticality, edge.failure_cost)
                    record IMPACT(target, severity, feasible_start, deficit, recommended_action)
                    # Cascade: push the target's own end time back by the deficit
                    affected_end[target] = target.end_time + deficit
                    queue.push(target)
                ELSE if target has a CROSS_DAY edge:
                    # A same-node absorbed delay may still break a cross-day anchor
                    check cross-day relationship (e.g. hotel night lost)
    RETURN DisruptionRippleReport(root_id, delay, is_cancellation, impacts, unaffected)
```

### 4.3 Key mechanics

- **Connection-broken detection.** The break predicate is `affected_end[upstream] + buffer > scheduled_start[downstream]`. This is the *quantitative* heartbeat of the algorithm. A delay is only a problem if it exceeds the edge's buffer — a 10m delay into a 60m buffer is absorbed (returns `unaffected`, exactly as `tests/test_journey_graph.py:63` asserts).
- **BFS over temporal edges** (not DFS, not arbitrary). The reachable set is *exactly the downstream causal closure* of the root, ordered by arrival time. A single root can fan out to many downstream nodes; BFS guarantees each is evaluated once and each gets its earliest-feasible clock.
- **Severity propagation.** The deficit propagates multiplicatively through the chain: a 90m flight delay becomes a 75m transfer deficit (because it absorbs 15m of the buffer) and then a 75m activity deficit. The design records *per-node* deficit and severity, so an operator sees a chain, not just the root.
- **Cancellation as the atomic worst case.** A cancellation should be modeled as a *reset* on the downstream node — the downstream node is not merely late, it is impossible, and the recommended action becomes "cancel or rebook immediately." The observed prototype does this (`src/schemas/journey_graph.py:198`).
- **Cycle/diamond handling.** Use a `visited` set keyed by node id to prevent re-processing a node reached by two paths (a diamond in the graph). Keep the *worst* (max deficit / max cost) impact if a node is reachable by more than one path — a two-path arrival where both are late compounds.
- **CROSS_DAY / hotel anchor.** A hotel is not a point in time; it is an interval that *contains* an arrival gap and *anchors* a multi-day activity span. A disruption that shifts the arrival past the check-in window can invalidate the night, which then feeds the next day's activity. Model hotel stay as a duration node, not a point node.

### 4.4 Failure-cost ranking (output ordering)

After propagation, order the impacted nodes by **`failure_cost`** (not just deficit) so the operator sees highest-exposure first. This is a **Proposed** addition over the observed prototype, which orders by traversal.

---

## 5. Data Sources

Where do nodes and edges come from? The JDG is **derived**, not a new store — it should be composed from data that already exists (or is one small adapter away). All of the following are **Observed** code paths or **Observed** packet fields.

### 5.1 Trip packet & booking data (`src/intake/packet_models.py`, `spine_api/models/trips.py`)

| Node | Source field | Where |
|---|---|---|
| Flight | `itinerary_legs` (type `== "flight"`), `flights` / `flight_segments`, `booking_data.flights` | `constraints.py:113`; `runtime.py:2639` |
| Transfer | `itinerary_legs` (type `== "transfer"`), transfer-like itinerary items | `constraints.py:141` (currently typed as `ACTIVITY` — see §6 gap) |
| Hotel | `booking_data.hotel` / accommodation blocks; `itinerary_legs` | not currently extracted into the graph |
| Activity | `itinerary_legs` (type `== "activity"`), `itinerary_items` / `activities` | `constraints.py:141`; `runtime.py:1377` |
| Traveler | `booking_data.travelers` / `travelers`; packet `party_composition` | `runtime.py:1012`; `packet_models.py` |

The **facts/slots** in `CanonicalPacket` (`src/intake/packet_models.py`) carry provenance (`evidence_refs`), authority (`authority_level`), and `epistemic_status` — which is exactly the metadata the JDG needs to mark a node as `FACT` vs `ASSUMED`. A JDG built purely from `ASSUMED` slots is a *proposal-shape* graph, not an *operational truth* graph; this distinction is what the epistemic overlay enables.

### 5.2 Supplier / live-tool adapters (`src/agents/live_tools.py`)

The `FlightStatusTool` protocol (`live_tools.py:26`) with `MockFlightStatusTool` (`:72`) and `HTTPFlightStatusTool` (`:236`), selected via `build_flight_status_tool_from_env()` (`:411`), is the **inbound IROPS signal source**. It yields `status`, `delay_minutes`, `route`. This is the *trigger* for ripple evaluation: when `delay_minutes >= 45` or `status in {cancelled, diverted}`, the JDG should be invoked on that node.

Other live tools that can produce **edge-affecting** events:
- `WeatherTool` (`live_tools.py:21`) — drives `WeatherPivotAgent` (`runtime.py:1296`) → can invalidate an outdoor activity node.
- `SafetyAlertTool` (`live_tools.py:33`) — drives `SafetyAlertAgent` (`runtime.py:2792`) → can invalidate a whole destination-day.
- `PriceWatchTool` (`live_tools.py:27`) — more pricing than IROPS; not a JDG edge driver.

### 5.3 External GDS / NDC (future, not present)

The current system has no real GDS/NDC connectivity — flight data is either mock (deterministic) or configurable HTTP (`live_tools.py:236`). **Proposed** for a full JDG:
- **GDS (Amadeus / Sabre / Travelport)** for authoritative schedules, MCT tables, and real-time ATO/ETA.
- **NDC** for fare/availability and rebooking options on connecting legs.
- **Hotel CRS / supplier APIs** for cancellation deadlines and prepaid penalties (needed for `failure_cost`).
- **Activity/transfer APIs (Viator, Klook, GetYourGuide; local transfer operators)** for operating windows and cancellation terms.

`reality_tier.py` / `feature_gates.py` (`spine_api/core/`) mark these as `DATA_DEPENDENT` / `PLANNED` today, so the JDG should **not** assume live access — it must degrade to the deterministic/mock adapters it already has, and only *upgrade* severity/cost fidelity when live sources arrive.

---

## 6. Integration Points

The JDG is a derived read-model that plugs into four existing seams. Each seam is **Observed** (path + symbol) below; the JDG wiring is **Proposed**.

### 6.1 Packet / intake layer — `src/intake/packet_models.py`

- **Observed:** `CanonicalPacket`, `Slot`, `AuthorityLevel`, `EpistemicStatus` (`:91`), `AssumptionRecord` (`:100`), `SuitabilityFlag`, `ambiguities`, `unknowns`, `contradictions`.
- **Proposed:** a `build_journey_graph(packet)` assembler that reads the packet's `facts` / `booking_data` / `itinerary_legs` and emits a `JourneyDependencyGraph`. It should tag each node with the slot's `epistemic_status` and `authority_level` so a graph built from assumptions is flagged `ASSUMED`, not silently treated as truth. This is the natural owner of graph *construction* from intake state.

### 6.2 Constraint router — `spine_api/routers/constraints.py`

- **Observed:** `constraints.py:32` imports `JourneyDependencyGraph`; `:111` constructs it; `:154` feeds it to `ConstraintEngine.evaluate_itinerary_graph`. It currently types non-flight legs as `ACTIVITY` and never calls `evaluate_disruption`.
- **Proposed:** (a) correctly type `itinerary_legs` into `FLIGHT/TRANSFER/HOTEL/ACTIVITY` (the current `ACTIVITY` catch-all loses transfer/hotel edges), (b) build the *edges* (buffer/sequence) between consecutive legs rather than only adding nodes, and (c) add an `evaluate_disruption(trip_id, node_id, delay, is_cancellation)` path here (or a sibling router) that returns a `DisruptionRippleReport`. This is the most direct existing seam.

### 6.3 Spine API routers — trip_lifecycle, agent_runtime, trip_observability

- **`spine_api/routers/trip_lifecycle.py`** — `reassess_trip` (`:39`) and `transition_trip_stage` (`:88`) already route disruption-adjacent workflows (reassessment). **Proposed:** a JDG ripple report is a natural *input* to a reassessment trigger when a disruption is detected, so the report should be attachable to the trip before reassessment fires.
- **`spine_api/routers/agent_runtime.py`** — `run_agent_runtime_once` (`:92`) and `get_agent_runtime` (`:59`). **Proposed:** register a new `IROPSRippleAgent` in the runtime registry (see §6.4) so a supervisor pass can *store* ripple reports on trips. Its `scan()` triggers when `flight_status_snapshot.risk_level ∈ {high, unknown}` or when a node's `delay_minutes` exceeds its incoming edge buffer.
- **`spine_api/routers/trip_observability.py`** — `get_trip_agent_events` (`:37`) and `get_trip_timeline` (`:54`). **Proposed:** expose a `GET /trips/{trip_id}/irops-ripple` endpoint that returns the latest `DisruptionRippleReport`; surface it alongside the existing timeline so an operator sees the ripple in the trip timeline.

### 6.4 Agent runtime — `src/agents/runtime.py` + `spine_api/services/agent_runtime_factory.py`

- **Observed:** `FlightStatusAgent` (`:2555`) writes `flight_status_snapshot`; `SafetyAlertAgent` (`:2792`); `WeatherPivotAgent` (`:1296`); `ConstraintFeasibilityAgent` (`:1499`); `build_default_registry()` (`:3150`) lists all agents; `agent_runtime_factory.build_agent_runtime()` (`:253`) wires the registry into `AgentSupervisor`.
- **Proposed:** add `IROPSRippleAgent` to `build_default_registry()`. Its contract:
  - `trigger_contract`: "Trip has a `flight_status_snapshot` (or other disruption signal) at `risk_level ∈ {medium, high, unknown}` and no current `irops_ripple_report` for the same signal marker."
  - `input_contract`: trip record with `flight_status_snapshot`, `itinerary_legs` / `booking_data`, and any same-day activity/transfer/hotel nodes.
  - `output_contract`: trip updated with `irops_ripple_report` (`DisruptionRippleReport.to_dict()`), `irops_ripple_risk_level`, and `operator_next_action`.
  - `idempotency_contract`: one ripple report per `trip_id` + disruption marker until the disruption signal changes (mirrors `FlightStatusAgent`'s `flight_marker` pattern at `runtime.py:2583`).
  - `failure_contract`: no real disruption signal → no report (don't fabricate); tool/assembly failure → fail closed into a known-limit report and poison after retry.

This is the cleanest place to *own the IROPS trigger*, because it sits right where `FlightStatusAgent` already produces the signal.

### 6.5 Persistence read-model

- **Observed:** `spine_api/models/trips.py` `Trip` has JSON columns (`booking_data`, `decision`, `extracted`, etc.). Agent outputs are persisted as named JSON keys on the trip (`flight_status_snapshot`, `safety_alert_packet`, etc.), read/written via the agent `TripRepository` and `TripStore`.
- **Proposed:** persist `irops_ripple_report` as a JSON key on the trip, exactly as `flight_status_snapshot` is persisted today. No new table, no new migration — this keeps the JDG additive and revertible and matches the existing read-model pattern.

---

## 7. First-Principles Decomposition

Strip the travel nouns and the JDG reduces to **three composable primitives** already present in the codebase under different names. This is the operating doctrine's noun-stripping requirement (§7, §9).

### 7.1 Primitive 1 — Temporal graph

A directed graph where nodes carry time intervals and edges carry *minimum gaps*. This is a **precedence/constraint network**. The existing `ConstraintEngine` (`src/decision/constraint_engine.py:41`) already does linear-adjacency temporal checks (`SPATIAL_OVERLAP`, `MCT_DEFICIT`, `TIGHT_LAYOVER`). The JDG generalizes this from *adjacent-pair* to *reachable closure*.

### 7.2 Primitive 2 — Constraint graph (CSP)

A graph where each edge is a *constraint* (HARD vs SOFT) and each node is a *variable* with a domain (its feasible window). The existing constraint vocabulary (`src/schemas/constraints.py`: `TEMPORAL_MCT`, `SPATIAL_CONTINUITY`, `REGULATORY_*`, `CAPACITY_ROOMING`, `FINANCIAL_BOUND`) is the constraint-primitive substrate. The JDG uses the same HARD/SOFT distinction on edges.

### 7.3 Primitive 3 — Failure propagation

A **causal cascade** computation: start at a perturbed variable, follow outgoing arcs, detect which downstream values violate their domain, and accumulate a *cost* (severity × exposure). This is the same shape as a **constraint-propagation / arc-consistency** pass or a **fault-tree / FMEA** walk. The existing `evaluate_disruption()` prototype is this primitive in miniature.

**Why this decomposition matters:** each primitive is independently testable and already has a partial implementation in the repo. The JDG is the *composition* of the three, not a new category of system. That makes it low-risk: it extends existing primitives instead of introducing a new paradigm.

---

## 8. Alternative Approaches Rejected

### 8.1 "Just keep a flat itinerary list" — rejected

- A flat list (the current `itinerary_legs` array, or `Docstring`-style day cards) is an **ordered collection** with no explicit dependency graph. It can be *read* in order, but it cannot express: shared buffers, cross-day anchors, traveler grouping, alternate-path reachability, or a non-linear diamond where two upstream nodes gate one downstream node.
- It supports **data display** but not **causal reasoning**. To compute a ripple you must re-derive the dependency structure every time by re-reading the list and doing temporal arithmetic in code — exactly the manual process the operator does today. It does not remove the bottleneck; it relocates it.
- A flat list **has no edge weights or failure costs**, so it cannot rank severity or compute an action window. It answers "what is on the trip" but not "what broke and how badly."

### 8.2 "A rule-based cascade table" — rejected

- A static table of `IF flight delayed > X THEN mark transfer missed` rules is **brute-force and non-composable**. It must enumerate every pair, every threshold, every node-type combination — O(N²) rules that go stale the moment the trip shape changes (add a hotel, change a buffer, split a party).
- Cascade tables **cannot handle variable graph structure**. A rule table is written for *the shape you had*, not the shape you have. Trips are heterogeneous (one 3-leg city break vs a 9-leg multi-country family trip), so a fixed rule set either under-covers or over-fires.
- Tables are **non-general about time**. The crucial quantity is `deficit vs buffer`, which is continuous and depends on the actual schedule, not a discrete `> X` threshold. A "> 45m" rule misclassifies a 30m delay into a 20m-buffer (broken) vs a 60m-buffer (fine).
- The JDG approach is a **computation over a data structure**, not a rule set — so it is general, composable, and survives trip-shape change. This is the decisive first-principles argument: **compute over the graph, don't tabulate every case.**

### 8.3 (Rejected as scope creep) "A full recovery/replanning optimizer" — deferred

A JDG is **not** a rebooking/replanning optimizer. It computes *what is affected and how urgent*, not *the optimal repair*. Building an optimizer is a substantially larger, higher-risk effort (a search over alternative legs, pricing, constraints). The doctrine (§1) prefers work that removes a real bottleneck first; the bottleneck is *situational awareness*, which the JDG removes. An optimizer is a clean follow-on that **consumes** the JDG's output (the affected node set + feasible windows) rather than replacing it. Rejecting the optimizer for v0 is not rejecting the JDG.

---

## 9. Open Questions and Stopping Rules

### 9.1 Open questions

1. **What is the canonical source of `itinerary_legs` / trip topology?** `constraints.py` reads `trip.get("itinerary_legs")`, but the `Trip` model (`spine_api/models/trips.py`) has no explicit `itinerary_legs` column — it is a derived/loose key. Is there a canonical home for the assembled leg graph, or is it built on demand from `booking_data` + `itinerary_items`? (Needs a source-of-truth decision before building the assembler.)

2. **Where do buffers/MCT actually live?** Currently `ConstraintEngine` hardcodes `90 international / 45 domestic` (`src/decision/constraint_engine.py:72`). Should these be: (a) per-edge defaults in the JDG, (b) per-airport MCT from a supplier/airport dataset, or (c) mutable per-agency config? The design proposes edge-level, but the *source* of authoritative MCT is undecided. **Revisit trigger:** when real GDS/airport MCT data becomes available.

3. **Is a hotel a point or an interval node?** The design proposes `HOTEL_STAY` as a duration node. This affects how hotel loss cascades across days. Needs product confirmation on how hotels are represented in `booking_data` today.

4. **What is the traveler overlay key?** The per-traveler "who is affected" dimension needs a stable traveler id. `booking_data.travelers` is a list; there is no confirmed per-traveler id in all cases. Falls back to "all travelers" when undefined (as `SafetyAlertAgent` already does at `runtime.py:2852`).

5. **Who owns the IROPS trigger decision?** A new `IROPSRippleAgent` in the runtime registry (Proposed) vs a direct endpoint on `constraints.py`. The agent pattern matches existing behavior (`FlightStatusAgent`) and gives idempotency + audit; the endpoint is more synchro/IOPS-debuggable. The design leans agent, but this is a composition decision for an owner.

6. **Severity/cost calibration.** The `failure_cost` weights and the `critical/high/medium/low` thresholds are **Proposed and uncalibrated**. They need real operational data (actual rebooking costs, penalty rates) to be decision-grade. Until then they are thresholds-for-monitoring, not thresholds-for-authority.

7. **Diamond-path compounding.** When a downstream node is reachable by two delayed upstream paths, the design keeps the worst deficit. Is "worst" the right aggregation, or should costs compound fully? Needs a small model test with real topology to confirm.

### 9.2 Stopping rules (when to stop / not pursue further)

- **Stop building the JDG as a schema.** The schema exists (`src/schemas/journey_graph.py`) and is adequate for v0. Further schema work before wiring is doctrine-antithetical (§7 — don't add capacity before composition). The first deliverable is **composition and reachability**, not more data classes.
- **Do not add an LLM to the ripple computation.** The propagation is deterministic arithmetic over a temporal graph. Inserting an LLM into this slot would violate the doctrine's deterministic-core boundary (§5.2 of the Aug-24 audit, §7 here). LLM is reserved for *interpretation/copy-generation* of the report, never the *computation*.
- **Do not build the recovery/optimizer under this task.** It is a separate, larger scope; the JDG ends at *detection + severity + recommended action*. If the work starts authoring rebooking search, stop and re-scope.
- **Do not fabricate live-connectivity assumptions.** If a node's time/schedule comes from an `ASSUMED` slot (not a confirmed booking), the report must mark it `ASSUMED` and degrade severity, exactly as the `reality_tier` / `epistemic_status` honesty layer demands. A clean JDG report over fabricated schedules is worse than no report.
- **Do not over-model.** Hotels as duration nodes, traveler overlays, and per-edge weights are enough. Do not add sub-day granularity, weather-likelihood probabilities, or stochastic Monte-Carlo simulation unless an operator actually consumes that fidelity. Simplicity is a deliverable.
- **Kill criterion:** if after wiring, no operator uses a ripple report to act within a defined period, and no disruption is surfaced earlier than the manual process, the JDG is not earning its complexity — re-scope or retire it.

---

## Appendix A — Ground-Truth Evidence Ledger

| # | Claim | Truth status | Asset & location |
|---|---|---|---|
| A1 | JDG schema + ripple evaluator exist | **Observed** | `src/schemas/journey_graph.py` (full file) |
| A2 | Graph is constructed in a router | **Observed** | `spine_api/routers/constraints.py:32, 111` |
| A3 | `evaluate_disruption()` not wired to any endpoint/agent | **Observed** | only `tests/test_journey_graph.py:63,67` call it; `grep` across `spine_api/` and `src/` shows no call site |
| A4 | Non-flight legs typed as `ACTIVITY`, no edges built | **Observed** | `spine_api/routers/constraints.py:141` |
| A5 | `FlightStatusAgent` produces per-node snapshot only | **Observed** | `src/agents/runtime.py:2555`; writes `flight_status_snapshot` |
| A6 | `ConstraintFeasibilityAgent` consumes only `risk_level` → generic blocker | **Observed** | `src/agents/runtime.py:1936` |
| A7 | Flight-status tool adapters (mock + HTTP) exist | **Observed** | `src/agents/live_tools.py:26,72,236,411` |
| A8 | `EpistemicStatus` / `AssumptionRecord` already exist in packet model | **Observed** | `src/intake/packet_models.py:91,100` |
| A9 | Constraint engine hardcodes MCT (90/45) | **Observed** | `src/decision/constraint_engine.py:72` |
| A10 | Constraint vocabulary exists (HARD/SOFT, MCT/spatial/rooming) | **Observed** | `src/schemas/constraints.py:15` |
| A11 | All agent outputs persist as JSON keys on the trip | **Observed** | `spine_api/models/trips.py:55-66`; `runtime.py:2624` |
| A12 | Agents are registered in `build_default_registry` | **Observed** | `src/agents/runtime.py:3150` |
| A13 | Runtime built via factory in server | **Observed** | `spine_api/services/agent_runtime_factory.py:253`; `spine_api/server.py:305` |
| A14 | R-12 finding: JDG gap for IROPS | **Observed** | `Docs/review/WAYPOINT_OS_REFACTOR_ARCHITECT_AUDIT_2026-08-29.md:130` |

## Appendix B — Verb / Recommendation

**Do not build a new schema.** The JDG prototype exists. The intervention is to **compose and reach it**:

1. Teach the graph builder to emit typed nodes + buffer/sequence edges from the real trip (fix the `ACTIVITY` catch-all), tagging each node with `epistemic_status`.
2. Add an IROPS trigger path — a `IROPSRippleAgent` in `build_default_registry()` fed by `flight_status_snapshot` — that stores `irops_ripple_report` on the trip (JSON key, no migration).
3. Surface the report via a `trip_observability` endpoint / timeline so an operator sees the ripple.
4. Extend the `constraints` router to expose a synchronous `evaluate_disruption` for inspection/debug.
5. Calibrate severity/cost thresholds only after real operational data exists.

This keeps the JDG additive, revertible, deterministic-core, and honest about which nodes are confirmed vs assumed — consistent with the doctrine's §8 (epistemic honesty), §7 (deterministic core), and §1 (remove the real bottleneck first).

*Exploration document. All `Proposed` items are design recommendations until reviewed and authorized; `Observed` items are ground truth from the live checkout.*
