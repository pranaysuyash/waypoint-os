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

## Existing tool: `validate-contrast.ts`

Color/accessibility helper script for contrast checks.
