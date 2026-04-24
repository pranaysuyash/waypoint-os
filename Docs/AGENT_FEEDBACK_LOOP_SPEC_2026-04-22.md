# Agent Feedback Loop: Suitability Overrides — Full Specification

**Date:** 2026-04-22
**Status:** Draft
**Author:** Architecture Agent
**Project:** travel_agency_agent (Waypoint OS spine)

---

## 0. Problem Statement

The agent emits risk flags (elderly_mobility_risk, toddler_pacing_risk, margin_risk, suitability flags, etc.) but has **no mechanism to receive human override signals**. When an agent owner, trip lead, or operator disagrees with a risk flag — e.g., "this elderly mobility risk is acceptable, the traveler confirmed fitness" — there is no API to record that decision, no persistence, and no way for the system to learn from it. The `CachedDecision` schema already has `feedback_count` and `success_rate` fields but nothing populates them. The `AutonomyPolicy.learn_from_overrides` flag exists but has no implementation.

This spec closes that gap end-to-end.

---

## 1. API Contract: POST /override

### 1.1 Endpoint

```
POST /trips/{trip_id}/override
```

Overrides are scoped to a trip because that is the atomic unit of operator interaction. An override targets one or more risk flags on a specific trip.

### 1.2 Request Schema

```python
class OverrideRequest(BaseModel):
    # --- Core fields ---
    flag: str                          # Risk flag being overridden, e.g. "elderly_mobility_risk"
    decision_type: Optional[str]       # Hybrid engine decision_type, e.g. "elderly_mobility_risk"
                                       # (same as flag when flag == decision_type, differs for "margin_risk" → "budget_feasibility")

    # --- Override semantics ---
    action: Literal["suppress", "downgrade", "acknowledge"]
    #  suppress:   Remove the flag entirely for this trip. Agent must not re-emit it.
    #  downgrade:  Lower severity. Requires new_severity.
    #  acknowledge: Owner saw flag, chose to proceed anyway. Flag remains visible but annotated.

    new_severity: Optional[Literal["low", "medium", "high", "critical"]] = None
    # Required when action="downgrade". Ignored otherwise.

    # --- Provenance ---
    overridden_by: str                  # User ID (agent, owner, system)
    reason: str                        # Free text justifying the override

    # --- Scope ---
    scope: Literal["this_trip", "pattern"] = "this_trip"
    # this_trip: Override applies only to this trip instance.
    # pattern:   Override should influence future similar cases (feeds learning).

    # --- Validation hint ---
    original_severity: Optional[str]   # Caller's understanding of current severity
                                        # Server validates this matches actual; rejects if stale.

    model_config = {"extra": "forbid"}
```

**Example request:**

```json
{
  "flag": "elderly_mobility_risk",
  "decision_type": "elderly_mobility_risk",
  "action": "suppress",
  "overridden_by": "agent_priya",
  "reason": "Traveler confirmed fitness via video call. No mobility aids needed. Doctor clearance on file.",
  "scope": "pattern",
  "original_severity": "high"
}
```

### 1.3 Response Schema

```python
class OverrideResponse(BaseModel):
    ok: bool
    override_id: str                    # Unique ID, e.g. "ovr_a1b2c3d4"
    trip_id: str
    flag: str
    action: str
    new_severity: Optional[str] = None
    cache_invalidated: bool             # True if the override invalidated a cached decision
    rule_graduated: bool                # True if this override triggered rule graduation
    pattern_learning_queued: bool       # True if scope="pattern" and learning was queued
    warnings: List[str] = []            # Non-fatal warnings, e.g. "conflicting_override_exists"
    audit_event_id: str                # ID of the created audit trail entry
```

**Example response:**

```json
{
  "ok": true,
  "override_id": "ovr_a1b2c3d4e5f6",
  "trip_id": "trip_abc123",
  "flag": "elderly_mobility_risk",
  "action": "suppress",
  "new_severity": null,
  "cache_invalidated": true,
  "rule_graduated": false,
  "pattern_learning_queued": true,
  "warnings": [],
  "audit_event_id": "evt_x7y8z9"
}
```

### 1.4 Error Responses

| Status | Condition | Detail |
|--------|-----------|--------|
| 400 | `action="downgrade"` but `new_severity` missing | `"new_severity required for downgrade action"` |
| 400 | `original_severity` doesn't match actual flag severity | `"Stale override: flag 'elderly_mobility_risk' severity is 'medium', not 'high'"` |
| 400 | Attempting to suppress a `critical` flag that is a safety invariant | `"Cannot suppress safety-invariant flag 'document_risk'. Use 'acknowledge' instead."` |
| 400 | `scope="pattern"` but `learn_from_overrides` is disabled in agency settings | `"Pattern learning disabled in agency autonomy settings"` |
| 404 | Trip not found | `"Trip not found"` |
| 409 | Conflicting override already exists (see §5.1) | `"Conflicting override exists: ovr_xyz (action=suppress). Use PUT /override/{override_id} to revise."` |
| 422 | Invalid `flag` value — not a known risk flag type | `"Unknown flag: 'foo_risk'"` |

### 1.5 Supporting Endpoints

```
GET  /trips/{trip_id}/overrides                    # List all overrides for a trip
GET  /overrides/{override_id}                      # Get a specific override
PUT  /overrides/{override_id}                       # Revise an existing override (same schema as POST, adds `revision_reason`)
DELETE /overrides/{override_id}                    # Soft-delete (marks as rescinded, does not remove from audit trail)
GET  /overrides/patterns?decision_type={type}       # List pattern-scope overrides for a decision type
```

---

## 2. Storage Schema: Override History

### 2.1 Design Principles

- Consistent with existing persistence.py: JSON file-based, one file per trip for overrides, plus a global patterns file.
- Append-immutable for audit integrity. Updates create new revision records; original is never mutated.
- File naming matches existing convention: `ovr_{id}.json`

### 2.2 Directory Structure

```
data/
  overrides/
    per_trip/
      trip_abc123.json              # All overrides for one trip
      trip_def456.json
    patterns/
      elderly_mobility_risk.json    # Pattern-scope overrides aggregated by decision_type
      toddler_pacing_risk.json
      budget_feasibility.json
      composition_risk.json
      visa_timeline_risk.json
    index.json                      # Global index: override_id → (trip_id, file path) lookup
```

### 2.3 Override Record Schema (per_trip file)

```json
{
  "trip_id": "trip_abc123",
  "overrides": [
    {
      "override_id": "ovr_a1b2c3d4",
      "trip_id": "trip_abc123",
      "flag": "elderly_mobility_risk",
      "decision_type": "elderly_mobility_risk",
      "action": "suppress",
      "original_severity": "high",
      "new_severity": null,
      "scope": "pattern",
      "overridden_by": "agent_priya",
      "reason": "Traveler confirmed fitness via video call...",
      "created_at": "2026-04-22T10:14:00Z",
      "updated_at": "2026-04-22T10:14:00Z",
      "rescinded": false,
      "rescinded_at": null,
      "rescinded_by": null,
      "revisions": [],
      "audit_event_ids": ["evt_x7y8z9"],
      "cache_key_invalidated": "abc12345...",   # The cache key that was invalidated, if any
      "influenced_rule_graduation": false
    }
  ]
}
```

### 2.4 Pattern Override Record Schema (patterns directory)

One file per `decision_type`. Contains the aggregated learning signal:

```json
{
  "decision_type": "elderly_mobility_risk",
  "pattern_overrides": [
    {
      "pattern_id": "pat_m1n2o3",
      "override_id": "ovr_a1b2c3d4",
      "trip_id": "trip_abc123",
      "flag": "elderly_mobility_risk",
      "action": "suppress",
      "original_severity": "high",
      "override_reason": "Traveler confirmed fitness via video call...",
      "created_at": "2026-04-22T10:14:00Z",
      "context_signature": {
        "destination": "Maldives",
        "has_elderly": true,
        "elderly_count": 1
      },
      "cache_key_prefix": "abc12345",
      "strength": 1,
      "confirmed_by_later_runs": 0
    }
  ],
  "last_compiled_at": "2026-04-22T10:14:00Z"
}
```

The `context_signature` mirrors the fields from `cache_key.py`'s `_get_relevant_fields()` for that decision type. This enables pattern matching: "when we see these same context features, we know this was overridden before."

### 2.5 OverrideStore Class

Following the existing persistence.py pattern (static methods, JSON file I/O):

```python
class OverrideStore:
    """File-based override storage using JSON."""

    OVERRIDES_DIR = DATA_DIR / "overrides"
    PER_TRIP_DIR  = OVERRIDES_DIR / "per_trip"
    PATTERNS_DIR  = OVERRIDES_DIR / "overrides" / "patterns"
    INDEX_FILE    = OVERRIDES_DIR / "index.json"

    @staticmethod
    def save_override(override_data: dict) -> str:
        """Save an override, returns override_id."""

    @staticmethod
    def get_overrides_for_trip(trip_id: str) -> list:
        """List all active overrides for a trip."""

    @staticmethod
    def get_override(override_id: str) -> Optional[dict]:
        """Get a specific override by ID."""

    @staticmethod
    def revise_override(override_id: str, updates: dict) -> Optional[dict]:
        """Append a revision to an existing override (immutable original)."""

    @staticmethod
    def rescind_override(override_id: str, rescinded_by: str) -> Optional[dict]:
        """Soft-delete: mark as rescinded. Does not remove from history."""

    @staticmethod
    def get_pattern_overrides(decision_type: str) -> list:
        """Get all pattern-scope overrides for a decision type."""

    @staticmethod
    def add_pattern_override(decision_type: str, override: dict) -> None:
        """Add an override to the pattern file for its decision type."""

    @staticmethod
    def get_active_overrides_for_flag(trip_id: str, flag: str) -> list:
        """Get non-rescinded overrides for a specific flag on a trip."""
```

---

## 3. decision.py: Incorporating Past Overrides into Future Scoring

### 3.1 New Function: `apply_override_adjustments()`

This function runs **after** `generate_risk_flags()` but **before** the `DecisionResult` is returned. It modifies the risk_flags list and optionally adjusts confidence.

```python
def apply_override_adjustments(
    risk_flags: List[Dict[str, Any]],
    trip_id: str,
    packet: CanonicalPacket,
    agency_settings: Optional[AgencySettings] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply stored overrides to risk flags.

    Returns:
        (adjusted_risk_flags, override_metadata)
        where override_metadata contains what was applied for audit/rationale.
    """
```

### 3.2 Processing Logic

For each risk flag in the list:

1. **Check trip-level overrides:** Query `OverrideStore.get_active_overrides_for_flag(trip_id, flag_name)`.

2. If a `suppress` override exists:
   - Remove the flag from the list.
   - Add `override_applied: {override_id, action: "suppress"}` to the override_metadata.

3. If a `downgrade` override exists:
   - Change `flag.severity` to `new_severity` from the override.
   - If `new_severity` is "low", also consider removing it (configurable via agency_settings).
   - Annotate the flag with `override_applied: {override_id, action: "downgrade", original_severity: ...}`.

4. If an `acknowledge` override exists:
   - Keep the flag as-is.
   - Annotate with `override_applied: {override_id, action: "acknowledge"}`.
   - This prevents the flag from counting toward decision_state escalation (treated as "owner accepted risk").

5. **Pattern overrides:** If no trip-level override exists, check `OverrideStore.get_pattern_overrides(decision_type)` and match against `context_signature` derived from the packet. If a matching pattern exists with `strength >= 2` (confirmed by ≥1 later run):
   - Apply a **soft confidence bonus**: do not remove the flag, but annotate it with `pattern_override_hint: {pattern_id, confidence: "soft"}`.
   - This causes the flag to be deprioritized in decision_state evaluation (treated as advisory rather than blocking).

### 3.3 Integration Point in `run_gap_and_decision()`

Insert after Phase 10 (risk flags generation), before Phase 11:

```python
    # --- Phase 10b: Apply override adjustments ---
    override_metadata = {}
    if agency_settings is None or agency_settings.autonomy.learn_from_overrides:
        risk_flags, override_metadata = apply_override_adjustments(
            risk_flags=risk_flags,
            trip_id=packet.packet_id,  # or the actual trip_id if available
            packet=packet,
            agency_settings=agency_settings,
        )
```

### 3.4 Decision State Re-evaluation

After override adjustments, re-check invariants:

- If a suppression removed the last critical-severity flag, and the decision_state was `STOP_NEEDS_REVIEW` **solely** because of that flag, relax to `ASK_FOLLOWUP`.
- If all risk flags are now `acknowledged`, treat the trip as `PROCEED_INTERNAL_DRAFT` (owner accepted risks).
- **Safety invariants are never overridden**: `document_risk`, `visa_not_applied`, and `traveler_safe_leakage_risk` cannot be suppressed (only acknowledged). This is enforced at the API layer (400 error) and double-checked here.

### 3.5 Rationale Enrichment

The `rationale` dict in `DecisionResult` is extended:

```python
rationale["overrides_applied"] = {
    flag_name: {
        "override_id": override_id,
        "action": action,
        "overridden_by": overridden_by,
        "reason": reason,
    }
    for each applied override
}
rationale["pattern_hints"] = {
    flag_name: {
        "pattern_id": pattern_id,
        "strength": strength,
        "note": "Previously overridden in N similar cases"
    }
    for each applied pattern hint
}
```

---

## 4. hybrid_engine.py: Cache Invalidation & Rule Graduation

### 4.1 Cache Invalidation

When a `suppress` or `downgrade` override is recorded, the cached decision that produced the original risk flag must be invalidated. Otherwise, future identical inputs will hit the cache and re-emit the overridden flag.

**Mechanism:**

1. On override POST, look up the trip's `run_id` from the trip data.
2. From the run's checkpointed decision step, find the `cache_key` for the relevant `decision_type`. This is stored in the `DecisionResult.source = "cache"` path — the hybrid engine already logs which cache key was used.
3. If the cache_key is found, call `cache_storage.invalidate(cache_key, decision_type)`.
4. New method on `DecisionCacheStorage`:

```python
def invalidate(self, cache_key: str, decision_type: str) -> bool:
    """
    Remove a cached decision. Returns True if entry existed and was removed.

    For safety, also decrements the global success_rate for entries
    with the same decision_type (signals to future cache validity checks
    that this decision path may be unreliable).
    """
```

5. Alternative (softer): instead of full invalidation, call `CachedDecision.record_feedback(success=False)`. This lowers the `success_rate` for that cache entry. If `success_rate < min_success_rate` (default 0.7), the entry is no longer served from cache (`is_valid()` returns False), causing a cache miss on the next identical query. The LLM or rules will re-evaluate.

**Recommended approach:** Use `record_feedback(success=False)` as the primary mechanism. This is:
- Incremental (not destructive).
- Composable (multiple overrides on the same pattern compound).
- Already built into the `CachedDecision.is_valid()` check.

Only call full `invalidate()` for `action="suppress"` when the override reason indicates the original decision was fundamentally wrong (not just context-dependent).

### 4.2 Rule Graduation

When an override with `scope="pattern"` is recorded, and the same context signature accumulates **3+ overrides** (configurable, `GRADUATION_THRESHOLD`), the system promotes the override into a rule.

**Mechanism:**

1. `OverrideStore.get_pattern_overrides(decision_type)` returns pattern entries.
2. Group by `context_signature` (same relevant fields as cache key generation).
3. When a group reaches `GRADUATION_THRESHOLD` (default: 3):
   - Auto-generate a rule function in `decision/rules/graduated_rules.py`:

```python
def rule_elderly_mobility_risk_graduated_maldives_1(packet):
    """Graduated from pattern overrides: 3 suppress actions for Maldives+elderly."""
    dest = _extract_value(packet.facts, "destination_candidates")
    has_elderly = _has_composition_member(packet, "elderly")
    if dest and "Maldives" in (dest if isinstance(dest, list) else [dest]) and has_elderly:
        return {
            "risk_level": "low",
            "reasoning": "Pattern override: agency operators consistently accept elderly+Maldives (3+ overrides). Original high-risk assessment may be environment-specific.",
            "recommendations": ["Verify with operator if uncertain"],
        }
    return None  # Rule does not apply to this packet
```

4. Register the graduated rule with the hybrid engine:

```python
engine.register_rule("elderly_mobility_risk", rule_elderly_mobility_risk_graduated_maldives_1)
```

5. The rule executes at step 2 of the `decide()` flow (after cache, before LLM), getting a **₹0 cost** hit and high confidence (0.9).
6. Annotate the `rule_hit` result with source `"graduated_rule"` and metadata `graduated_from_overrides: [override_id, ...]`.

### 4.3 Graduation Guard Rails

- Graduated rules always return `risk_level: "low"` or skip entirely (return None). They never escalate risk — only the original rules/LLM can do that.
- A graduated rule has a **max lifetime** of 90 days (configurable). After that, it auto-expires and must be re-confirmed by continued overrides.
- If an override is **rescinded** that contributed to a graduated rule, the rule's counter decreases. If it drops below threshold, the rule is deregistered.
- Graduated rules are **never safety-invariant overrides**. They cannot affect `document_risk`, `visa_not_applied`, or `traveler_safe_leakage_risk`.

### 4.4 Cache Key Integration for Override Matching

The `generate_cache_key()` function in `cache_key.py` already extracts relevant fields per decision type. The override's `context_signature` uses the **same field extraction**, ensuring that:

- A pattern override for `elderly_mobility_risk` with `context_signature = {destination: "Maldives", has_elderly: true}` will match the same cache key prefix as a future decision hitting the cache/rule flow.
- This allows the `apply_override_adjustments()` function to check: "given the inputs that determined this cache key, do any pattern overrides exist?"

New helper function in `cache_key.py`:

```python
def get_context_signature(decision_type: str, packet: CanonicalPacket) -> Dict[str, Any]:
    """
    Return the relevant fields for a decision type as a context signature.

    This is the same dict used to generate the cache key, but returned
    as a readable dict (not hashed) for override pattern matching.
    """
    return _get_relevant_fields(decision_type, packet)
```

---

## 5. Edge Cases

### 5.1 Conflicting Overrides

**Scenario:** Two agents override the same flag on the same trip differently:
- Agent A: suppress "elderly_mobility_risk" (reason: traveler confirmed fit)
- Agent B: acknowledge "elderly_mobility_risk" (reason: want to keep it visible for tracking)

**Resolution:**

1. The API rejects the second override with **409 Conflict** if it targets the same flag and trip with a different action. The response includes the existing override ID.
2. To resolve, the second agent must either:
   - Use `PUT /overrides/{override_id}` to revise the existing override (requires appropriate permissions).
   - Use `POST /override` with a `force: bool = False` flag (default False) to explicitly opt in to override-of-override.
3. If `force=true`, the new override supersedes the old one. The old override is marked `superseded_by: new_override_id` in the per_trip file. Both remain in the audit trail.

**Precedence rules (when multiple overrides exist for the same flag):**
1. Most recent non-rescinded override wins.
2. `suppress` > `downgrade` > `acknowledge` (most impactful action takes precedence).
3. A `rescind` on the most recent override reverts to the previous override.

### 5.2 Override on a Flag That No Longer Exists

**Scenario:** An override is recorded for "elderly_mobility_risk" but the next spine run doesn't emit that flag (because the packet context changed — e.g., the elderly traveler was removed from party composition).

**Resolution:**
- The override remains stored but has no effect (vacuously true — there's nothing to adjust).
- The override's `cache_key_invalidated` flag remains set, so the cached decision for that key is still degraded.
- On the next run, if the flag re-appears (different trip, same pattern), the pattern override can still match.

### 5.3 Stale Severity (Optimistic Concurrency)

**Scenario:** Agent sees severity="high" in the UI, but a concurrent spine run already downgraded it to "medium" before the override request arrives.

**Resolution:**
- The `original_severity` field in the request is validated against the actual current severity.
- If mismatched, return 400 with the actual severity. The agent UI must refresh and re-submit.
- This prevents accidentally suppressing a flag that was already downgraded or removed.

### 5.4 Safety Invariant Flags Cannot Be Suppressed

**Hard rule:** These flags can only be `acknowledged`, never `suppressed` or `downgrade`d:
- `document_risk` (expired passport)
- `visa_not_applied` (visa required but not applied)
- `traveler_safe_leakage_risk` (internal data leakage)

At the API layer, a suppress/downgrade for these returns 400. In `apply_override_adjustments()`, even if the override somehow got through storage, the function double-checks and ignores invalid actions.

### 5.5 Audit Trail Integrity

**Requirements:**
1. Every override creates an `AuditStore.log_event("override_created", ...)` entry.
2. Revisions create `AuditStore.log_event("override_revised", ...)` entries.
3. Rescissions create `AuditStore.log_event("override_rescinded", ...)` entries.
4. Overrides are **never hard-deleted** from storage. The `rescinded` flag is the deletion mechanism.
5. All audit events include: `override_id`, `trip_id`, `flag`, `action`, `overridden_by`, `reason`, timestamp.
6. Even invalidated overrides remain in the audit trail — they tell a story of human judgment history.

### 5.6 Concurrent Override + Spine Run

**Scenario:** While a spine run is in progress, an override is posted for the same trip.

**Resolution:**
- The current spine run completes with the old risk flags (no mid-run intervention).
- On the **next** spine run for that trip, the override is picked up by `apply_override_adjustments()`.
- The response from POST /override includes `effective_on_next_run: true` to make this clear.

### 5.7 Pattern Override Scope Creep

**Scenario:** An operator sets `scope="pattern"` for "elderly_mobility_risk" on Maldives, but the reason was trip-specific (traveler is a doctor). The pattern learning should not generalize this.

**Mitigation:**
1. The `reason` field is stored and available for review in pattern overrides.
2. Pattern overrides require `strength >= 2` (multiple independent confirmations) before influencing scoring.
3. A "pattern review" endpoint `GET /overrides/patterns?decision_type={type}&review_required=true` lists patterns that have only 1 confirmation and might be premature.
4. Agency can set `learn_from_overrides: false` to disable pattern learning entirely.
5. Graduated rules (strength 3+) have a 90-day expiry and must be re-confirmed.

### 5.8 Override on a Cached Decision That No Longer Exists

**Scenario:** An override targets a cache entry, but the cache entry has already been evicted due to TTL or low success_rate.

**Resolution:**
- The `record_feedback(success=False)` call is a no-op if the cache key doesn't exist. This is fine — there's nothing to invalidate.
- The override is still stored (for audit and pattern learning). Future runs will use rules/LLM and may produce a lower severity naturally.

### 5.9 Multiple Decision Types Sharing a Flag

**Scenario:** The flag `margin_risk` comes from `decision_type = "budget_feasibility"` in the hybrid engine, but is generated from `check_budget_feasibility()` in the non-hybrid path.

**Resolution:**
- The override request has both `flag` (what the operator sees) and `decision_type` (what the hybrid engine uses). The server maps between them using the existing `flag_map` in `_generate_risk_flags_with_hybrid_engine()`:
  ```python
  flag_map = {
      "elderly_mobility_risk": "elderly_mobility_risk",
      "toddler_pacing_risk": "toddler_pacing_risk",
      "composition_risk": "composition_risk",
      "visa_timeline_risk": "visa_timeline_risk",
      "margin_risk": "budget_feasibility",
  }
  ```
- If `decision_type` is not provided, the server looks it up from `flag_map`.

---

## 6. Configuration

### 6.1 New Agency Settings Fields

Added to `AutonomyPolicy` in `agency_settings.py`:

```python
@dataclass
class AutonomyPolicy:
    # ... existing fields ...

    # Override feedback configuration
    learn_from_overrides: bool = True
    override_graduation_threshold: int = 3      # Overrides before pattern → rule
    override_pattern_min_strength: int = 2       # Min confirmations before pattern affects scoring
    graduated_rule_ttl_days: int = 90            # Auto-expire graduated rules
    allow_suppress_safety_flags: bool = False    # Always False; safety invariant
    override_concurrency_mode: str = "reject"   # "reject" | "force" | "latest_wins"
```

### 6.2 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OVERRIDE_STORAGE_DIR` | `data/overrides` | Override storage root |
| `OVERRIDE_MAX_PER_TRIP` | `50` | Max overrides per trip before archival |
| `GRADUATION_THRESHOLD` | `3` | Pattern overrides before rule graduation |
| `GRADUATED_RULE_TTL_DAYS` | `90` | Lifetime of graduated rules |

---

## 7. Implementation Phases

### Phase 1: Foundation (Week 1)
- `OverrideStore` class (persistence)
- `POST /trips/{trip_id}/override` endpoint
- `GET /trips/{trip_id}/overrides` endpoint
- Audit trail integration
- `apply_override_adjustments()` in decision.py (trip-level only)

### Phase 2: Cache Integration (Week 2)
- `record_feedback(success=False)` on override
- Cache key → override mapping
- `context_signature` extraction from cache_key.py
- Pattern override storage & retrieval

### Phase 3: Pattern Learning (Week 3)
- Pattern override matching in `apply_override_adjustments()`
- Graduated rule generation & registration
- Rule expiry mechanism
- Pattern review endpoint

### Phase 4: UI & Polish (Week 4)
- Frontend override controls in Next.js
- Override history panel on trip detail page
- Pattern management in agency settings
- Conflict resolution UX

---

## 8. Testing Strategy

### 8.1 Unit Tests

| Test | Validates |
|------|-----------|
| `test_override_suppress_removes_flag` | suppress action removes flag from risk_flags |
| `test_override_downgrade_changes_severity` | downgrade action changes severity |
| `test_override_acknowledge_keeps_flag` | acknowledge action annotates but preserves |
| `test_safety_flag_cannot_be_suppressed` | 400 on suppress for document_risk, etc. |
| `test_conflicting_override_rejected` | 409 when duplicate flag override exists |
| `test_stale_severity_rejected` | 400 when original_severity mismatches |
| `test_pattern_override_requires_min_strength` | No effect until strength >= 2 |
| `test_graduated_rule_registered_after_threshold` | Rule registered at threshold |
| `test_graduated_rule_expires` | Rule deregistered after TTL |
| `test_rescind_decrements_graduation_counter` | Counter drops, rule may be deregistered |

### 8.2 Integration Tests

| Test | Validates |
|------|-----------|
| `test_full_override_lifecycle` | POST → storage → apply → re-run → verify adjusted |
| `test_override_invalidates_cache` | Override → cache miss on next run |
| `test_pattern_learning_end_to_end` | 3 overrides → graduated rule → rule hit on next run |
| `test_concurrent_spine_run_and_override` | Override applied on next run, not current |
| `test_audit_trail_complete` | All override actions have audit entries |

---

## 9. Security Considerations

1. **Authorization:** Override endpoint should eventually require role-based access. Initially, `overridden_by` is trusted. Future: JWT with `role: owner | agent | system`.
2. **Immutability:** Override records are append-only. Revisions create new records; originals are preserved.
3. **Safety invariants:** Cannot be bypassed by override API regardless of authorization.
4. **Rate limiting:** Max N overrides per trip per hour (prevent override spam).
5. **Data isolation:** Override storage is server-side only. Never included in `traveler_bundle` (leakage boundary).

---

## 10. Summary of Data Flow

```
                ┌──────────────────────┐
                │  POST /override      │
                │  (operator action)  │
                └──────────┬───────────┘
                           │
              ┌────────────▼────────────┐
              │  OverrideStore.save()  │
              │  + AuditStore.log()   │
              └──────┬─────────┬──────┘
                     │         │
          ┌──────────▼──┐  ┌───▼──────────────┐
          │ per_trip/   │  │ patterns/         │
          │ trip_id.json│  │ decision_type.json│
          └─────────────┘  └──────┬───────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  Cache invalidation        │
                    │  CachedDecision             │
                    │  .record_feedback(False)    │
                    └─────────────┬──────────────┘
                                  │
              ┌───────────────────▼────────────────────┐
              │  Next spine run: run_gap_and_decision() │
              │                                         │
              │  1. generate_risk_flags()                │
              │  2. apply_override_adjustments()        │
              │     ├── Check per_trip overrides        │
              │     ├── Check pattern overrides         │
              │     ├── Apply suppress/downgrade/ack    │
              │     └── Re-evaluate decision_state      │
              │  3. Return DecisionResult                │
              │     with rationale.overrides_applied     │
              └────────────────────┬───────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Pattern strength check      │
                    │  If threshold reached:       │
                    │  → Generate graduated rule   │
                    │  → Register in hybrid engine │
                    └─────────────────────────────┘
```

---

## Appendix A: Flag → Decision Type Mapping (Authoritative)

```python
FLAG_TO_DECISION_TYPE = {
    "elderly_mobility_risk": "elderly_mobility_risk",
    "toddler_pacing_risk": "toddler_pacing_risk",
    "composition_risk": "composition_risk",
    "visa_timeline_risk": "visa_timeline_risk",
    "margin_risk": "budget_feasibility",
    "coordination_risk": None,           # Not in hybrid engine (always rule-based)
    "traveler_safe_leakage_risk": None,   # Safety invariant, never overridable
    "document_risk": None,                # Safety invariant, never overridable
    "visa_not_applied": None,             # Safety invariant, never overridable
}
```

## Appendix B: Override Action Effect Matrix

| Action | Flag Removed? | Severity Changed? | Counts Toward Decision State? | Learning Signal |
|--------|:---:|:---:|:---:|:---:|
| suppress | Yes | N/A | No | Cache feedback (False) |
| downgrade | No | Yes | Uses new severity | Cache feedback (False) |
| acknowledge | No | No | No (owner accepted) | None (neutral) |

## Appendix C: Files to Create/Modify

| File | Change |
|------|--------|
| `spine_api/server.py` | Add OverrideRequest/OverrideResponse models, POST/GET/PUT/DELETE endpoints |
| `spine_api/persistence.py` | Add `OverrideStore` class |
| `src/intake/decision.py` | Add `apply_override_adjustments()`, integrate into `run_gap_and_decision()` |
| `src/decision/hybrid_engine.py` | Add `invalidate_cache()` helper, graduated rule registration path |
| `src/decision/cache_schema.py` | Already has `record_feedback()`, `is_valid()` — no changes needed |
| `src/decision/cache_key.py` | Add `get_context_signature()` function |
| `src/decision/cache_storage.py` | Add `invalidate()` method |
| `src/intake/config/agency_settings.py` | Add override config fields to `AutonomyPolicy` |
| `src/decision/rules/graduated_rules.py` | New file, auto-generated graduated rules |
|| `data/overrides/` | New directory structure |

---

## Cross-References

| Document | Purpose |
|----------|---------|
| `Frontend_SUITABILITY_DISPLAY_STRATEGY_2026-04-22.md` | Why suitability needs dedicated UI, operational/production/agent analysis |
| `SUITABILITY_PRESENTATION_CONTRACT_2026-04-22.md` | Exact data shapes, `SuitabilityProfile` schema, component spec, implementation phases |

**Status**: This spec defines the override API and agent learning loop. The Presentation Contract defines how the frontend renders the data that triggers overrides. They form a closed loop: backend scores → frontend displays → operator overrides → backend learns.