# Current Custody View & Artifact Classification Baseline

**Document Version**: 1.0 (Canonical Custody Register)  
**Established**: 2026-09-16  
**Governing Findings**: `EV-05` (`FND-0194`), `EV-10` (`FND-0199`)

---

## 1. Executive Summary & Custody Consolidation

To permanently resolve the ledger proliferation observed in `EV-05` (`final10` through `final32` CSV churn across worktree iterations) and clarify the Git authorization and request tracing boundaries identified in `EV-10`:

1. **Frozen Historical Snapshots**:
   All 38 historical classification CSVs located in `Docs/review/assets/` (`final2` through `final31`) are frozen as historical point-in-time evidence. No further `finalNN` CSVs will be generated solely for path-count or worktree drift.
2. **Canonical Working Tree Custody Baseline**:
   - **Baseline File**: `Docs/review/assets/a1_1_live_worktree_2026-09-05_final32_classification.csv`
   - **Generation Timestamp**: `2026-09-05T17:48:41+05:30`
   - **SHA-256 Digest**: `994f72f39112db285520f05a2872e27ce0ae1801346705e2721ebb8b6ac2cc25`
   - **Classification Standard**: Every untracked/dirty path is classified into ownership, sensitivity, and purpose per `Docs/review/A1_1_DELIVERY_ARTIFACT_REVIEW_2026-09-05.md`.

---

## 2. Request Trace & Git Authorization Boundaries (`EV-10`)

`EV-10` observed that earlier request traces had incorrectly presented existing user Git authorizations as missing and labelled uncommitted paths as concurrent without forensic proof.

### Canonical Interpretation & Clarifications
1. **User Authorization Ground Truth**:
   The user's direct instruction explicitly authorized the operating-system overhaul and its filesystem verification across all findings. It authorizes file inspections, code modifications, test executions, and doc updates within this repository scope.
2. **Commit & Push Gates Remain Distinct**:
   Per Operating Doctrine 8.0, workspace mutations (editing, generating, moving files) are authorized to complete the requested scope. However, Git commit, push, branch changes, and external mutations remain separate named gates that require explicit, unambiguous user confirmation before execution.
3. **Dirty vs Concurrent State**:
   Dirty or uncommitted working tree paths must not be labeled `unknown_preserved_concurrent` without specific multi-agent or multi-branch provenance evidence. In the current single-worktree session, changes are tracked directly to the authorized findings burndown.
4. **Command Execution Honesty**:
   Background command execution must never confuse "launched with no immediate output" or "background timeout" with verified failure or verified completion. Every finding closure requires concrete verification receipts (exit code 0 and passing test output).

---

## 3. Artifact Custody & Verification Standards

- **Runtime State**: `data/drafts/index.json` is properly ignored in Git while locally preserved.
- **Historical Tools**: `scripts/update_council_panel.py` and `scripts/write_visualizers.py` are safely archived in `Docs/archive/historical_tools/` with exact byte hashes preserved in gzip archives.
- **Images**: All 40 scenario screenshots in `Docs/review/assets/` are classified as historical local simulation evidence, with simulated badges and disclosures verified.
