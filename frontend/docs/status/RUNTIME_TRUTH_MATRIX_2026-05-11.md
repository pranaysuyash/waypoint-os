# Frontend Runtime Truth Matrix

Date: 2026-05-12
Scope: `frontend` runtime modules vs research/spec documentation claims

## Purpose

This document is the canonical reconciliation layer between:

1. What is implemented and reachable in runtime navigation/workflows.
2. What is documented as research/spec completeness.

Use this matrix before planning new implementation work to avoid building from stale "complete" labels in research docs.

## Runtime Evidence Snapshot

- Navigation module flags come from [`src/lib/nav-modules.ts`](../../src/lib/nav-modules.ts).
- Document operations runtime exists in:
  - [`src/lib/api-client.ts`](../../src/lib/api-client.ts)
  - [`src/app/(agency)/workbench/OpsPanel.tsx`](../../src/app/(agency)/workbench/OpsPanel.tsx)
  - [`src/lib/route-map.ts`](../../src/lib/route-map.ts)

## Implemented vs Research Matrix

| Area | Runtime Status | Research/Spec Status | Evidence | Decision |
|---|---|---|---|---|
| Timeline feature | Implemented and reachable | Research complete | `nav-modules.ts` shows planning/inbox/overview active; timeline docs in `TIMELINE_*` | Keep marked complete for research and implementation |
| Output Panel (bundle display/debug) | Partially implemented in workbench surfaces | Research complete | `OutputPanel.tsx` exists; deep dive docs `OUTPUT_*` are extensive | Label as `partially implemented; research complete` |
| Template engine (compile/render pipeline) | Not implemented in runtime | Research/spec complete only | `DOCUMENT_GEN_01_TEMPLATES.md` lists open next steps; `OUTPUT_12_TEMPLATE_REFERENCE_COMPLETE.md` defines architecture but no runtime engine path in `src/lib` | Keep as planned architecture; do not present as shipped |
| Quotes module (`/quotes`) | Disabled in nav | Research complete | `src/lib/nav-modules.ts` line with `href: '/quotes', enabled: false` | Mark as planned runtime module |
| Documents module (`/documents`) | Enabled in nav with rollout gates complete | Research complete | `src/lib/nav-modules.ts` + `isDocumentsModuleEnabled()` + `/app/(agency)/documents/page.tsx` | Treat as active route-level module over canonical contracts |
| Document ingestion/extraction operations | Implemented in workbench ops path | Research partially aligned | `api-client.ts` has `uploadDocument`, `getDocuments`, `extractDocument`, `applyExtraction`; `OpsPanel.tsx` calls these | Treat as canonical current path; extend this path, do not create parallel flow |

## Architecture Guardrail

Do not create a parallel "document generation v2" route tree while current operational document path lives under workbench.  
Extend canonical surfaces first:

1. Keep operational ingestion/extraction in current Ops path.
2. Add template generation as an additive capability behind explicit flags/contracts.
3. Enable nav modules only when routes and end-user behavior are production-valid.

Related decision note:
- [CANONICAL_DOCUMENT_OPS_PATH_2026-05-11.md](./CANONICAL_DOCUMENT_OPS_PATH_2026-05-11.md)
- [DOCUMENTS_MODULE_ENABLEMENT_CONTRACT_2026-05-11.md](./DOCUMENTS_MODULE_ENABLEMENT_CONTRACT_2026-05-11.md)

## Planning Rule

When a doc says "Complete", interpret it as one of:

- `Research Complete`
- `Implementation Complete`
- `Research + Implementation Complete`

If label type is missing, assume ambiguity and resolve via runtime evidence before planning.

## Browser Runtime Drift Finding

2026-05-11 live Chrome testing found a runtime-cache drift mode that plain HTTP checks did not catch:

- `curl` returned valid HTML for `/login` and `/workbench?draft=new&tab=safety`.
- Chrome initially showed a blank gray shell.
- `.next/dev` still contained stale compiled references to the removed `IntegrityMonitorPanel` component even though source had moved to `components/system/SystemCheckPanel`.
- Clearing the Next.js dev cache with `npm run dev:reset`, then restarting the frontend, restored the visible browser flow.

Runtime truth rule:

- For frontend acceptance, combine HTTP contract checks with a real rendered-browser check.
- If source and browser disagree after a component supersession/removal, inspect `.next/dev` and `frontend/.next/dev/logs/next-development.log` before changing source.
- Do not preserve stale components solely to satisfy dev-cache artifacts; reset the runtime cache and verify again.

## Auth Redirect Copy Finding

2026-05-11 live login testing also exposed a user-facing copy issue:

- The login page previously rendered a raw redirect target such as `workbench?draft=new&tab=safety` as visible copy.
- The correct runtime behavior is to preserve the exact redirect internally while showing an operator-facing destination label.

Current contract:

- `resolveSafeRedirect()` keeps the trusted redirect path and query string.
- `formatAuthRedirectLabel()` converts that same safe target into human copy, for example `/workbench?draft=new&tab=safety` -> `New Inquiry - Risk Review`.
- Full-page login and modal login both use the same formatter so labels do not drift.

Verification:

- `npm run -s test -- --run 'src/lib/__tests__/auth-redirect.test.ts' 'src/components/auth/__tests__/AuthProvider.test.tsx'`
- Visible HTML text check for `/login?redirect=%2Fworkbench%3Fdraft%3Dnew%26tab%3Dsafety` includes `New Inquiry - Risk Review` and does not expose the raw workbench query string.
