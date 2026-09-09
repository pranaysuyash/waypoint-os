# Personas/Scenarios Library Graduation Protocol — Exploration (VE-04)

**Date**: 2026-09-09
**Status**: EXPLORE → DECIDE (protocol proposed; adoption is an owner decision)
**Source**: Random document audit seed 20260909. Systemic finding: `Docs/personas_scenarios/` contains **415 proposal documents** (AREA_DEEP_DIVE family + ADDITIONAL_SCENARIOS_100..139+ family) whose scenario IDs never graduated into the eval corpus. The corpus today = 30 alpha packets (`data/fixtures/test_scenarios.py`) + 2 niche longtail + SC-style workbench fixtures + edge messages. The library is a proposal graveyard with no triage path — the same pattern as the itinerary-checker wedge (proposals that quietly stalled without formal closure).
**Register refs**: VE-04 (this doc), VA-04 (first graduation executed), VD-01..04.

---

## 1. Evidence

- Pool size: 415 files in `Docs/personas_scenarios/` (2026-09-09 count).
- Corpus IDs: `trip_alpha_*`, `ACAD-*`, `REPAT-*`, `SC-*`. **Zero** IDs from the personas_scenarios library appear in `data/fixtures/` or `src/evals/` (negative search, 2026-09-09).
- One incidental overlap: `data/fixtures/test_messages.json` `msg_edge_006` exercises visa-timeline urgency, but it predates and does not reference VISA-00x.
- First graduation under this protocol: **SC-960 / SC-961** (2026-09-09, visa audit VA-04/VE-03) — seeded from `AREA_DEEP_DIVE_VISA_IMMIGRATION.md` VISA-001/VISA-002 families.

## 2. The problem

Two failure modes coexist:

1. **Silent stall** — proposals that partially landed (visa engines) or never landed, with no register entry, no supersession banner, no closure decision. Future audits keep re-discovering them (this audit is the proof).
2. **Library noise** — 415 untriaged docs make the folder unauditable; nobody can answer "which of these are ratified, dead, or blocked?"

## 3. Proposed protocol (mirrors the findings-register discipline)

Every document in the library gets exactly one disposition, recorded as a **front-matter banner** on the doc itself (additive, no history deleted):

```markdown
<!-- SCENARIO_DISPOSITION: graduated | blocked | superseded | rejected | open
     Date: YYYY-MM-DD
     Register ref: <FINDINGS_TASKS row id or VE/VD id>
     Graduated-to: <fixture/test ids, if graduated>
     Notes: one line
-->
```

Disposition rules:

| Disposition | Meaning | Action |
|---|---|---|
| `graduated` | Scenario(s) live in the eval corpus | Name the fixture/test IDs in the banner |
| `blocked` | Genuinely wanted, blocked on a register item | Name the blocker (e.g. VD-02) |
| `superseded` | A later doc/decision replaced it | Name the superseding artifact |
| `rejected` | Owner decided not to build | One-line why (pre-launch filter etc.) |
| `open` | Not yet triaged | Default state; the triage backlog |

**Triage cadence**: a disposition is required before a domain lane is activated (e.g. if visa work unblocks, `AREA_DEEP_DIVE_VISA_IMMIGRATION.md` + `REG_SPEC_VISA_AUTOMATION.md` + `ID_SPEC_IDENTITY_VAULT.md` must all get banners in the same pass). Bulk backfill of the other ~410 docs is **not** urgent — do it opportunistically whenever an audit or work-stream touches a doc (this mirrors the register's "additive addendum" discipline and avoids a mega-pass that would go stale).

**Graduation path** (how a proposal becomes a corpus seed — codified from the SC-960/961 execution):

1. Draft the raw note from the proposal's scenario row.
2. Run the real pipeline (`ExtractionPipeline.extract` at the right stage + `run_gap_and_decision`) and **freeze expectations from actual behavior** — never from the proposal's imagined outcome. If actual behavior is wrong, that's a finding, not a fixture.
3. Conform to `specs/scenario_fixture.schema.json`.
4. Wire it into a test that loads the fixture and asserts the frozen contract (no orphan fixtures).
5. Banner the source doc `graduated` with fixture IDs.

## 4. Why not bulk-triage now

415 docs × even 2 minutes of judgment each is ~14 hours of agent/owner attention that the pre-launch filter (better + money) cannot justify today, especially with ~150 of them being ADDITIONAL_SCENARIOS idea-stubs rather than commitments. Opportunistic triage on touch is the additive path; the banner format guarantees no doc is ever silently re-discovered as "unknown status" again.

## 5. Decision requested from owner

- Ratify the banner format + opportunistic cadence (recommended), or
- Commission a bulk triage pass (est. 4-6 focused agent sessions), or
- Reject the protocol and archive the library as pure historical inspiration (supersession banners only).
