# Waypoint OS Pre-Mortem: AGENT/LLM PIPELINE RELIABILITY
## Role: Saboteur | Register: Cold Glee
## Date: 2026-05-05

> "The seam is never where they reinforced it. It's where two systems touch and
> neither one owns the handshake."

---

## FAILURE 1: LLM DECIDE() NEVER VALIDATES RETURNED JSON AGAINST THE SCHEMA IT WAS GIVEN

**1. WHAT GOES WRONG:**
All three LLM clients (OpenAI, Gemini, Local) parse JSON from the LLM response and
return it directly without validating that the parsed dict conforms to the `schema`
parameter that was passed in. The schema is stuffed into the prompt as text
instruction, but never used programmatically after `json.loads()` succeeds. This
means any LLM response that is *valid JSON but violates the schema* — missing
required fields, wrong types, extra unexpected structures — flows silently into the
decision pipeline as canonical state.

**2. CHAIN OF EVENTS:**
- Gemini 2.0-flash returns `{"decision": "GO", "confidence": 0.9}` when the schema
  required `{"decision_state": "GO", "risk_flags": [], "blockers": []}`.
- `json.loads()` succeeds. `decide()` returns the malformed dict.
- The `run_gap_and_decision` module reads `decision_state` from the dict — gets None.
- Decision state defaults or falls through to a permissive path.
- A trip that should be STOP_NEEDS_REVIEW gets GO and generates a traveler-facing
  proposal with hard_blockers hidden.

**3. USER EXPERIENCE:**
A traveler receives a quote for a trip that the system internally flagged as unsafe.
The agent appears confident. The operator sees nothing amiss because the escalation
path was never triggered.

**4. EMOTIONAL IMPACT:**
When this surfaces — and it always surfaces through a customer complaint or an
incident — the operator's trust collapses. Not in a feature, but in the *invisible
machinery*. The system was supposed to be the guard. It became the hole.

**5. WHY TEAM MISSES IT:**
- The prompt says "Respond ONLY with the JSON object matching this schema." The team
  treats that as a contract, not a suggestion.
- `response_format={"type": "json_object"}` in OpenAI only enforces *valid JSON*, not
  schema conformance. The team conflates the two.
- Tests use small schemas where the LLM almost always complies.
- No schema validation library (jsonschema, pydantic) is imported anywhere in the
  LLM client layer.

**6. LIKELIHOOD x IMPACT:**
Likelihood: HIGH (Gemini and GPT-4o-mini routinely omit or rename fields in
structured output, especially under temperature=0.3 with complex schemas).
Impact: CRITICAL (silent decision bypass).
Score: 9/10.

**7. TRUST DAMAGE:**
Catastrophic. This is not a timeout or a retry — it is the system making a different
decision than it reports. Trust does not recover from "you said GO but meant STOP."

**8. RECOVERABILITY:**
Recovery requires reprocessing all trips since the last known-good LLM response
validation point. No such checkpoint exists. Manual audit of every decision output
is the only path.

**9. EARLIEST SIGNAL:**
- Logs showing `decision_state: None` in SpineResult after a successful LLM call.
- Any LLM response where parsed keys don't match schema keys.
- Fixture assertions failing intermittently on `decision_state_in` checks.

**10. VERIFY BY:**
- Add instrumentation that diffs every `decide()` return dict against its input
  schema. Run 500 calls with production-like schemas and count violations.
- Check production logs for `None` defaults in decision_state after Gemini calls.

---

## FAILURE 2: RECOVERY AGENT REQUEUE COUNTS LIVE IN MEMORY — RESTART ERASES STATE, RE-TRIGGERS ESCALATION CASCADE

**1. WHAT GOES WRONG:**
`RecoveryAgent._requeue_counts` is a plain `dict[str, int]` initialized empty in
`__init__`. On process restart (container redeploy, crash recovery, OOM kill), this
dict is wiped. Every trip that was previously re-queued once gets detected as stuck
again with `requeue_attempts=0`. The agent re-queues them. If the reason they were
stuck is still present, they fail again and get re-queued a second time. Now the
agent *thinks* the first requeue was the first attempt, when it was actually the
third or fourth. Trips cycle through requeue → fail → restart → requeue without
ever reaching the `MAX_REQUEUE_ATTEMPTS=2` threshold that triggers escalation.
They are stuck *permanently* in a requeue loop, invisible to escalation.

**2. CHAIN OF EVENTS:**
- Container restarts at 3:00 AM (normal deploy cycle).
- RecoveryAgent starts, reads trips, finds 12 stuck trips.
- All have `requeue_attempts=0` in the fresh in-memory dict.
- Agent re-queues all 12, incrementing its dict to `{trip_id: 1}`.
- The underlying issue (e.g. a schema validation bug) causes all 12 to fail again.
- Container restarts again at 3:05 AM (OOM from processing retries).
- Dict wiped again. All 12 look like `requeue_attempts=0` again.
- This loop runs indefinitely because `MAX_REQUEUE_ATTEMPTS=2` is never reached.

**3. USER EXPERIENCE:**
Operators see the same 12 trips flagged, "resolved" (re-queued), and then stuck
again, repeatedly. The system appears to be doing work but nothing progresses.
Escalation tickets are never created. The operator dashboard shows "recovery active"
green status while trips rot.

**4. EMOTIONAL IMPACT:**
The glee here is watching a recovery system that thinks it's recovering but is
actually just burning CPU cycles in a loop. It's the software equivalent of
turning the ignition on a flooded engine — more fuel, no spark, no progress.

**5. WHY TEAM MISSES IT:**
- The code comment says "In-memory tracking of requeue attempts per trip (cleared
  on restart)" — the team documented the gap as if it were a feature.
- Tests use `run_once()` which doesn't test restart behavior.
- The `stuck` detection reads `updated_at` from the trip repo, but the requeue
  *updates* `updated_at`, so the trip no longer looks stuck after requeue.

**6. LIKELIHOOD x IMPACT:**
Likelihood: HIGH (any container restart during stuck-trip recovery triggers this).
Impact: HIGH (trips permanently stuck without escalation).
Score: 8/10.

**7. TRUST DAMAGE:**
Operators learn the "recovery" agent is decorative. They stop trusting any green
status indicator. They build manual checklists around the system.

**8. RECOVERABILITY:**
Requires identifying all trips that have been re-queued more than MAX_REQUEUE_ATTEMPTS
by cross-referencing audit logs. Then manually escalating each one. The audit trail
exists but the automated escalation path was bypassed.

**9. EARLIEST SIGNAL:**
- Same trip_id appearing in recovery pass logs across multiple container restarts.
- `requeue_attempts=0` appearing for trips that were previously re-queued.
- Audit log showing `re_queue` action for the same trip > 2 times.

**10. VERIFY BY:**
- Restart the process while trips are stuck and verify requeue_counts resets.
- Count audit log entries for `re_queue` action on the same trip_id.
- Check if any trip ever reaches `escalate` action in a deployment with daily
  restarts.

---

## FAILURE 3: LLM FALLBACK CHAIN DOES NOT EXIST — WHEN PRIMARY LLM IS DOWN, THE SYSTEM SILENTLY FAILS OR HANGS

**1. WHAT GOES WRONG:**
Each LLM client (`GeminiClient`, `OpenAIClient`, `LocalLLMClient`) is instantiated
independently. There is no `HybridDecisionEngine`, no fallback chain, no
circuit-breaker pattern in the LLM client layer. The `LLMUsageGuard` checks
budget and rate limits *before* a call, but if the actual API call fails after
the guard allows it, the code path raises `LLMUnavailableError` or
`LLMResponseError` and the caller must handle it. Examining `orchestration.py`,
the spine wraps LLM-impacting phases in `try/except` that re-raises — meaning a
Gemini outage kills the entire spine run with no fallback.

The `decide()` methods catch *all* non-LLM exceptions and re-wrap them as
`LLMUnavailableError`, losing the original error category. There's no retry at
the LLM client level, no exponential backoff, no fallback to a secondary model.

**2. CHAIN OF EVENTS:**
- Google Gemini API has a 15-minute partial outage (common; happened multiple times
  in 2025).
- `GeminiClient.decide()` raises `LLMUnavailableError("Gemini API call failed: 503")`.
- The spine's decision phase catches and re-raises.
- `run_spine_once()` raises the exception.
- The Streamlit app shows a generic error.
- All intake processing halts. No trips are processed. No front-door assessments.
  No follow-ups.
- 15 minutes of trip inquiries pile up with zero system response.

**3. USER EXPERIENCE:**
The agency operator sees a Streamlit error screen. Travelers who submitted
inquiries during the outage get no acknowledgment — the front door agent never
runs. The system is entirely down because one API provider is down.

**4. EMOTIONAL IMPACT:**
The solo founder watching their B2B product go completely dark because a
third-party API had a 15-minute blip. Every moment of downtime is a moment a
travel agency client could switch to a competitor. The helplessness is the
product failing in a way the founder cannot fix — they can't fix Google.

**5. WHY TEAM MISSES IT:**
- The `BaseLLMClient` abstract class has no fallback infrastructure.
- Tests mock the LLM client, so outage scenarios are never tested.
- The codebase references a "hybrid decision engine" in comments but never
  implements one.
- The `LLMUsageGuard` only guards *before* the call — there's no post-call
  failure handling architecture.
- The team is pre-launch and hasn't experienced a real API outage yet.

**6. LIKELIHOOD x IMPACT:**
Likelihood: CERTAIN (every cloud LLM provider has outages measured in hours/month).
Impact: CRITICAL (complete system stoppage).
Score: 10/10.

**7. TRUST DAMAGE:**
Total. A B2B tool that goes completely dark when a single upstream API hiccups
is not enterprise-ready. The first customer who experiences this will not renew.

**8. RECOVERABILITY:**
After the outage resolves, all queued trips must be manually reprocessed. But
there's no queue — the requests failed immediately. They're just gone.

**9. EARLIEST SIGNAL:**
- Any 5xx from Gemini/OpenAI in production logs.
- `run_spine_once` raising exceptions in monitoring.
- Zero trips processed in any 5-minute window.

**10. VERIFY BY:**
- Disconnect network during a spine run and observe behavior.
- Add a 5-minute Gemini API outage to staging and count failed trips.
- Check if any code path retries or falls back on LLM unavailable.

---

## FAILURE 4: PRIVACY GUARD IS A GATE THAT TELLS YOU WHERE THE WALL IS — AND THERE'S NO WALL ON THE OTHER SIDE

**1. WHAT GOES WRONG:**
The `PrivacyGuard` in `dogfood` mode blocks persistence of real-user PII to
plaintext JSON. That's the only enforcement point. But the LLM clients receive
the *full trip data including PII* before the guard ever checks. The prompt
pipeline in `orchestration.py` sends raw trip text through extraction, decision,
and strategy phases before the privacy guard runs at the *persistence* boundary.
The `build_internal_bundle()` and `build_traveler_safe_bundle()` are built *after*
the LLM has already seen and processed the data. Gemini and OpenAI APIs have
received traveler names, emails, medical conditions, and phone numbers in the
prompt — the guard only stops *storing* the result.

Even in `beta` and `production` modes, `check_trip_data()` returns immediately
without blocking. The comment says "encryption should be active" but the
encryption module uses a hardcoded development key as fallback: the literal
string `'v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8='`.

The `decrypt()` function on failure *returns the original token as plaintext*.
If the ENCRYPTION_KEY env var is unset (common in staging), or rotates, all
encrypted data silently becomes readable as plaintext fallback.

**2. CHAIN OF EVENTS:**
- A boutique agency operator submits a real trip inquiry with traveler names,
  dates, medical requirements.
- Privacy guard in `dogfood` mode would block persistence — but the operator
  set `DATA_PRIVACY_MODE=beta` to test with real data.
- Guard returns immediately. No block.
- The full traveler data is sent to Gemini API as prompt content.
- Gemini processes it. The response comes back.
- The result is stored with the hardcoded development key encryption.
- A few weeks later, the ENCRYPTION_KEY env var is added and the old data
  can't be decrypted — but `decrypt()` falls back to returning the original
  plaintext token. The "encrypted" data is just plaintext with a Fernet wrapper
  that fails gracefully to exposure.

**3. USER EXPERIENCE:**
No visible failure. The system works. Traveler data flows through Gemini. The
operator is unaware that PII left their infrastructure. Nothing breaks — which
is the worst kind of privacy failure, because there's no signal.

**4. EMOTIONAL IMPACT:**
This isn't a bug that crashes. It's a quiet drain. The privacy guard gives the
team a false sense of security. When a customer asks "where does our data go?",
the honest answer includes "through Google's API as prompt text, encrypted with
a key that's hardcoded in the source code." The founder can't say this. The
customer can't trust this.

**5. WHY TEAM MISSES IT:**
- The privacy guard *works* in dogfood mode. Tests pass.
- The guard is tested at the persistence boundary, not at the LLM call boundary.
- The hardcoded key has a comment: "stable development key in non-production modes."
- The `decrypt()` fallback is documented as a feature for "old data."
- Nobody has traced the data flow from intake to LLM prompt content.

**6. LIKELIHOOD x IMPACT:**
Likelihood: CERTAIN (every real trip sends PII to external LLMs).
Impact: CRITICAL (PII exfiltration to third parties, encryption bypass).
Score: 10/10.

**7. TRUST DAMAGE:**
Existential for a B2B product. A travel agency's core obligation is traveler
data protection. If PII flows to Gemini/OpenAI without disclosure, the agency
is in violation of their own privacy policy and potentially GDPR/Indian DPDP
obligations.

**8. RECOVERABILITY:**
Not recoverable for already-sent data. Google has already received and
processed the prompts. The only recovery is disclosure, policy changes, and
rebuilding the LLM pipeline to sanitize before external calls.

**9. EARLIEST SIGNAL:**
- Any prompt log or telemetry that shows traveler names in LLM API calls.
- The `ENCRYPTION_KEY` env var not being set in any non-dogfood deployment.
- Test coverage that only checks `check_trip_data()` but never checks what
  data is sent to `decide()`.

**10. VERIFY BY:**
- Trace a real trip (with email, phone, medical notes) from intake to LLM
  prompt. Check if PrivacyGuard runs before or after the LLM call.
- Set DATA_PRIVACY_MODE=beta. Run a spine. Check what Gemini received.
- Unset ENCRYPTION_KEY. Try decrypting stored data.

---

## FAILURE 5: USAGE GUARD RESERVATION LEAK — EVERY CRASHED LLM CALL LEAVES A "RESERVED" ROW FOREVER INFLATING DAILY COST

**1. WHAT GOES WRONG:**
The `LLMUsageGuard.check_before_call()` inserts a `status='reserved'` row in
the usage_events table. After the LLM call, `record_call()` finalizes the
reservation to `status='completed'` or `status='failed'`. But if the process
crashes, OOMs, or has an unhandled exception between `check_before_call()` and
`record_call()`, the row stays as `status='reserved'` forever.

The `check_and_reserve()` SQL calculates daily cost using:
```sql
COALESCE(SUM(CASE WHEN status IN ('reserved','completed') THEN 
  actual_cost ELSE estimated_cost END), 0) AS daily_cost
```

A `reserved` row with `actual_cost=NULL` falls through to `estimated_cost`. Since
`estimated_cost` is always set (the caller provides it), these orphaned reservations
contribute phantom cost to the daily budget calculation. If the estimated cost is
deliberately conservative (high) — as it should be — the phantom cost accumulates
faster than real cost.

Process crashes during LLM calls leave dozens of orphaned reservations per day. After
a week, the daily cost calculation includes phantom reservations from previous days
that were never finalized. The guard thinks the agency has spent more than it
actually did.

**2. CHAIN OF EVENTS:**
- An LLM call starts. Guard reserves ₹0.50 estimated cost.
- Process OOMs during inference. Container restarts.
- The reserved row is now orphaned with `actual_cost=NULL`, `status='reserved'`.
- Next guard check includes this phantom ₹0.50 in the daily cost.
- After 20 crashes in a day, phantom cost is ₹10.00 against a ₹50.00 daily budget.
- The guard blocks real calls at ₹40.00 actual spend because it projects ₹50.00
  including ₹10.00 phantom.
- Budget mode "block" prevents further LLM calls with 20% budget to spare.

**3. USER EXPERIENCE:**
The system stops processing trips with a "daily budget exceeded" error even though
actual spend is well within limits. The operator can't figure out why. There's no
dashboard showing reserved vs. completed costs. The system is silently throttling
itself.

**4. EMOTIONAL IMPACT:**
The budget guard was supposed to be a safety net. Instead it becomes a
self-imposed choke collar that tightens with every crash. The system punishes
itself for its own instability.

**5. WHY TEAM MISSES IT:**
- Tests always call `record_call()` after `check_before_call()`. No test simulates
  a crash between the two.
- The SQL query intentionally counts 'reserved' as real spend — that's the
  fail-closed design principle. But fail-closed without garbage collection is
  just a slow leak.
- No TTL or sweep mechanism exists for orphaned reservations.
- The InMemoryUsageStore tests don't match the SQLite store's SQL exactly.

**6. LIKELIHOOD x IMPACT:**
Likelihood: MEDIUM-HIGH (depends on crash frequency; OOMs in local LLM are common).
Impact: HIGH (budget exhaustion from phantom spend).
Score: 7/10.

**7. TRUST DAMAGE:**
Moderate. The system appears unreliable for budgeting. Agencies paying for an
AI copilot that stops working before its budget is spent will question the
value proposition.

**8. RECOVERABILITY:**
Requires a manual SQL update: `UPDATE usage_events SET status='failed',
actual_cost=0 WHERE status='reserved' AND created_at < now() - interval '1 hour'`.
Or a background sweeper process that doesn't exist yet.

**9. EARLIEST SIGNAL:**
- `daily_cost` from `get_state()` exceeding actual API invoices.
- `status='reserved'` rows in usage_events with `actual_cost IS NULL` and
  `created_at` older than 1 hour.
- Budget block events with projected cost higher than invoice cost.

**10. VERIFY BY:**
- Kill the process after `check_before_call()` but before `record_call()`.
- Check the usage_events table for orphaned reservations.
- Run `get_state()` daily_cost and compare to actual API spend.

---

## FAILURE 6: INMEMORYWORKCOORDINATOR LEASE EXPIRY CREATES INVISIBLE DUPLICATE EXECUTION

**1. WHAT GOES WRONG:**
`InMemoryWorkCoordinator.acquire()` grants a lease with `leased_until =
now + lease_seconds` (default 60s). If an agent execution takes longer than
60 seconds — which is realistic for the DocumentReadinessAgent or any agent
making live HTTP tool calls — the lease expires while execution is still
running. On the next `run_once()` pass, another scan cycle sees the same work
item as un-leased (because `leased_until < now`), grants a new lease, and
executes the same work item concurrently.

The idempotency key is `{agent_name}:{trip_id}:{marker}` where `marker` is
based on the trip's `updated_at`. But the first execution hasn't updated the
trip yet (it's still running), so the marker hasn't changed. Two workers now
execute the same logical action on the same trip simultaneously.

**2. CHAIN OF EVENTS:**
- FrontDoorAgent scans trip T-001 at 10:00:00. Lease granted until 10:01:00.
- FrontDoorAgent.execute() is slow due to a synchronous HTTP tool call.
- At 10:01:05, AgentSupervisor runs another scan pass. The lease has expired.
- The same trip T-001 is still in `list_active()` with the same marker.
- A new lease is granted. The agent starts a second execution of T-001.
- Both executions call `trip_repo.update_trip()`. The second write may
  overwrite the first's assessment with stale data.
- The audit log shows two AGENT_ACTION events for the same trip. Operators
  see duplicate actions and can't tell which is canonical.

**3. USER EXPERIENCE:**
The operator sees two front-door assessments for the same trip in the audit
log. One might say "urgent" priority, the other "low". The trip's
front_door_assessment field shows whichever write finished last. The system
appears inconsistent.

**4. EMOTIONAL IMPACT:**
The glee of watching a system that's so carefully designed with idempotency
keys and lease-based coordination — and the lease is just too short. The
careful architecture is undermined by a single constant: 60 seconds.

**5. WHY TEAM MISSES IT:**
- Tests execute instantly. No test simulates an agent that takes >60s.
- The default 60s lease feels generous for "an API call."
- The live tools timeout at 10s each, but agents can call multiple tools.
- `DocumentReadinessAgent` calls live tools and has complex logic.
- No heartbeat/lease-renewal mechanism exists.

**6. LIKELIHOOD x IMPACT:**
Likelihood: MEDIUM (depends on agent execution time vs. 60s lease).
Impact: MEDIUM-HIGH (duplicate execution, potential data corruption).
Score: 6/10.

**7. TRUST DAMAGE:**
Moderate. Operators question the idempotency guarantees when they see
duplicate actions. If assessments are inconsistent, trust in the agent's
determinism erodes.

**8. RECOVERABILITY:**
Requires deduplicating audit events and identifying which assessment is
canonical. Manual operator intervention per trip.

**9. EARLIEST SIGNAL:**
- Two AGENT_ACTION events for the same trip_id in the same agent within
  one supervisor interval.
- `coordinator.snapshot()` showing a lease with status=COMPLETED but a
  new lease with status=RUNNING for the same key.

**10. VERIFY BY:**
- Set `lease_seconds=1` and run an agent that takes >1s. Check for
  duplicate audit events.
- Add a sleep(65) to any agent's execute() and run two scan cycles.

---

## FAILURE 7: LOCAL LLM CLIENT LAZY LOADS MODEL IN is_available() — EVERY AVAILABILITY CHECK IS A 2-10 SECOND BLOCKING CALL

**1. WHAT GOES WRONG:**
`LocalLLMClient.is_available()` calls `self._load_model()` which downloads and
loads a ~4GB model into memory. This is a blocking operation that takes 2-10
seconds on CPU. The `decide()` method also calls `is_available()` as its first line.
But more critically, any code that checks `is_available()` for routing — like a
hypothetical health check or a supervisor ping — will block for seconds.

The `count_tokens()` method *also* calls `_load_model()` if the model isn't loaded.
Every token count is a potential model-load if the model was previously `unload()`ed
(e.g., for memory pressure).

What makes this deadly: the model loading uses `print()` statements for progress
logging, not `logger.info()`. In a production server, these prints go to stdout
and may not be captured by the logging infrastructure. There's no timeout on model
loading, no async loading, no background readiness check.

If a health check endpoint calls `is_available()` on a LocalLLMClient that hasn't
loaded yet, it blocks the entire health check for 2-10 seconds, potentially
causing a cascading timeout in the load balancer that removes the container from
the pool.

**2. CHAIN OF EVENTS:**
- Container starts. Health check hits `/health` which (hypothetically) checks
  `local_llm.is_available()`.
- Model hasn't been loaded yet. `_load_model()` starts.
- 2-10 seconds of blocking. Health check times out at 5 seconds.
- Load balancer marks instance unhealthy. Removes from pool.
- Instance restarts (k8s liveness probe failure). Same cycle begins.

**3. USER EXPERIENCE:**
The system enters a crash loop. Every health check triggers a model load that
blocks for seconds. The container never passes its readiness probe. Users see
502s.

**4. EMOTIONAL IMPACT:**
The founder watching their deployment enter a restart loop because a health
check tried to load a 4GB model. The failure is so architectural — the model
loading IS the availability check — that it's hard to fix without redesign.

**5. WHY TEAM MISSES IT:**
- Local LLM is the fallback provider. It's rarely tested in CI.
- `is_available()` is expected to be O(1), not O(4GB).
- No liveness/readiness probe configuration exists in the repo.
- `print()` instead of `logger` means loading progress isn't visible.

**6. LIKELIHOOD x IMPACT:**
Likelihood: MEDIUM (only when local LLM is the active provider, or when code
  checks availability for routing).
Impact: HIGH (container crash loop).
Score: 7/10.

**7. TRUST DAMAGE:**
Severe for the specific failure mode. The system appears completely broken —
not partially degraded, but offline in a loop. Every restart wastes time and
money.

**8. RECOVERABILITY:**
Requires removing `is_available()` from health check paths, pre-loading
the model at startup, or adding a cached availability flag that doesn't
trigger loading.

**9. EARLIEST SIGNAL:**
- Container restart count increasing.
- Health check timeouts.
- 2-10 second gaps in any log stream.

**10. VERIFY BY:**
- Call `local_llm.is_available()` on a fresh instance and measure wall time.
- Check if any health/readiness endpoint or supervisor pings `is_available()`.

---

## FAILURE 8: HTTP LIVE TOOLS HAVE NO RETRY, NO CIRCUIT BREAKER, AND LEAK PROVIDER PAYLOADS INTO TOOLRESULT

**1. WHAT GOES WRONG:**
`HTTPFlightStatusTool`, `HTTPPriceWatchTool`, and `HTTPSafetyAlertTool` make
synchronous HTTP calls with `urllib.request.urlopen()` and a 10-second timeout.
If the provider is down, the call raises an exception that propagates straight
up to the agent's `execute()` method, which wraps it as a `RETRY_PENDING` status.
After 3 retries with backoff (0, 1, 5), the work item is poisoned. There's no
circuit breaker — every subsequent call to the same provider also fails and
consumes the same 3-retry budget.

More insidiously: the HTTP tools include the **entire raw provider response**
in the `ToolResult.data` dict:
- `HTTPFlightStatusTool` includes `data["provider_payload"] = payload`
- `HTTPPriceWatchTool` includes `data["provider_payload"] = payload`

This raw payload may contain API keys in redirect URLs, internal provider IDs,
rate limit headers reflected in response bodies, and partner-specific pricing
data that shouldn't be stored in the trip record. The `ToolResult` is serialized
via `to_dict()` and stored in the trip as `tool_evidence`. Every raw API response
is now permanently stored in the trip record.

**2. CHAIN OF EVENTS:**
- FlightStatusTool calls a provider. Provider response includes an internal
  `trace_id` and `api_version` field, plus a `metadata.partner_ref` that
  contains a session token.
- This full response is stored as `provider_payload` in the trip record.
- The trip record is stored in plaintext JSON (or encrypted with the hardcoded key).
- An operator exports trip data for analysis. The export includes the provider's
  internal session token.
- The provider's API uses that token for replay. The operator's export just
  leaked a valid API session.

**3. USER EXPERIENCE:**
No user-facing impact until the leak is discovered. When discovered, it's
already too late — the data has been exported, shared, stored in backups.

**4. EMOTIONAL IMPACT:**
The cold glee of finding that the tool contract architecture — so carefully
designed with `ToolEvidence` and `ToolFreshnessPolicy` — includes a
`provider_payload` field that is just a raw dump. The contract was built to
normalize provider data, and then the tools bypass their own contract by
stuffing the raw response in alongside the normalized data.

**5. WHY TEAM MISSES IT:**
- The `ToolResult` contract says "raw provider response should never be treated
  as canonical state" — but it *is* stored as canonical state.
- Tests use mock tools that don't have `provider_payload` fields.
- The `to_dict()` serialization includes everything. Nobody audits what's in
  `provider_payload`.
- No PII/sensitive-data scan runs against stored tool evidence.

**6. LIKELIHOOD x IMPACT:**
Likelihood: HIGH (every live HTTP tool call stores the full response).
Impact: MEDIUM-HIGH (data leak, potential replay attack vectors).
Score: 7/10.

**7. TRUST DAMAGE:**
High for the provider relationship. If a flight status provider discovers their
internal tokens being stored in plaintext in a third party's database, they
may revoke the API key.

**8. RECOVERABILITY:**
Requires scrubbing `provider_payload` from all stored trip records and adding
a sanitization step before storage. Already-leaked data can't be recalled.

**9. EARLIEST SIGNAL:**
- Any `provider_payload` in stored ToolResult data that contains keys like
  `token`, `session`, `secret`, or `key`.
- Trip record size growing unexpectedly due to large provider payloads.

**10. VERIFY BY:**
- Store a ToolResult from a live HTTP tool call and inspect the dict for
  sensitive fields.
- Search stored trip data for `provider_payload` keys.
  
---

## The failure nobody wants to talk about:

The LLM pipeline was designed as a command — "decide this" — with the assumption that
the LLM is a reliable subordinate. But the LLM is not a subordinate. It's a
*translator* that sometimes speaks a different dialect, and nobody on the team speaks
the dialect well enough to notice when the translation is wrong. The schema is
shipped as a *suggestion*, not enforced as a *contract*. The privacy guard guards
persistence, not transmission. The recovery agent recovers from its own amnesia.
The usage guard reserves budget for calls that never happened.

Every layer in the pipeline has a boundary it protects — and a boundary it ignores.
The seam that tears will be the one where two systems touch and neither one owns
the handshake: the LLM returns JSON that isn't schema-valid, and no code is
responsible for checking. The privacy guard blocks storage, but no code is
responsible for blocking transmission. The recovery agent re-queues, but no code
is responsible for remembering how many times.

The system doesn't fail because any single component is broken. It fails because
every component correctly handles its own contract while silently violating the
system's intent.