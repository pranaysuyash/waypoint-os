# Assisted Enquiry Assignment and Routing Research

Date: 2026-05-19

## Product Principle

Long-unassigned enquiries are not just missing a field. They are operational leakage.

Waypoint should surface the age of unassigned work immediately, then eventually recommend or perform assignment using agency-specific evidence.

Trust rule:

> Waypoint recommends or prepares ownership; the agency can override it.

## Current UI Correction

The Overview Action Required card should not say only `Assign owner` when the item has waited for a long time.

Better current-slice language:

- `Qualification overdue · Breached SLA · unassigned oldest 25d waiting`
- `Pending: Qualify · Assign owner (25d waiting) · Identify customer · Confirm basics`

This makes the operational issue visible without needing a new endpoint.

## Long-Term Routing Model

The right long-term system is not a single round-robin. Assignment should score candidates from several signals:

- availability: who is currently online, on shift, or inside working hours
- active load: how many open enquiries/trips each operator owns
- overdue load: how much stale work each operator is already carrying
- response speed: recent median time to first action and qualification
- completion quality: reopen rate, missing-detail rate, quote approval quality, customer follow-through
- specialization: destination, trip type, source channel, language, VIP/high-value handling
- fairness: avoid always giving work to the fastest person
- continuity: returning customer, existing relationship, or prior trip ownership
- escalation policy: high-value, complex, or breached-SLA work may route to senior operators

## Suggested Phases

### Phase 1 - Visibility

- Highlight long-unassigned work in Overview and Inbox.
- Sort unassigned breached-SLA enquiries above generic overdue enquiries.
- Show reason: `unassigned oldest 25d waiting`.
- Keep action manual: operator opens the queue and assigns.

### Phase 2 - Suggested Owner

- Backend computes `recommended_owner_id` and `recommendation_reason`.
- UI shows `Suggested owner: Priya · lowest active load` or `Suggested owner: Arjun · fastest qualifier for leisure enquiries`.
- Operator confirms or changes owner.
- Store recommendation, operator decision, and override reason for learning.

### Phase 3 - Assisted Bulk Assignment

- Allow owner/manager to assign a selected queue using recommendations.
- Show distribution before applying: owner counts, stale work impact, SLA risk.
- Require confirmation for bulk assignment.
- Preserve audit trail.

### Phase 4 - Policy-Based Auto Assignment

- Agency enables a routing policy.
- New enquiries are assigned automatically only when confidence and policy checks pass.
- Breached or ambiguous cases remain manual or escalate.
- Operators can override, and overrides become feedback.

## Backend Design Questions

1. What is the canonical ownership table for enquiries versus trips?
2. Is operator availability represented anywhere today, or does it need a new schedule/presence model?
3. Which timestamps define first action, qualification, reassignment, and completion?
4. Can we compute active load from existing trip/enquiry status, or do we need an operator workload summary table?
5. Should routing be synchronous at intake or queue-based after enquiry creation?
6. How do we handle no eligible owner?
7. How do we prevent one strong operator from receiving every difficult enquiry?
8. What audit events are required for recommendation, auto-assignment, override, and reassignment?
9. What agency-level settings are required before auto-assignment is allowed?
10. How do we test routing deterministically without relying on production history?

## Data Model Sketch

Possible future records:

- `assignment_recommendations`
  - `id`
  - `agency_id`
  - `entity_type`
  - `entity_id`
  - `recommended_owner_id`
  - `score`
  - `reason_codes`
  - `model_version`
  - `created_at`
  - `accepted_at`
  - `overridden_by`
  - `override_reason`

- `operator_workload_snapshots`
  - `agency_id`
  - `operator_id`
  - `active_enquiries`
  - `active_trips`
  - `overdue_items`
  - `median_first_action_minutes`
  - `median_qualification_minutes`
  - `captured_at`

- `assignment_policies`
  - `agency_id`
  - `mode`: `manual`, `suggested`, `bulk_assisted`, `auto`
  - `fairness_weight`
  - `speed_weight`
  - `load_weight`
  - `specialization_weight`
  - `max_active_enquiries_per_owner`
  - `require_manager_for_breached_sla`

## What Not To Build Yet

- Do not auto-assign silently.
- Do not route based only on equal counts.
- Do not optimize purely for speed if it creates unfair load or lower quality.
- Do not hide manual override.
- Do not make assignment recommendations without audit events.
- Do not call this an AI feature in user-facing language.

## First Slice Candidate

Build a backend grouped-work summary for Overview:

- total overdue enquiries
- count unassigned
- oldest unassigned age
- count missing customer identity
- count missing trip basics
- count with suggested owner available once routing exists

Then update Overview to use that summary instead of deriving pending categories only from visible examples.
