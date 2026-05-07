# Pre-Mortem 06: Scale & Operational Survival

**Project:** Waypoint OS
**Role:** Operator / Captain
**Emotional Register:** Grim satisfaction — watching the numbers quietly get worse.
**Date:** 2026-05-05

*"It is 3 months after beta launch. Five agencies are using Waypoint OS daily. The launch went badly."*

---

## Finding 1: 814 Run Directories Already — Linear Growth Will Fill Disk in Months

**What goes wrong:** Every pipeline run creates a new directory under `data/runs/`. There are already 814 run directories from development alone. At 5 agencies doing 50-300 trips/month each, worst case: 1500 runs/month plus re-runs. The 67MB current usage is small, but the directory count (not the bytes) will exhaust inode limits on cloud filesystems (GP3 EBS volumes max ~1M inodes) within 2 years. File listing operations (`ls data/runs/`) are already slow.

**Chain of events:**
- Development produces 814 runs organically. No cleanup mechanism exists.
- Beta launches with 5 agencies. Each trip generates 2-5 runs (initial + edits + re-runs).
- After 6 months: ~15,000-20,000 run directories.
- Filesystem operations on `data/runs/` become slow. Backups take hours.
- Any admin tool that iterates over runs (audit, cleanup, migration) becomes unusable.

**User experience:** Invisible until a backup fails or `ls` times out. Then the operator sees a 500 error on the audit page.

**Emotional impact:** Exhausted resignation — "of course it broke, it was fine until it wasn't."

**Likelihood x Impact:** High x Major (slow onset)
**Trust damage:** Medium
**Recoverability:** Hard — must build cleanup tooling while system is operational; cannot simply delete because audit trail depends on runs.
**Earliest signal:** `ls data/runs/ | wc -l` grows past a threshold; the audit page takes >2s to load.
**Verify by:** Extrapolate: 814 runs from how many weeks of dev? Multiply by expected rate for 5 agencies.

---

## Finding 2: Geography Database Re-Indexes on Every Start

**What goes wrong:** `geography.py` loads the full 590k-city GeoNames database (14MB cities5000.txt) and 3.9MB cities.json on every import. With no persistent pre-computed index, every server restart pays a ~500ms-2s startup tax for a cache that is discarded on process exit.

**Chain of events:**
- Server restarts (deploy, crash, scale event).
- Geography module loaded. 590k cities parsed from text file into memory sets.
- For each city, country cross-references are built, lowercase lookups are computed.
- All of this is discarded when the process exits.
- Under load (multiple agency trips arriving simultaneously), multiple workers each pay the init cost.

**User experience:** First trip request after deploy takes 2-3 seconds while geography initializes. Operator wonders why it's slow. Subsequent requests are fine.

**Emotional impact:** Mild annoyance — "it's slow again."

**Likelihood x Impact:** High x Minor (degradation, not outage)
**Trust damage:** Low
**Recoverability:** Easy — add a persistent pre-computed index or a warm-up endpoint.
**Earliest signal:** First API call after any deploy is noticeably slow.
**Verify by:** Time `import src.intake.geography` vs a subsequent import.

---

## Finding 3: Solo Founder Cannot Absorb First-Week Support Load

**What goes wrong:** The pre-mortem itself found 32+ failure modes across 4 areas. The first week of beta with 5 agencies will surface a fraction of these, but each requires investigation, diagnosis, and fix. The founder handles code + deploy + support + sales simultaneously. There is no triage layer between the operator and the developer.

**Chain of events:**
- Agency A's operator sees an incorrect confidence score (Finding 1 from Decision Engine pre-mortem).
- Agency B has a trip where the toddler pacing flag didn't fire (Finding 3 from Decision Engine).
- Agency C's operator calls: "the audit page is slow" (Finding 1 from this doc).
- Agency D asks: "what does this amber flag mean?" (Provenance gaps from UX pre-mortem).
- Each issue: founder investigates for 30-90 minutes, fixes, deploys.
- Within two weeks, the founder has spent 15+ hours on reactive support.
- Pipeline work, customer discovery calls, and sales outreach all halt.

**User experience:** From the agency perspective: issues are fixed but slowly. Responses become delayed. Some questions don't get answered. Agencies interpret this as lack of commitment or product immaturity.

**Emotional impact:** Anxiety for the founder; cautious patience from agencies that erodes into doubt.

**Likelihood x Impact:** Near-certain x Major
**Trust damage:** Medium to High (degraded over time as response time increases)
**Recoverability:** Moderate — a crash-response triage (accept known low-severity bugs, fix only critical+high) buys the founder time.
**Earliest signal:** Any agency operator sends a support question followed by a reminder.
**Verify by:** The pre-mortem report itself — count the "High" and "Critical" risks. Each requires a founder-hour to address.

---

## Finding 4: LLM Costs Are Unmonitored and Unbounded

**What goes wrong:** The usage guard tracks costs via a SQLite store with reservation semantics, but there is no hard cap that stops the pipeline. Each trip costs ~₹150 with cheap models. At 5 agencies x 150 trips/month, that's ~₹1,12,500/month. If a pipeline loop (LLM failure → retry → recurse) fires, costs escalate silently.

**Chain of events:**
- Agent pipeline calls LLM for extraction, then decision, then strategy.
- An LLM returns invalid JSON (common for smaller models).
- Pipeline logs an error and retries from the agent recovery path.
- Retry calls LLM again. Each retry costs money. No circuit breaker.
- After 3 retries across 2 stages: 6x the expected cost for a single trip.
- At scale, cascading retries across 5 agencies spike monthly costs.
- The usage guard records these costs but does not enforce a hard ceiling.

**User experience:** Invisible. Founder only sees the bill at end of month.

**Emotional impact:** Shocked anger — "I spent how much on API calls?"

**Likelihood x Impact:** Medium x Major
**Trust damage:** Low (internal only)
**Recoverability:** Moderate — implement a hard budget ceiling on the usage guard, circuit breaker on retries.
**Earliest signal:** First billing statement or spot-check of the usage_store.sqlite database.
**Verify by:** Check the usage guard code for a hard cap/ceiling parameter. Does `check_before_call()` ever return `allowed=false` because of daily budget, or only because of rate limits?

---

## Finding 5: 4 Audit Corruptions Already — No Alerting on Corruption

**What goes wrong:** The audit directory already contains 4 corruption recovery files: `events.corrupt-20260428T102633Z.json`, `events.corrupt-20260502T111951Z.json`, `events.corrupt-20260502T183419Z.json`, `events.corrupt-20260503T083535Z.json`. These represent 4 distinct data loss events during DEVELOPMENT, with zero test coverage of monitoring or alerting. The audit trail has already lost data.

**Chain of events:**
- JSONL file gets truncated or has an incomplete write.
- Next read fails. Recovery logic dumps recoverable data to a `.corrupt-*` file.
- Unrecoverable lines are silently dropped.
- No email, no dashboard alert, no log warning that audit data was lost.
- Operators trust the audit trail, which is now incomplete.

**User experience:** Invisible — operator looks at audit log and sees a clean record. Doesn't know events were dropped.

**Emotional impact:** Betrayal — "we relied on this for compliance."

**Likelihood x Impact:** Very High (already happening) x Major
**Trust damage:** High
**Recoverability:** Easy for new data (add JSONL write atomicity, fsync, verify-before-trim). Impossible for already-lost data.
**Earliest signal:** Another `.corrupt-*` file appears.
**Verify by:** Check the frequency pattern in the timestamps: 4 corruptions in 5 days (Apr 28 to May 3). That's ~1 corruption/day in dev.

---

## Finding 6: No Rollback Path for File-Based Override Store

**What goes wrong:** The override system writes to per_trip JSONL files and an index.json with non-atomic operations. There is no undo, no checkpoint, no snapshot. An incorrect bulk operation or application bug can silently corrupt or clobber override state, and there is no way to revert.

**Chain of events:**
- A bug in a new feature touches all per_trip files.
- Or: an admin script iterates `data/overrides/per_trip/` and modifies entries.
- Wrong data is persisted. The index.json is updated to point to corrupted files.
- The override system now serves wrong decisions. Trips get wrong flags.
- No recovery path exists except "restore from git" for git-tracked files — but overrides are now gitignored.

**User experience:** Operator overrides a decision but the system ignores it. Override history shows something they didn't write.

**Emotional impact:** Helpless anger — "the system is overruling me and I can't fix it."

**Likelihood x Impact:** Medium x Catastrophic
**Trust damage:** Catastrophic (if operators stop trusting override system, the whole decision engine is useless)
**Recoverability:** Moderate (add file snapshots or periodic checkpoint backups) to impossible (no backup = data lost).
**Earliest signal:** Operator reports "I suppressed this flag but it's still showing."
**Verify by:** Check the override write path for transactional semantics — does it write temp file, fsync, rename, or just `open().write()`?

---

## The Failure Nobody Wants to Talk About

Waypoint OS doesn't fail from one bug. It fails because the solo founder is running a system with 814 run dirs, 4 data corruption events already detected, no hard cost ceiling on LLM calls, and no support triage layer — and the first 6 weeks of beta will surface enough of these issues simultaneously that the founder is forced to choose between fixing urgent bugs, supporting frustrated agencies, and continuing the sales pipeline that pays for it all. The product works. The business model is sound. But the operations surface area exceeds what one person can sustain across code + support + sales simultaneously, and the system gives no advance warning of which problem will break first.
