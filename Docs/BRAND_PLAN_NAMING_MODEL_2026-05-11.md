# Brand and Plan Naming Model (2026-05-11)

## Problem
Users were seeing naming drift between product, agency, and marketing terms (for example, "Waypoint OS" vs agency labels), which created trust friction and UI inconsistency.

## First-Principles Model
Treat identity as separate layers:

1. Product identity (global, stable): `Waypoint OS`
2. Agency identity (tenant-level): `profile.agency_name`
3. Optional commercial descriptors:
   - `profile.sub_brand` (line of business)
   - `profile.plan_label` (commercial/service tier label)

This prevents implicit renames and keeps branding deterministic across surfaces.

## Implementation Notes
- Settings Profile tab includes explicit guidance so operators understand where each field is used.
- Tooltips and copy explain internal vs customer-facing intent.
- Optional fields are additive and non-breaking.

## Current UX Contract
- Product name remains fixed in shell/product surfaces.
- Agency name remains the canonical workspace identity.
- Sub-brand and plan label are optional descriptors, never substitutes for product name.

## Why this is long-term safe
- Clear semantic ownership per field avoids future coupling bugs.
- Multi-tenant friendly: each agency can express identity without affecting product brand.
- Future-ready for packaging and subscription display logic.
