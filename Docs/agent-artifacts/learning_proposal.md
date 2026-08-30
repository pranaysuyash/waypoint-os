# Learning Proposal: E2E Visual Verification & Commit Gate Discipline

Based on the recent workflow interactions, corrections, and successful resolutions, this proposal outlines persistent operational guidelines to add to the repository's instruction stack (`/Users/pranay/Projects/travel_agency_agent/AGENTS.md`).

---

## 1. Identified Pivotal Behaviors & Lessons

### A. Strict E2E Visual Proofing & Inspection
* **Context**: Earlier visual checks generated unauthenticated/blank fallback screens ("Checking your session..." or dark loading screens) that were embedded into walkthroughs without prior visual inspection.
* **Rule**:
  1. Always start backend (`spine_api`) and frontend (`frontend`) dev servers before capturing UI proofs.
  2. Pre-hydrate session/auth state in the test browser context to prevent session-block redirects.
  3. **Mandatory Visual Inspection**: Always use `view_file` on captured `.png`/`.jpg` artifacts to verify 100% full, authenticated visual rendering before attaching them to `walkthrough.md` or presenting them to the user.

### B. Dev Server Port & Logging Hygiene
* **Context**: Next.js on port `3000` collided with Grafana (`EADDRINUSE`), and missing background endpoints (`/metrics`) caused log noise.
* **Rule**:
  1. Use dedicated non-colliding dev ports for Next.js (`:3005`).
  2. Implement clean `@app.get("/metrics")` and `@app.get("/health")` endpoints on FastAPI servers to prevent background monitoring 404 log clutter.

### C. Motto Commit Gate & Pre-Commit Lint Discipline
* **Context**: Pre-commit hooks enforce `ruff` linting and section-level Motto_v4 attestation gates (`PROJECTS_AGENT_SECTION_*`).
* **Rule**:
  1. Always run `uv run ruff check --fix` and resolve remaining linting errors before triggering `git commit`.
  2. Complete section-by-section attestations with genuine evidence strings, placing `SECTION_00_INTEGRATED` last, and meeting the 60-second review window without attempting to bypass or skip gates.

---

## 2. Proposed Changes to `AGENTS.md`

```diff
--- a/AGENTS.md
+++ b/AGENTS.md
@@ -100,6 +100,24 @@
+## Strict Visual E2E Verification Standard
+
+- **Always Start Servers**: Before capturing UI screenshots, start both backend (`spine_api` on `:8000`) and frontend (`frontend` on `:3005`).
+- **Pre-Hydrate Auth**: Ensure client session state is pre-hydrated (`isAuthenticated: true`) so protected routes (`/workbench`) render full UI content instead of loading/session notices.
+- **Inspect Before presenting**: Never attach or claim screenshots are "proof" without viewing them first via `view_file` to confirm clean, non-blank, fully rendered UI content.
+
+## Commit Gate & Code Quality Standard
+
+- **Linter Zero-Warning Policy**: Run `uv run ruff check --fix .` before staging changes to ensure zero lint errors hit the pre-commit gate.
+- **Motto Attestation Protocol**: Execute section attestations (`attest_motto_commit.py`) with real evidence strings, ensuring `SECTION_00_INTEGRATED` is recorded last, and respect the required review duration.
```

---

## 3. Action Requested

Please review this proposal. Once approved, I will apply these updates to [`AGENTS.md`](file:///Users/pranay/Projects/travel_agency_agent/AGENTS.md).
