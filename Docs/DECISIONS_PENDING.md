
## TRV-DP-01 (opened 2026-10-12 01:10 IST, nightly orchestrator): ownership of the dirty tree before nightly implementation
- **Context:** The tree has uncommitted work as recent as 2026-10-05 (sim3 tools, about 15 tests). The Codex register says the owner state is unclear. The nightly orchestrator wrote `Docs/audit/OPEN_ITEMS_AUDIT.md` and `IMPLEMENTATION_PLAN.md` but made no code changes.
- **Options:** A. Pranay names the current owner/session, and the nightly task does doc-only work here. B. Nightly may do plan items 1–2 (LAUNCH_STATUS receipt refresh, TODO-to-findings check), which are test/doc additions only. C. Hold everything.
- **Recommendation:** B for item 1 (refresh the evidence receipt) only after the in-flight sim3 work is classified. Otherwise A.
- **Also for decision:** root clutter list (audit TRV-N04), including classifying `dogfood_cookies.txt` (possible session secret; not opened). Fly CD on push while public launch is NO-GO (TRV-N05, already blocker 8).
- **Blocked:** IMPLEMENTATION_PLAN items 1–3.

## TRV-DP-02 (resolved 2026-10-21, authorized by operator):
- **Decision P-1 (Live Jev vs Heuristic Serving)**: Adopted Option A as standard default (Live Smart Assistant active automatically when credentials present, with zero-downtime heuristic fallback when absent or offline). Option B (higher limits / pro features) reserved for commercial packaging while ongoing local research, evaluation, and documentation proceed.
- **Decision P-3 (Statutory Airline Claim Processing)**: Adopted Option A as standard default (Software Helper: exact statutory compensation calculation and dispute letter generation under EC 261 / UK261 / US DOT / Montreal Convention Art. 19; airline pays traveler directly). Paid direct recovery representation reserved for future phase.
- **Decision P-4 (GDPR Art. 17 Erasure Depth)**: Adopted Option A (Recursive deep erasure of personal direct PII, contact info, and identity certificates while preserving non-PII aggregated bookkeeping/margin metrics).
- **Maintenance TRV-N04 (Root Clutter & Secret Hygiene)**: Adopted Option A (Temporary test databases `test_*.db` and `dogfood_cookies.txt` are confirmed `.gitignore` excluded to prevent accidental Git commits or leakages).
