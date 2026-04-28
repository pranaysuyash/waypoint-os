# Implementation Task List — Industry Process Gap Audit

**Date:** 2026-04-28
**Source:** `Docs/INDUSTRY_PROCESS_GAP_ANALYSIS_2026-04-16.md`

## Summary

This task list captures the partial implementation work already present in the repo and the highest-priority gaps identified from the industry process audit.

## Repo evidence found

1. **Visa timeline risk assessment**
   - `src/decision/rules/visa_timeline.py`
   - `src/decision/hybrid_engine.py`
   - `src/intake/extractors.py`

2. **Visa / insurance heuristics**
   - `src/intake/decision.py` (`visa_insurance` budget bucket)
   - `src/intake/decision.py` (`visa_status` document-blocker logic)

3. **Payment state placeholders**
   - `src/intake/packet_models.py` (`LifecycleInfo.payment_stage`)
   - `src/intake/packet_models.py` (`SubGroup.payment_status`)

4. **Feedback / review / recovery workflow**
   - `src/analytics/review.py`
   - `src/analytics/engine.py`

5. **Supplier negotiation stub**
   - `src/intake/negotiation_engine.py`

6. **Cancellation/refund placeholder**
   - `src/intake/decision.py` (`pending_policy_lookup`)

## High-priority implementation work

### 1. Financial state tracking

- Implement `QuoteRecord`, `CollectionRecord`, `SupplierCostRecord`, and payment milestone models.
- Persist quote amounts, collected amounts, outstanding balance, and supplier-confirmed net cost.
- Compute overdue status from due dates and wire to notification/escalation logic.
- Support multi-party payment splits for group travel sub-groups.
- Add owner review or escalation triggers for overdue balances and low-margin bookings.

### 2. Visa / document workflow

- Add a destination/nationality visa requirement database and per-country requirement model.
- Create document checklist generation for passport, visas, insurance, photos, bank statements, and consulate-specific requirements.
- Track per-traveler document status and file upload metadata.
- Implement application status lifecycle: not started, submitted, under review, approved, rejected.
- Add timed reminders for document collection and pre-departure delivery (D-60, D-45, D-30, D-3, D-1).

### 3. Cancellation / refund policy engine

- Model supplier cancellation terms by component (hotel, flight, transfer, activity).
- Compute refund eligibility and amount using notice period, reason category, and insurance applicability.
- Support credit note tracking separate from cash refunds.
- Add rebooking alternative generation and fare difference calculation logic.
- Replace `pending_policy_lookup` with an actionable cancellation policy evaluation path.

### 4. Active trip and operations workflows

- Add booking reference/PNR/voucher tracking for suppliers and confirmations.
- Implement flight status monitoring and disruption detection for active trips.
- Support DMC/transfer coordination, request statuses, and emergency contact records.
- Add pre-departure briefing/dossier generation and D-1 reminder automation.
- Expand emergency response fields for passport loss, overbooking, and carrier bankruptcy.

### 5. Insurance recommendations

- Model mandatory insurance requirements for visa-sensitive destinations (e.g. Schengen €30K minimum).
- Implement insurance recommendation rules based on destination, traveler age, and medical risk.
- Store insurance policy delivery metadata and emergency contact numbers.

### 6. Supplier and contract modeling

- Add supplier contract fields: contracted net rate, rack rate, meal plan, room category, allotment, blackout dates.
- Standardize room category taxonomy and meal plan mapping.
- Track supplier confirmations, voucher issuance, and supplier-specific deadlines.

## Suggested next validation

- Add a small integration test covering visa timeline risk plus `visa_status` extraction.
- Add a unit test for `LifecycleInfo.payment_stage` and `SubGroup.payment_status` behavior.
- Add a regression test for the cancellation policy placeholder state in `src/intake/decision.py`.
