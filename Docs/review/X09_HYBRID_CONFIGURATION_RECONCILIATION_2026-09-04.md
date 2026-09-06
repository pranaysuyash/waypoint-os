# X-09: Production-vs-CI hybrid configuration reconciliation

**Date:** 2026-09-04\
**Scope:** `USE_HYBRID_DECISION_ENGINE` serving, deployment, CI, and D6
scenario-evaluator configuration.\
**Owner lane:** production-vs-CI configuration truth (X-09).\
**Disposition:** additive reconciliation landed locally; production-release
ratification remains open.

## Why this matters

The hybrid decision engine is reachable from the serving decision path and its
code default is enabled.  Before this slice, the D6 scenario helper silently
forced the feature off, so a green or red D6 result could describe a materially
different configuration from the one serving advisors.  That is a configuration
truth problem, not merely a test-fixture problem: deployment, CI, and audit
evidence must identify the same effective mode.

The internal value of this slice is bounded and concrete:

* make the intended current serving mode explicit in deployment manifests and
  CI;
* stop D6 from silently overriding a caller's mode;
* keep D6's deterministic authority axes (decision state, hard blockers, and
  contradictions) separate from model-quality claims; and
* preserve enough metadata to detect a future mode drift in the stable snapshot.

## Evidence baseline

| Claim | Current evidence |
| --- | --- |
| Serving code defaults hybrid mode on | `src/intake/decision.py:32-37` reads `USE_HYBRID_DECISION_ENGINE` with default `"1"`; `src/decision/hybrid_engine.py:804-830` documents the same default in the factory. |
| Hybrid is a serving-path capability, not an orphan module | The serving call chain is documented in `Docs/exploration/C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md:12-24,40-49`; the same dossier records the reachable LLM last-resort tier and the existing usage/telemetry controls. |
| The prior CI split was real | The dossier's H-01 finding (`Docs/exploration/C02_WIRE_OR_ARCHIVE_DOSSIERS_2026-09-02.md:49`) identified production default-on versus D6 forcing off.  The old override was in `src/evals/audit/snapshot.py` around the scenario collector; it is now replaced by caller-preserving behavior at `src/evals/audit/snapshot.py:727-749`. |
| D6's graded axes are deterministic authority outcomes | `src/evals/audit/rules/scenarios.py:15-26` defines exact decision-state, blocker-count, and contradiction axes; the collector still grades those production packet outcomes and does not claim that the LLM risk-enrichment tier has passed a model-quality evaluation. |
| The category is not yet a public/release authority | `src/evals/audit/snapshot.py:776-779` keeps `gap_decision` as `shadow`; its accuracy can be reported and hash-tracked without blocking CI until the fixture semantics and evaluation contract are ratified. |

## Decision

The canonical intended *configuration* for the current serving path is
**hybrid enabled (`USE_HYBRID_DECISION_ENGINE=1`)**.  This is an evidence-led
reconciliation of the code default and existing serving wiring, not an approval
that an external model is production-ready.

The chosen contract is:

1. Production-facing images/manifests and CI declare `1` explicitly.
2. The D6 helper preserves an explicit caller value.  If no value is supplied,
   it temporarily applies the same serving default (`1`) and restores the
   process environment exactly afterward.
3. D6 records a canonical effective value (`"1"` for either unset-default or
   explicit-on, `"0"` for explicit-off), so stable snapshots do not drift merely
   because CI declares a default that local serving code would infer.
4. D6 records `evaluation_contract:
   deterministic_authority_axes` and `provider_calls_authorized: false`.
   Thus this lane is evidence about deterministic authority outcomes under the
   effective configuration; it is not evidence of provider quality, latency,
   cost, or real production behavior.

## Alternatives evaluated

| Option | Disposition | Rationale |
| --- | --- | --- |
| Turn hybrid off everywhere | **Defer/reject for this slice** | It would change the current serving behavior and needs an explicit owner/product decision. It would also discard an already-wired capability rather than reconcile its evidence. |
| Keep D6 forced off | **Reject** | It creates opaque split-brain evidence and makes the audit artifact unable to describe the serving configuration. |
| Explicit on in serving/CI + deterministic D6 metadata | **Choose** | Small blast radius, preserves current behavior, makes mode drift observable, and does not overclaim model quality. |
| Make hybrid/model quality a hard D6 gate now | **Defer** | There is no provider-authorized golden/holdout/adversarial contract, disagreement policy, or release-quality cost/latency evidence in this lane. |

## Implementation record

The bounded patch changes the following surfaces:

* `src/evals/audit/snapshot.py` no longer forces the scenario collector to
  `0`; it preserves explicit values, applies the serving default only when
  unset, restores the environment, and emits `hybrid_config` in scenario
  health and the stable snapshot view.
* `tests/test_x09_hybrid_configuration.py` adds focused coverage for unset
  default, explicit CI-on, explicit off, environment restoration, provider-key
  isolation, and stable metadata retention.
* `.github/workflows/ci.yml` sets `USE_HYBRID_DECISION_ENGINE: "1"` on the
  backend test job.
* `Dockerfile`, `Dockerfile.spine_api`, `docker-compose.yml`, `fly.toml`, and
  `render.yaml` declare the serving value explicitly. Compose retains a
  deliberate deploy-time override (`${USE_HYBRID_DECISION_ENGINE:-1}`).
* `.env.example` labels the toggle and explains that the current serving
  default is on.
* `data/evals/d6_audit_gate_snapshot.json` was regenerated through the existing
  verifier so its scenario health records the canonical effective value.

No provider secret was used, exposed, or authorized by this work.  When
credentials are absent, the existing engine's safe fallback is observed; this
does not constitute a provider or hosted-runtime test.

## Verification evidence

All commands were run in the shared dirty checkout without staging, committing,
pushing, resetting, checking out, stashing, or cleaning.

* `PYTHONPATH=. .venv/bin/pytest -q tests/test_x09_hybrid_configuration.py tests/evals/test_d6_gate_snapshot.py`
  — **59 passed**.
* `.venv/bin/ruff check src/evals/audit/snapshot.py tests/test_x09_hybrid_configuration.py`
  — **All checks passed**.
* `python3 -m py_compile src/evals/audit/snapshot.py tests/test_x09_hybrid_configuration.py`
  — passed.
* YAML parsing of `src/evals/audit/manifest.yaml` and `docker-compose.yml` —
  passed.
* With provider credentials removed from the process, a direct D6 build under
  `USE_HYBRID_DECISION_ENGINE=1` produced **30/30 scenario results** and
  `SCENARIO_ACCURACY=1.0`, with the expected safe-fallback warnings for the
  visa risk-enrichment decision.
* `scripts/verify_d6_gate_snapshot.py --write` — `{"ok": true}`; the tracked
  snapshot now records `effective_enabled: true`, `configured_value: "1"`,
  deterministic authority axes, and `provider_calls_authorized: false`.
* `scripts/verify_d6_gate_snapshot.py` under both an unset toggle (serving
  default) and explicit `USE_HYBRID_DECISION_ENGINE=1` — `{"ok": true}` in
  both cases. This is the key parity proof for the canonical effective value.

These are static/local and focused integration evidence (Tier 1/2, S1). They
are not Tier 3 provider, Tier 4 hosted/production, or Tier 5 real-user proof.

## Residual gates and owner decision

The current implementation is truthful about configuration, but **an owner
decision is still required before calling hybrid model quality or production
release readiness complete**:

* ratify that hybrid-on is the intended real-production posture, including
  whether external LLM calls are permitted for each deployment/data class;
* define a provider/model registry, explicit no-provider CI policy, and a
  golden/holdout/adversarial corpus that measures hybrid risk flags against the
  legacy/deterministic baseline;
* define disagreement, abstention, fallback, rollback, latency, cost, budget,
  and outage semantics; and
* prove telemetry/audit coverage, consent/PII egress controls, and a hosted
  deployment check before promotion.

Until those gates are satisfied, `gap_decision` remains `shadow`, and the
snapshot's `provider_calls_authorized: false` must not be read as proof that a
provider-backed run was exercised. The existing dossier's related governance
items remain open and are intentionally not silently closed by this patch.

## Recovery path

To deliberately run rules-only, set `USE_HYBRID_DECISION_ENGINE=0` in the
deployment environment and CI, regenerate the D6 artifact through the existing
verifier, and record the owner decision. Do not reintroduce a hidden evaluator
override. A future rollback should be a reviewed additive configuration change,
not a destructive Git operation.

## Handoff

This slice is ready for parent integration review. The checkout remains broadly
dirty due to concurrent work; this lane did not stage or claim unrelated paths.
The parent should include the two new/changed X-09 paths and regenerated snapshot
in its final custody inventory, then run the repository's full gate after all
parallel slices converge.
