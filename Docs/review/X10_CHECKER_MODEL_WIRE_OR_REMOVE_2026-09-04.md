# X-10 Checker-Model Wire-or-Remove Decision

**Date:** 2026-09-04\
**Scope:** `checker_model` agency setting, its API/UI contract, and the
runtime checker path\
**Owner:** decision/evaluation lane\
**Status:** **DEFER WIRE; RETAIN COMPATIBILITY; CORRECT CLAIMS BEFORE
ACTIVATION**

## Executive decision

`checker_model` is genuinely unwired at runtime. It is declared and persisted,
returned by the settings API, typed in the frontend client, and editable in
`AiAgentTab`, but no runtime call reads it. The current checker is a
deterministic in-process heuristic (`CheckerAgent.audit(packet, decision)`),
not a model client. The public itinerary checker is likewise a deterministic
pipeline with optional live weather/climate enrichment; it does not use this
setting.

Do **not** pass the configured model string into the current checker as a
label, metadata field, or unused argument. That would imply model execution
without a provider call, model-version evidence, spend accounting, consent,
or fallback semantics. Do **not** delete the setting in this slice either:
the field is part of the persisted agency-settings schema and the API/UI
contract, and deleting it would be a breaking contract change without solving
the underlying model-routing question.

The first-principles disposition is:

1. retain `checker_model` as a compatibility-preserved, currently reserved
   setting;
2. mark the UI/API semantics as inactive/reserved before presenting it as an
   active capability;
3. build the canonical T1/T2 model-router contract first; and
4. only then consume `checker_model` at that router boundary, with provider
   identity, model version, budget, consent, validation, human-review,
   fallback, and telemetry evidence.

This closes the audit question (“is it unwired?”) but does **not** close X-10
as a product capability. Runtime model wiring remains an explicit future task.

## Evidence inventory

### Configuration and persistence

The setting exists in the per-agency `AiAgentSettings` dataclass:

```text
src/intake/config/agency_settings.py:284-304
```

The default is `"gemini-2.0-flash"`. `AgencySettings.from_dict()` accepts a
stored `ai_agent` object and constructs `AiAgentSettings(**raw_ai_agent)`;
`AgencySettings.to_dict()` serializes it with `dataclasses.asdict()`:

```text
src/intake/config/agency_settings.py:524-545
src/intake/config/agency_settings.py:554-560
```

This proves persistence/configuration plumbing, not model execution. The
current `from_dict()` path also accepts arbitrary strings; there is no
provider/model registry validation. That is acceptable for compatibility while
reserved, but it is insufficient for an active provider selector.

### API contract and routes

The API request contract accepts an optional string:

```text
spine_api/contract.py:423-440
```

`GET /api/settings/ai-agent` returns the stored value and
`POST /api/settings/ai-agent` stores it:

```text
spine_api/routers/settings.py:742-771
spine_api/routers/settings.py:774-814
```

The POST path performs no model-registry validation, provider capability
check, or runtime activation. It is therefore a settings write/read contract,
not a model-routing contract.

### Frontend exposure

The frontend client types and calls the same field:

```text
frontend/src/lib/api-client.ts:796-821
```

`AiAgentTab` renders a `Checker Model` selector from a generic static
`MODEL_OPTIONS` list and saves the selected string:

```text
frontend/src/app/(agency)/settings/components/AiAgentTab.tsx:20-29
frontend/src/app/(agency)/settings/components/AiAgentTab.tsx:316-348
```

The current copy (“Choose which AI models power each capability”) overstates
the checker field because no checker model is called. This is a truth-boundary
finding and must be corrected before the field is treated as active. The
settings component is outside this bounded backend decision slice, so the copy
change is recorded as a follow-up rather than silently made here.

### Runtime consumer audit

The only exact `checker_model` references in the live source tree are the
declaration, API contract, settings GET/POST, and frontend client/component
listed above. No runtime consumer exists in `src/`, `spine_api/`, or `tests/`
beyond those configuration surfaces.

The actual checker path is:

```text
src/intake/frontier_orchestrator.py:88-112
src/intake/frontier_orchestrator.py:166-185
src/intake/checker_agent.py:14-75
```

`run_frontier_orchestration()` resolves only the feature gate
`enable_checker_agent` and the independent `autonomy.checker_audit_threshold`.
It invokes:

```python
checker_agent.audit(packet, decision)
```

`CheckerAgent.audit()` performs deterministic checks for missing budget,
high-stakes purpose, and low confidence without hard blockers. It does not
accept `agency_settings`, a model ID, a provider client, a prompt, or a model
version. Its docstring explicitly describes the model call as a production
system possibility, while the current implementation is a heuristic.

The public checker path loads agency settings only as part of the canonical
pipeline context:

```text
spine_api/services/public_checker_service.py:139-225
```

That path runs `run_spine_once()` and finalizes deterministic live-check
signals. No `checker_model` value is passed to a client or checker there.

## Why immediate wiring is rejected

The existing design evidence already identifies the correct future insertion
point and its prerequisites in
`Docs/exploration/C03_ROUTER_DESIGN_2026-09-02.md`:

- the setting is currently “stored, editable in UI, never consumed” (§0.1);
- the proposed router must classify post-tier-0 artifacts, not prompt length
  (§2);
- model tiers require field-level quality profiles and a frozen golden set
  (§3);
- T1/T2 calls require bounded retries, usage budgets, egress policy, and
  explicit fallback to deterministic T0 (§4); and
- promotion requires task-success and cost-per-accepted-packet evidence (§5).

None of those prerequisites is established by the current setting or checker.
A small “wire” that merely forwards `checker_model` to the deterministic
checker would therefore be cosmetic and misleading. A real wire would be a
new router/provider/evaluation capability and is not a safe one-file change.

## Wire-or-remove alternatives

| Option | Decision | Reason |
|---|---|---|
| Pass `checker_model` into `CheckerAgent.audit()` but keep heuristic logic | **Reject** | Creates false model-use attribution; no provider call or model-version evidence. |
| Add model metadata to the current `CheckerAuditResult` only | **Reject** | Metadata is not execution; it would make observability less truthful. |
| Delete the setting/API/UI field now | **Defer** | Breaking persisted/API/UI contract; does not answer whether a future reviewed T1 checker is needed. Requires owner-approved migration and product decision. |
| Keep reserved field, correct active-capability copy, then wire at a canonical router boundary | **Accept** | Preserves compatibility, makes current truth explicit, and aligns future work with C03’s measured tier contract. |

## Required follow-up implementation package

The next X-10 wave should be a separate, dependency-ordered package:

1. Add a canonical model/provider registry with allowlisted IDs, provider
   capability metadata, deprecation/version policy, and a clear unknown-model
   rejection path.
2. Add a post-T0 route classifier that chooses T0/T1/T2 from validation,
   gate, confidence, ambiguity, contradiction, and measured field-coverage
   signals.
3. Define an advisory `CheckerProposal` contract that preserves T0 facts,
   identifies fields targeted, records source/model/version, and requires
   validation plus owner review before applying any proposal.
4. Route `checker_model` only through that canonical boundary; never let an
   agency setting select an unregistered provider or bypass usage guard,
   egress policy, consent, or tenant isolation.
5. Record route tier, route reason, fields targeted, model/provider/version,
   latency, cost, fallback result, and review outcome in the existing telemetry
   and audit structures.
6. Add frozen golden-set, private holdout, adversarial, mutation, and
   disagreement tests before enabling T1; keep deterministic T0 behavior as
   the fail-closed fallback.
7. Update the UI copy only after the contract is explicit: while reserved it
   must say it applies once reviewed AI extraction/checking is enabled; after
   activation it must show availability, consent, and model/version state.

## Verification receipt

The following existing contract/runtime tests were run against the shared
working tree during this audit:

```text
PYTHONPATH=src .venv/bin/pytest -q \
  tests/test_agency_settings.py \
  tests/test_feature_gates.py \
  tests/test_settings_router_contract.py
53 passed in 7.93s

.venv/bin/ruff check \
  src/intake/checker_agent.py \
  src/intake/frontier_orchestrator.py \
  src/intake/config/agency_settings.py \
  spine_api/contract.py \
  spine_api/routers/settings.py \
  tests/test_agency_settings.py \
  tests/test_feature_gates.py \
  tests/test_settings_router_contract.py
All checks passed!
```

These tests prove settings persistence, API contract shape, and the
`enable_checker_agent` gate. They do not prove model execution; no such
execution exists in the current path. The absence claim is bounded to the
repository search scope listed above and should be re-run after any router or
provider addition.

## Residual gates and ownership

- **Local decision:** complete for X-10’s wire-or-remove audit.
- **Code change in this slice:** none; the current setting/API/UI plumbing and
  deterministic checker were preserved.
- **Documentation:** this evidence record is the durable decision artifact;
  C03 remains the future router design source.
- **Still open:** UI copy correction, model registry, router, provider
  credentials, consent/PII review, spend guard, quality/holdout evidence,
  telemetry, human-review semantics, rollout/rollback, and owner ratification
  of per-agency model choice.
- **Git:** no staging, commit, push, reset, checkout, stash, clean, or branch
  mutation was performed. All concurrent dirty work remains preserved.
