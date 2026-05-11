# Frontend Runtime Truth Matrix

Date: 2026-05-11  
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
| Documents module (`/documents`) | Disabled in nav | Research complete | `src/lib/nav-modules.ts` line with `href: '/documents', enabled: false` | Mark as planned runtime module |
| Document ingestion/extraction operations | Implemented in workbench ops path | Research partially aligned | `api-client.ts` has `uploadDocument`, `getDocuments`, `extractDocument`, `applyExtraction`; `OpsPanel.tsx` calls these | Treat as canonical current path; extend this path, do not create parallel flow |

## Architecture Guardrail

Do not create a parallel "document generation v2" route tree while current operational document path lives under workbench.  
Extend canonical surfaces first:

1. Keep operational ingestion/extraction in current Ops path.
2. Add template generation as an additive capability behind explicit flags/contracts.
3. Enable nav modules only when routes and end-user behavior are production-valid.

Related decision note:
- [CANONICAL_DOCUMENT_OPS_PATH_2026-05-11.md](./CANONICAL_DOCUMENT_OPS_PATH_2026-05-11.md)

## Planning Rule

When a doc says "Complete", interpret it as one of:

- `Research Complete`
- `Implementation Complete`
- `Research + Implementation Complete`

If label type is missing, assume ambiguity and resolve via runtime evidence before planning.
