# process_issue_review_2026-04-15

## 2026-04-15
### Issue
`apply_operating_mode()` in `src/intake/decision.py` referenced `hard_blockers` in the `follow_up` branch without receiving it as a parameter.

### Why It Matters
- This can raise `NameError` when `operating_mode == "follow_up"` and branch condition is evaluated.
- It is a latent runtime risk in non-default operating modes.

### Resolution
- Updated function signature to pass `hard_blockers` into `apply_operating_mode(...)`.
- Updated call site in `run_gap_and_decision(...)`.
- Added regression test:
  - `tests/test_follow_up_mode.py`

### Current Status
- Fixed and covered by targeted regression test.
