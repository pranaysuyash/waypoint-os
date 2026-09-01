# Findings Lifecycle — State Machine & Enforcement (2026-08-30)

**Resolves:** EX-06 (Exploration & Research Backlog 2026-08-29) · informs doctrine amendment D-02 (Pranay's decision pending)
**Problem:** ~25 audits in 5 months produced findings with no lifecycle — no status, no owner, no re-verification date. Findings could only be re-discovered, never closed, and completion claims went unchecked (A-21: this audit nearly duplicated six in-flight artifacts because none of them were tracked as *findings with state*).

---

## 1. The state machine

Every finding row (ID-bearing row in a register table) is in exactly one of four states:

```
            ┌────────────┐   fix verified    ┌────────────┐
            │    OPEN    │ ────────────────▶ │   CLOSED   │
            │            │                   │ (fixed)    │
            └─────┬──────┘                   └────────────┘
                  │ wontfix / superseded / recorded-no-go
                  ▼
            ┌────────────┐        new evidence may
            │  DEFERRED  │ ───── reopen as OPEN ────▶ (back to OPEN)
            └────────────┘
```

| State | Meaning | Row markers the checker recognizes |
|---|---|---|
| **open** | actionable, awaiting work | (no marker — default) |
| **closed** | fix verified with evidence, or wontfix/superseded/no-go with recorded reason | `RESOLVED`, `FIXED`, `closed`, `wontfix`, `superseded`, `no-go`, `rejected` |
| **deferred** | deliberately parked with a reason (design exists elsewhere, conditional, recorded no-go-for-now) | `deferred`, `conditional`, `trap`, `no-go-for-now` |

Rules:
1. **One row per finding ID.** Two tasks from one finding merge into one row (wave refs disambiguate).
2. **A closing transition requires evidence in the row**: the verification command/output doc or a dated resolution link. No bare "done".
3. **A no-go is a record, not a silence** (doctrine §9): rejected directions keep their row with the reason, marked no-go/deferred — they are never deleted and never silently re-proposed.
4. **Open rows carry a verification date** — either an in-row `YYYY-MM-DD` or the register's `**Date:**` header. In-row dates only *raise* freshness (e.g. `RESOLVED 2026-08-30`), never lower it (rows cite other docs' older dates as references).

## 2. Enforcement (mechanical)

`scripts/check_findings_register.py` (stdlib-only, CI-ready):

```
python3 scripts/check_findings_register.py Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md
python3 scripts/check_findings_register.py --max-age 30 <register1.md> <register2.md>
```

- **Errors (exit 1):** duplicate ID rows · open findings stale beyond `--max-age` (default 45 days).
- **Warnings:** open rows with no verifiable date at all.
- **Verified:** both existing registers pass (consolidated: 51 rows — 45 open / 6 closed; FINDINGS_REGISTER_2026-08-29: 16 rows — 9 open / 7 closed). Failure modes exercised with a synthetic stale+duplicate fixture.

**CI wiring (one line, deferred):** add to the `docs-quality` or a new job in `.github/workflows/ci.yml`:

```yaml
      - name: Findings lifecycle gate
        run: python3 scripts/check_findings_register.py Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md
```

Deferred because `.github/workflows/ci.yml` carries the A-14 agent's uncommitted changes; wire it in the next CI touch.

## 3. Register canon

- **Canonical register:** `Docs/review/FINDINGS_TASKS_CONSOLIDATED_2026-08-30.md` (it subsumes R-, A-, F-, EX-, RQ-, D- IDs). The 2026-08-29 register remains as historical evidence and still validates.
- New findings enter the canonical register with an ID, a task line, and today's date — the register **is** the verification event.
- Audit-specific registers may still be written (evidence artifacts), but their findings must be carried into the canonical register in the same change, or they will go stale and the gate will say so.

## 4. Doctrine amendment candidate (D-02 — for Pranay)

Per doctrine §16.9, recurring gaps become explicit amendments. Proposed text for the Review Doctrine:

> **Finding lifecycle.** Every review finding is recorded in the canonical register with an ID, state (`open | closed | deferred`), and verification date. Closing requires cited evidence; no-go requires a recorded reason; open findings are re-verified on a cadence enforced by `scripts/check_findings_register.py` in CI. Completion claims must cite the verification command and its date (see also D-05).

Companion amendments D-01 (absence claims need executed evidence) and D-05 (completion-claim standard) remain open for Pranay's decision; this tooling implements D-01/D-05 mechanically for findings rows regardless.

## Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md
