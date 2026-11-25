# Frontend Tools

Reusable utilities for local development diagnostics and consistency checks.

## `dev-doctor.mjs`

Checks for frontend source/runtime drift (for example, old nav labels in one browser window and new labels in another).

What it verifies:
- `Shell.tsx` contains expected nav/version markers
- Which process(es) are listening on port `3000`
- Whether `http://localhost:3000` response matches expected nav/version markers
- Whether `http://localhost:3000/api/version` is reachable and matches `package.json` version

Run:
- `npm run dev:doctor`

## `dev-reset.mjs`

Performs a clean frontend runtime reset:
- Stops process(es) listening on `:3000`
- Removes `.next` cache directory

Run:
- `npm run dev:reset`
- `npm run dev` (after reset)

### Authenticated responsive route scan

Run `node frontend/tools/audit-responsive-routes.cjs` from the project root
with the isolated demo running on port 3017 and Chrome installed. Pass route
paths to limit the scan. It emits JSON Lines with viewport widths, top-level
overflows and out-of-bounds controls. Set `RESPONSIVE_AUDIT_CAPTURE` to an
evidence directory for flagged viewport captures, and
`RESPONSIVE_AUDIT_CAPTURE_WIDTHS` to comma-separated widths to capture even
when the scan reports no issue. The scan is triage. Manually verify flagged
geometry and exercise representative loaded states and interactions.

Set `RESPONSIVE_AUDIT_PUBLIC=1` to scan static public routes without creating a
demo session. Set `RESPONSIVE_AUDIT_BASE` when using a different local preview.
A non-success HTTP response is reported as an unavailable route and has no
viewport observations.
